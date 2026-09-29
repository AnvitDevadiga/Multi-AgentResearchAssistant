"""FastAPI application: POST /research and GET /research/stream."""
from __future__ import annotations

import os
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.graph import run_research, get_compiled_graph, initial_state
from app.structured_output import structured_from_state

load_dotenv()


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User research question")


class SourceItem(BaseModel):
    url: str
    title: str = ""
    summary: str = ""


class ConfidenceAssessment(BaseModel):
    claim: str
    confidence: str
    notes: str = ""


class ResearchResponse(BaseModel):
    query: str
    report: str = Field(..., description="Final markdown report")
    overview: str = ""
    key_findings: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    assessments: list[ConfidenceAssessment] = Field(default_factory=list)
    sources: list[SourceItem] = Field(default_factory=list)
    confidence: str = Field("MEDIUM", description="Overall confidence: HIGH | MEDIUM | LOW")
    source_count: int = 0
    errors: list[str] = Field(default_factory=list)
    current_agent: str = ""


def create_app() -> FastAPI:
    app = FastAPI(
        title="Multi-Agent Research Assistant",
        version="1.0.0",
        description=(
            "LangGraph 4-agent pipeline: Search → Summarize → Critic → Report. "
            "Returns structured JSON with confidence scoring and markdown report."
        ),
    )
    origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()] or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    def root():
        return """
        <html>
            <head>
                <title>Multi-Agent Research Assistant</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                        background: linear-gradient(160deg, #0b1220 0%, #111827 45%, #0f172a 100%);
                        color: #e5e7eb;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        flex-direction: column;
                        gap: 18px;
                        padding: 24px;
                    }
                    h1 { color: #38bdf8; font-size: 2.2rem; text-align: center; }
                    p { color: #94a3b8; font-size: 1rem; text-align: center; max-width: 560px; line-height: 1.6; }
                    .pipeline {
                        background: rgba(15, 23, 42, 0.85);
                        border: 1px solid #334155;
                        padding: 14px 28px;
                        border-radius: 12px;
                        color: #7dd3fc;
                        font-size: 0.95rem;
                        letter-spacing: 0.5px;
                    }
                    .badges {
                        display: flex;
                        gap: 10px;
                        flex-wrap: wrap;
                        justify-content: center;
                    }
                    .badge {
                        background: rgba(15, 23, 42, 0.85);
                        border: 1px solid #475569;
                        padding: 6px 14px;
                        border-radius: 999px;
                        font-size: 0.8rem;
                        color: #cbd5e1;
                    }
                    .btn {
                        background: #38bdf8;
                        color: #0f172a;
                        padding: 14px 32px;
                        border-radius: 10px;
                        text-decoration: none;
                        font-weight: 700;
                        font-size: 1rem;
                        margin-top: 8px;
                        transition: transform 0.15s, background 0.15s;
                    }
                    .btn:hover { background: #0ea5e9; transform: translateY(-1px); }
                </style>
            </head>
            <body>
                <h1>Multi-Agent Research Assistant</h1>
                <p>
                    Autonomous research pipeline with web search, source validation,
                    confidence scoring, and structured report generation.
                </p>
                <div class="pipeline">
                    Search → Summarize → Critic → Report
                </div>
                <div class="badges">
                    <span class="badge">LangGraph</span>
                    <span class="badge">Google Gemini</span>
                    <span class="badge">DuckDuckGo</span>
                    <span class="badge">FastAPI</span>
                </div>
                <a class="btn" href="/docs">Open API Docs →</a>
            </body>
        </html>
        """

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "multi-agent-research-assistant"}

    @app.post("/research", response_model=ResearchResponse)
    def research(req: ResearchRequest):
        if not os.environ.get("GOOGLE_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="GOOGLE_API_KEY is not configured on the server.",
            )
        q = req.query.strip()
        if not q:
            raise HTTPException(status_code=400, detail="Query must not be empty.")
        out = run_research(q)
        structured = structured_from_state(out)
        return ResearchResponse(
            query=q,
            report=structured.get("report", ""),
            overview=structured.get("overview", ""),
            key_findings=structured.get("key_findings", []),
            contradictions=structured.get("contradictions", []),
            assessments=structured.get("assessments", []),
            sources=structured.get("sources", []),
            confidence=structured.get("confidence", "MEDIUM"),
            source_count=structured.get("source_count", 0),
            errors=list(out.get("errors") or []),
            current_agent=str(out.get("current_agent") or ""),
        )

    @app.get("/research/stream")
    def research_stream(query: str):
        if not os.environ.get("GOOGLE_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="GOOGLE_API_KEY is not configured on the server.",
            )
        q = query.strip()
        if not q:
            raise HTTPException(status_code=400, detail="Query must not be empty.")

        async def event_generator():
            graph = get_compiled_graph()
            state = initial_state(q)
            for chunk in graph.stream(state, stream_mode="updates"):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app


app = create_app()
