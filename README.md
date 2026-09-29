# Multi-Agent Research Assistant

A 100% headless, LangGraph-driven multi-agent research pipeline that crawls the web, aggregates sources, synthesizes data, identifies contradictions, and delivers consumer-friendly reports.

## Architecture

The backend is built with FastAPI and orchestrated by LangGraph, utilizing the powerful reasoning capabilities of **Google Gemini 1.5 Flash**.

The workflow consists of four dedicated agents:
1. **Search Agent**: Scours the web using DuckDuckGo to aggregate raw intelligence.
2. **Summarizer Agent**: Processes raw web pages to extract key facts and distinct metrics.
3. **Critic Agent**: Reviews all intelligence to identify and flag any contradictions or anomalies.
4. **Report Agent**: Synthesizes the verified data into a flowing, professional Perplexity.ai-style report.

## The Dashboard

The UI is built on Streamlit with a highly polished "Deep Canopy Jungle" aesthetic. It cleanly decouples the pure markdown narrative from the system diagnostics (such as the Confidence Score and Anomaly Detection metrics), resulting in a premium, commercial-grade user experience.

## Running the Application

### 1. Setup Environment
Ensure your `.env` file contains your Google API key:
```bash
GOOGLE_API_KEY=your_key_here
```

### 2. Start the FastAPI Backend
```bash
uvicorn app.api:app --host 127.0.0.1 --port 8080 --reload
```

### 3. Start the Streamlit Dashboard
Open a new terminal window and run:
```bash
streamlit run dashboard.py
```
