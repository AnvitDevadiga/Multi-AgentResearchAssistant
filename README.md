<div align="center">

# Multi-Agent Research Assistant

### LangGraph-powered autonomous research with source validation

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-4_Agents-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST_API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama_3-F54E27?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

<br/>

> **4 specialized agents · Web search · Confidence scoring · Structured JSON + Markdown reports**

<br/>

---

</div>

## Highlights

| Capability | Implementation |
|---|---|
| **Multi-agent orchestration** | 4-agent LangGraph workflow (Search → Summarize → Critic → Report) |
| **Factual reliability** | Critic agent cross-checks sources, flags contradictions, scores claim confidence |
| **Production API** | FastAPI endpoint with structured JSON outputs for downstream apps |
| **Interactive demo** | Streamlit UI with live agent progress, tabs, and report download |
| **Cost-efficient stack** | Groq free tier + DuckDuckGo search (no paid search API required) |

<br/>

---

## Architecture

![Architecture](multi_agent_research_architecture.svg)

Each agent is a LangGraph node sharing typed state. The pipeline runs sequentially: retrieve sources, extract facts, validate claims, then compile a markdown report.

<br/>

---

## The 4 Agents

| Agent | Role | Output |
|---|---|---|
| **Search** | Queries DuckDuckGo, fetches page content | Top 5 URLs + text snippets |
| **Summarizer** | Extracts key facts from each source | Structured per-source summaries |
| **Critic** | Cross-checks claims across sources | Contradictions + confidence assessments |
| **Report** | Synthesizes verified material | Final markdown research report |

<br/>

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/AnvitDevadiga/research-assistant.git
cd research-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Add GROQ_API_KEY from https://console.groq.com (free tier)
```

### 3. Launch Streamlit UI (recommended for demos)

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501` — enter a query, watch the 4-agent pipeline progress, and explore results in tabs (Report · Sources · Validation · Raw JSON).

### 4. Or run the REST API

```bash
uvicorn app.api:app --reload
```

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "latest trends in AI agents"}'
```

<br/>

---

## API Reference

**POST** `/research`

**Request:**

```json
{
  "query": "your research question here"
}
```

**Response:**

```json
{
  "query": "latest trends in AI agents",
  "report": "## Overview\n...",
  "overview": "Short summary extracted from the report",
  "key_findings": ["Finding 1", "Finding 2"],
  "contradictions": ["Source A says X; Source B says Y"],
  "assessments": [
    {
      "claim": "LangGraph adoption grew in 2026",
      "confidence": "high",
      "notes": "Supported by multiple sources"
    }
  ],
  "sources": [
    {
      "url": "https://example.com",
      "title": "Example Article",
      "summary": "Brief summary of the source"
    }
  ],
  "confidence": "HIGH",
  "source_count": 5,
  "errors": [],
  "current_agent": "report"
}
```

Interactive docs: `http://localhost:8000/docs`

<br/>

---

## Project Structure

```
Multi-AgentResearchAssistant/
├── app/
│   ├── agents/
│   │   ├── search_agent.py       # DuckDuckGo search + content fetch
│   │   ├── summarizer_agent.py   # LLM-powered summarization
│   │   ├── critic_agent.py       # Contradiction detection + confidence
│   │   └── report_agent.py       # Final report compilation
│   ├── graph.py                  # LangGraph state machine
│   ├── api.py                    # FastAPI REST endpoints
│   ├── structured_output.py      # Structured JSON from pipeline state
│   ├── llm.py                    # Groq LLM configuration
│   └── state.py                  # Shared agent state schema
├── streamlit_app.py              # Interactive demo UI
├── requirements.txt
├── Procfile                      # Render.com deployment
└── .env.example
```

<br/>

---

## Live Demo

Deployed API: **[research-assistant-k824.onrender.com](https://research-assistant-k824.onrender.com)**

> Free tier may sleep after inactivity. First request can take ~30s to wake up.

<br/>

---

## Skills Demonstrated

- **Agentic AI:** Multi-step LangGraph workflows with typed shared state
- **LLM engineering:** Structured JSON extraction, fallbacks, prompt design per agent role
- **Backend:** FastAPI REST API with Pydantic models and CORS
- **Frontend:** Streamlit dashboard with live progress and export
- **DevOps:** Render deployment via Procfile

<br/>

---

<div align="center">

**Built by [Anvit Devadiga](https://github.com/AnvitDevadiga)**

[![GitHub](https://img.shields.io/badge/GitHub-AnvitDevadiga-181717?style=for-the-badge&logo=github)](https://github.com/AnvitDevadiga)
[![Email](https://img.shields.io/badge/Email-anvitdevadiga@outlook.com-0078D4?style=for-the-badge&logo=microsoftoutlook&logoColor=white)](mailto:anvitdevadiga@outlook.com)

</div>
