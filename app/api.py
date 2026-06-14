"""FastAPI application: POST /research."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.graph import run_research
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
                    <span class="badge">Groq · Llama 3</span>
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
        if not os.environ.get("GROQ_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="GROQ_API_KEY is not configured on the server.",
            )
        q = req.query.strip()
        if not q:
            raise HTTPException(status_code=400, detail="Query must not be empty.")
        out = run_research(q)
        structured = structured_from_state(out)
        return ResearchResponse(
            query=q,
            report=structured["report"],
            overview=structured["overview"],
            key_findings=structured["key_findings"],
            contradictions=structured["contradictions"],
            assessments=structured["assessments"],
            sources=structured["sources"],
            confidence=structured["confidence"],
            source_count=structured["source_count"],
            errors=list(out.get("errors") or []),
            current_agent=str(out.get("current_agent") or ""),
        )

    return app


app = create_app()
    def root():
        return """
        <html>
            <head>
                <title>Multi-Agent Research Assistant</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: Arial, sans-serif;
                        background: #0f0f0f;
                        color: #fff;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        flex-direction: column;
                        gap: 16px;
                    }
                    h1 { color: #00ff88; font-size: 2rem; text-align: center; }
                    p { color: #aaa; font-size: 1rem; text-align: center; }
                    .pipeline {
                        background: #1a1a1a;
                        border: 1px solid #333;
                        padding: 12px 24px;
                        border-radius: 10px;
                        color: #00ff88;
                        font-size: 0.9rem;
                        letter-spacing: 1px;
                    }
                    .badges {
                        display: flex;
                        gap: 10px;
                        flex-wrap: wrap;
                        justify-content: center;
                    }
                    .badge {
                        background: #1a1a1a;
                        border: 1px solid #444;
                        padding: 6px 14px;
                        border-radius: 20px;
                        font-size: 0.8rem;
                        color: #ccc;
                    }
                    .btn {
                        background: #00ff88;
                        color: #000;
                        padding: 14px 32px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: bold;
                        font-size: 1rem;
                        margin-top: 10px;
                        transition: background 0.2s;
                    }
                    .btn:hover { background: #00cc66; }
                </style>
            </head>
            <body>
                <h1>🤖 Multi-Agent Research Assistant</h1>
                <p>An autonomous AI pipeline that researches, summarizes, critiques, and reports.</p>
                <div class="pipeline">
                    Search → Summarize → Critic → Report
                </div>
                <div class="badges">
                    <span class="badge">⚡ Groq LLM</span>
                    <span class="badge">🦙 Llama 3</span>
                    <span class="badge">🔗 LangGraph</span>
                    <span class="badge">🚀 FastAPI</span>
                </div>
                <a class="btn" href="/docs">Launch API →</a>
            </body>
        </html>
        """

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/research", response_model=ResearchResponse)
    def research(req: ResearchRequest):
        if not os.environ.get("GROQ_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="GROQ_API_KEY is not configured on the server.",
            )
        q = req.query.strip()
        if not q:
            raise HTTPException(status_code=400, detail="Query must not be empty.")
        out = run_research(q)
        return ResearchResponse(
            query=q,
            report=out.get("final_report") or "",
            errors=list(out.get("errors") or []),
            current_agent=str(out.get("current_agent") or ""),
        )

    return app

app = create_app()
