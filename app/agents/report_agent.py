"""Agent 4: Final markdown report."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_chat_model
from app.state import ResearchState


def _minimal_report(state: ResearchState) -> str:
    q = state.get("query", "")
    lines = [
        "## Overview",
        f"Research query: **{q}**",
        "",
        "## Key Findings",
        "- _No summarized sources available._",
    ]
    return "\n".join(lines)


def report_node(state: ResearchState) -> dict:
    """Synthesize verified material into structured markdown."""
    hook = state.get("_progress_hook")
    if callable(hook):
        try:
            hook("report")
        except Exception:
            pass

    try:
        llm = get_chat_model()
        sys = SystemMessage(
            content=(
                "You are an expert researcher and master communicator. Your goal is to write a highly detailed, expansive, yet incredibly simple and easy-to-understand research report, exactly like Perplexity.ai does for a broad consumer audience. "
                "The tone must be engaging and deeply informative, but instantly accessible to non-experts. Avoid complex jargon. Break down complex topics into simple truths. "
                "You MUST return a comprehensive 'Overview' section (2-3 paragraphs diving deeply into the topic) and a 'Key Findings' section with 4 to 6 highly distinct, descriptive bullet points. "
                "You must never return an empty summary. "
                "You MUST use inline citations (e.g., [1]). "
                "You MUST completely exclude 'Contradictions Found' and 'Sources' from the main body text. "
                "Required sections with these exact headings (use ##): Overview, Key Findings."
            )
        )
        bundle = {
            "query": state.get("query", ""),
            "summaries": state.get("summaries", []),
            "critic": state.get("critic_output", {}),
            "pipeline_errors": state.get("errors", []),
        }
        human = HumanMessage(
            content=(
                "Produce the final report from this JSON:\n\n"
                f"{json.dumps(bundle, ensure_ascii=False, indent=2)}"
            )
        )
        out = llm.invoke([sys, human])
        text = (out.content if hasattr(out, "content") else str(out)).strip()
        if not text:
            return {
                "final_report": _minimal_report(state),
                "current_agent": "report",
                "errors": ["Report: empty LLM output; minimal report generated."],
            }
        return {"final_report": text, "current_agent": "report"}
    except Exception as e:
        return {
            "final_report": _minimal_report(state),
            "current_agent": "report",
            "errors": [f"Report agent failed: {e!s}; minimal report generated."],
        }
