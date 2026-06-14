"""
Streamlit UI — Multi-Agent Research Assistant.

Run from repo root: ``streamlit run streamlit_app.py``
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import requests
import streamlit as st
from dotenv import load_dotenv

from app.structured_output import structured_from_state

load_dotenv()

USE_API = os.environ.get("STREAMLIT_USE_API", "").lower() in ("1", "true", "yes")
API_BASE = os.environ.get("RESEARCH_API_URL", "http://127.0.0.1:8000").rstrip("/")

PIPELINE = [
    ("search", "Search", "Retrieve sources from the web"),
    ("summarizer", "Summarize", "Extract facts from each source"),
    ("critic", "Critique", "Check claims and score confidence"),
    ("report", "Report", "Write the final markdown output"),
]

EXAMPLES = {
    "Choose an example…": "",
    "AI agents & LangGraph (2026)": "Latest trends in AI agents and LangGraph 2026",
    "Solid-state batteries": "Solid-state battery breakthroughs and commercial readiness",
    "LangGraph vs CrewAI": "Compare multi-agent frameworks: LangGraph vs CrewAI",
    "RAG vs agentic search": "Impact of RAG vs agentic search on enterprise AI",
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 920px;
            }
            header[data-testid="stHeader"] { background: transparent; }
            .step-row {
                display: flex;
                align-items: stretch;
                gap: 0;
                margin: 1rem 0 0.5rem 0;
            }
            .step {
                flex: 1;
                padding: 0.75rem 0.5rem;
                border-top: 2px solid #e5e7eb;
                font-size: 0.8125rem;
                line-height: 1.35;
            }
            .step .num {
                display: block;
                font-size: 0.6875rem;
                font-weight: 600;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: #9ca3af;
                margin-bottom: 0.2rem;
            }
            .step .label { font-weight: 600; color: #374151; }
            .step .hint { color: #6b7280; font-size: 0.75rem; margin-top: 0.15rem; }
            .step.done { border-top-color: #059669; }
            .step.done .num { color: #059669; }
            .step.active { border-top-color: #2563eb; background: #f8fafc; }
            .step.active .num { color: #2563eb; }
            .step.pending { opacity: 0.45; }
            div[data-testid="stSidebar"] .stMarkdown p { font-size: 0.875rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_stepper(active: str | None, completed: set[str]) -> None:
    parts: list[str] = ['<div class="step-row">']
    for i, (key, label, hint) in enumerate(PIPELINE, 1):
        if key in completed:
            state = "done"
        elif key == active:
            state = "active"
        else:
            state = "pending"
        parts.append(
            f'<div class="step {state}">'
            f'<span class="num">Step {i}</span>'
            f'<span class="label">{label}</span>'
            f'<div class="hint">{hint}</div>'
            f"</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def run_local_pipeline(query: str, progress_slot) -> dict:
    from app.graph import run_research

    order = [step[0] for step in PIPELINE]

    def show_progress(active: str | None, completed: set[str]) -> None:
        with progress_slot.container():
            st.markdown("**Progress**")
            render_stepper(active=active, completed=completed)

    def hook(agent: str) -> None:
        if agent not in order:
            return
        idx = order.index(agent)
        show_progress(active=agent, completed=set(order[:idx]))

    out = run_research(query, progress_hook=hook)
    show_progress(active=None, completed=set(order))
    return out


def run_remote_api(query: str) -> dict:
    r = requests.post(
        f"{API_BASE}/research",
        json={"query": query},
        timeout=600,
    )
    r.raise_for_status()
    data = r.json()
    return {
        "query": query,
        "final_report": data.get("report", ""),
        "errors": data.get("errors", []),
        "current_agent": data.get("current_agent", ""),
        "summaries": [
            {
                "url": s.get("url", ""),
                "title": s.get("title", ""),
                "summary": s.get("summary", ""),
                "key_facts": [],
            }
            for s in data.get("sources", [])
        ],
        "critic_output": {
            "contradictions": data.get("contradictions", []),
            "assessments": data.get("assessments", []),
        },
        "_structured": data,
    }


def render_sources(sources: list[dict]) -> None:
    if not sources:
        st.caption("No sources were returned for this query.")
        return
    for i, src in enumerate(sources, 1):
        title = (src.get("title") or src.get("url") or "Untitled").strip()
        url = src.get("url", "")
        with st.expander(f"{i}. {title[:90]}", expanded=False):
            if url:
                st.link_button("Open source", url, use_container_width=False)
            if src.get("summary"):
                st.write(src["summary"])


def render_validation(contradictions: list[str], assessments: list[dict]) -> None:
    if contradictions:
        st.markdown("**Contradictions**")
        for item in contradictions:
            st.markdown(f"- {item}")
    else:
        st.caption("No contradictions were flagged across sources.")

    if assessments:
        st.markdown("**Claim assessments**")
        rows = [
            {
                "Claim": a.get("claim", ""),
                "Confidence": str(a.get("confidence", "")).capitalize(),
                "Notes": a.get("notes", ""),
            }
            for a in assessments
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No per-claim assessments for this run.")


def render_results(query: str, out: dict) -> None:
    structured = out.get("_structured") or structured_from_state(out)
    confidence = structured.get("confidence", "MEDIUM")
    source_count = structured.get("source_count", len(structured.get("sources", [])))
    contradictions = structured.get("contradictions", [])
    report = structured.get("report") or out.get("final_report") or ""

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sources", source_count)
    c2.metric("Findings", len(structured.get("key_findings", [])))
    c3.metric("Contradictions", len(contradictions))
    c4.metric("Confidence", confidence.title())

    tab_report, tab_sources, tab_validation, tab_json = st.tabs(
        ["Report", "Sources", "Validation", "JSON"]
    )

    with tab_report:
        if report.strip():
            with st.container(border=True):
                st.markdown(report)
            st.download_button(
                "Download .md",
                data=report,
                file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
            )
        else:
            st.caption("No report was generated.")

    with tab_sources:
        render_sources(structured.get("sources", []))

    with tab_validation:
        render_validation(contradictions, structured.get("assessments", []))

    with tab_json:
        st.json(
            {
                "query": query,
                "confidence": confidence,
                "source_count": source_count,
                "overview": structured.get("overview", ""),
                "key_findings": structured.get("key_findings", []),
                "contradictions": contradictions,
                "assessments": structured.get("assessments", []),
                "sources": structured.get("sources", []),
                "errors": out.get("errors", []),
            }
        )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("**Pipeline**")
        for i, (_, label, hint) in enumerate(PIPELINE, 1):
            st.caption(f"{i}. {label} — {hint}")

        st.divider()

        st.markdown("**Session**")
        if USE_API:
            st.caption(f"API · `{API_BASE}`")
        elif os.environ.get("GROQ_API_KEY"):
            st.caption("Local · Groq configured")
        else:
            st.warning("Add `GROQ_API_KEY` to `.env`", icon="⚠️")

        history = st.session_state.get("history") or []
        if history:
            st.divider()
            st.markdown("**Recent**")
            for item in history[:4]:
                label = item[:64] + ("…" if len(item) > 64 else "")
                if st.button(label, key=f"hist_{hash(item)}"):
                    st.session_state.query_input = item


def _apply_example() -> None:
    picked = st.session_state.get("example_pick", "Choose an example…")
    if picked != "Choose an example…":
        st.session_state.query_input = EXAMPLES[picked]


def main() -> None:
    st.set_page_config(
        page_title="Research Assistant",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles()
    render_sidebar()

    st.title("Research Assistant")
    st.caption("Four-agent LangGraph workflow · Groq · DuckDuckGo")

    if "query_input" not in st.session_state:
        st.session_state.query_input = ""

    query_col, action_col = st.columns([6, 1], vertical_alignment="bottom")
    with query_col:
        st.text_input(
            "Query",
            placeholder="What would you like to research?",
            label_visibility="collapsed",
            key="query_input",
        )
    with action_col:
        run = st.button("Run", type="primary", use_container_width=True)

    with st.expander("Example queries", expanded=False):
        st.selectbox(
            "Pick one to fill the input",
            options=list(EXAMPLES.keys()),
            label_visibility="collapsed",
            key="example_pick",
            on_change=_apply_example,
        )

    if not run:
        return

    query = st.session_state.query_input.strip()
    if not query:
        st.warning("Enter a research question first.")
        return
    if not USE_API and not os.environ.get("GROQ_API_KEY"):
        st.error("Set `GROQ_API_KEY` in your `.env` file.")
        return

    progress_slot = st.empty()
    with progress_slot.container():
        st.markdown("**Progress**")
        render_stepper(active="search", completed=set())

    try:
        if USE_API:
            with st.spinner("Running pipeline…"):
                out = run_remote_api(query)
            with progress_slot.container():
                st.markdown("**Progress**")
                render_stepper(active=None, completed={s[0] for s in PIPELINE})
        else:
            out = run_local_pipeline(query, progress_slot)
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
        return
    except Exception as exc:
        st.error(f"Pipeline failed: {exc}")
        return

    history = st.session_state.get("history", [])
    if query not in history:
        st.session_state.history = [query] + history[:7]

    errs = out.get("errors") or []
    if errs:
        with st.expander(f"{len(errs)} pipeline notice(s)"):
            for err in errs:
                st.caption(err)

    st.divider()
    render_results(query, out)


if __name__ == "__main__":
    main()
