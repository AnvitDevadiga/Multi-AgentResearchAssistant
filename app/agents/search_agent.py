"""Agent 1: DuckDuckGo search — top URLs and content snippets."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.state import ResearchState, SearchHit

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_FETCH_BYTES = 400_000
TEXT_PREVIEW_CHARS = 8_000


def _strip_html(html: str) -> str:
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_page_text(url: str, timeout: float = 10.0) -> str:
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            trust_env=False,
        ) as client:
            r = client.get(url)
            r.raise_for_status()
            body = r.content[:MAX_FETCH_BYTES]
            raw = body.decode("utf-8", errors="replace")
            return _strip_html(raw)[:TEXT_PREVIEW_CHARS]
    except Exception:
        return ""


def _ddg_lite_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """DuckDuckGo Lite HTML results (no API key)."""
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://lite.duckduckgo.com/",
    }
    payload: dict[str, str] = {"q": query, "b": ""}
    out: list[dict[str, str]] = []
    with httpx.Client(
        follow_redirects=True,
        timeout=25.0,
        headers=headers,
        trust_env=False,
    ) as client:
        for _ in range(2):
            r = client.post("https://lite.duckduckgo.com/lite/", data=payload)
            r.raise_for_status()
            if b"No more results." in r.content:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            tables = soup.find_all("table")
            if not tables:
                break
            rows = tables[-1].find_all("tr")
            i = 0
            while i < len(rows):
                tr = rows[i]
                a = tr.find("a", href=True)
                href = (a.get("href") or "").strip() if a else ""
                if (
                    href.startswith("http")
                    and "google.com/search" not in href
                    and "duckduckgo.com/y.js" not in href
                ):
                    title = a.get_text(strip=True) if a else ""
                    snippet = ""
                    if i + 1 < len(rows):
                        ntr = rows[i + 1]
                        sn = ntr.find("td", class_=lambda c: c and "result-snippet" in c)
                        if sn:
                            snippet = sn.get_text(" ", strip=True)
                            i += 2
                        else:
                            i += 1
                    else:
                        i += 1
                    out.append({"href": href, "title": title, "body": snippet})
                    if len(out) >= max_results:
                        return out
                    continue
                form = tr.find("form")
                if form and out:
                    hidden = {
                        str(inp.get("name")): str(inp.get("value") or "")
                        for inp in form.find_all("input", type="hidden")
                        if inp.get("name")
                    }
                    if hidden:
                        payload = {"q": query, "b": "", **hidden}
                i += 1
            break
    return out[:max_results]


def _ddg_package_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Fallback: ``duckduckgo_search`` (backend depends on library version)."""
    from duckduckgo_search import DDGS

    out: list[dict[str, str]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            href = (r.get("href") or r.get("url") or "").strip()
            if not href.startswith("http"):
                continue
            out.append(
                {
                    "href": href,
                    "title": (r.get("title") or "").strip(),
                    "body": (r.get("body") or "").strip(),
                }
            )
            if len(out) >= max_results:
                break
    return out


def _run_search(query: str, max_results: int = 5) -> list[SearchHit]:
    raw: list[dict[str, str]] = []
    try:
        raw = _ddg_lite_search(query, max_results=max_results)
    except Exception:
        raw = []
    if not raw:
        try:
            raw = _ddg_package_search(query, max_results=max_results)
        except Exception:
            raw = []

    # Filter valid URLs first
    valid = []
    for r in raw:
        href = (r.get("href") or "").strip()
        title = (r.get("title") or "").strip()
        body = (r.get("body") or "").strip()
        if not href or not urlparse(href).scheme.startswith("http"):
            continue
        valid.append({"href": href, "title": title, "body": body})
        if len(valid) >= max_results:
            break

    if not valid:
        return []

    # Fetch all page contents concurrently
    fetched_contents: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(len(valid), 5)) as pool:
        future_to_url = {pool.submit(_fetch_page_text, v["href"]): v["href"] for v in valid}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                fetched_contents[url] = future.result()
            except Exception:
                fetched_contents[url] = ""

    hits: list[SearchHit] = []
    for v in valid:
        href = v["href"]
        fetched = fetched_contents.get(href, "")
        raw_content = fetched if fetched else v["body"]
        hit: SearchHit = {
            "url": href,
            "title": v["title"] or href,
            "snippet": v["body"],
            "raw_content": raw_content if raw_content else v["body"],
        }
        hits.append(hit)
    return hits


def _notify(state: ResearchState, message: str) -> None:
    hook = state.get("_progress_hook")
    if callable(hook):
        try:
            hook(message)
        except Exception:
            pass


def search_node(state: ResearchState) -> dict:
    """Retrieve top search hits and optional fetched text."""
    _notify(state, "search")
    query = (state.get("query") or "").strip()
    if not query:
        return {
            "search_results": [],
            "current_agent": "search",
            "errors": ["Search: empty query."],
        }
    try:
        hits = _run_search(query, max_results=5)
        if not hits:
            return {
                "search_results": [],
                "current_agent": "search",
                "errors": ["Search: no results returned (try a different query)."],
            }
        return {"search_results": hits, "current_agent": "search"}
    except Exception as e:
        return {
            "search_results": [],
            "current_agent": "search",
            "errors": [f"Search agent failed: {e!s}"],
        }
