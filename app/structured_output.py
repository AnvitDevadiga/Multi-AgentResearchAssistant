"""Build structured API/UI payloads from LangGraph pipeline state."""

from __future__ import annotations

import re
from typing import Any


def _extract_overview(report: str) -> str:
    if not report.strip():
        return ""
    match = re.search(
        r"(?is)##\s*overview\s*\n+(.*?)(?=\n##\s|\Z)",
        report,
    )
    if match:
        return match.group(1).strip()
    paragraphs = [p.strip() for p in report.split("\n\n") if p.strip()]
    return paragraphs[0][:600] if paragraphs else report[:600]


def _overall_confidence(assessments: list[dict[str, Any]], contradictions: list[str]) -> str:
    if not assessments:
        return "LOW" if contradictions else "MEDIUM"
    scores = {"high": 3, "medium": 2, "low": 1}
    values = [scores.get(str(a.get("confidence", "medium")).lower(), 2) for a in assessments]
    avg = sum(values) / len(values)
    if contradictions and avg < 2.5:
        return "LOW"
    if contradictions:
        return "MEDIUM"
    if avg >= 2.6:
        return "HIGH"
    if avg >= 1.8:
        return "MEDIUM"
    return "LOW"


def structured_from_state(state: dict[str, Any]) -> dict[str, Any]:
    """Normalize graph state into recruiter-friendly structured JSON."""
    summaries = state.get("summaries") or []
    critic = state.get("critic_output") or {}
    contradictions = list(critic.get("contradictions") or [])
    assessments = list(critic.get("assessments") or [])
    report = str(state.get("final_report") or "")

    key_findings: list[str] = []
    for summary in summaries:
        for fact in summary.get("key_facts") or []:
            text = str(fact).strip()
            if text and text not in key_findings:
                key_findings.append(text)
        if len(key_findings) >= 12:
            break

    sources = [
        {
            "url": s.get("url", ""),
            "title": s.get("title", ""),
            "summary": s.get("summary", ""),
        }
        for s in summaries
        if s.get("url")
    ]

    search_results = state.get("search_results") or []
    if not sources and search_results:
        sources = [
            {
                "url": hit.get("url", ""),
                "title": hit.get("title", ""),
                "summary": hit.get("snippet", ""),
            }
            for hit in search_results
            if hit.get("url")
        ]

    confidence = _overall_confidence(assessments, contradictions)

    return {
        "overview": _extract_overview(report),
        "key_findings": key_findings[:12],
        "contradictions": contradictions,
        "assessments": assessments,
        "sources": sources,
        "confidence": confidence,
        "source_count": len(sources),
        "report": report,
    }
