import streamlit as st
import time
import base64
import threading
import os
from pathlib import Path
from streamlit.runtime.scriptrunner import add_script_run_ctx
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="MARA — Multi-Agent Research Assistant",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------
def _b64(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    import mimetypes
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


BG = _b64("bg.jpg")


# ---------------------------------------------------------------------------
# Backend — in-process LangGraph pipeline (no server needed)
# ---------------------------------------------------------------------------
def _run_research(query: str) -> dict:
    from app.graph import run_research
    from app.structured_output import structured_from_state
    state = run_research(query)
    structured = structured_from_state(state)
    structured["errors"] = list(state.get("errors") or [])
    return structured


# ═══════════════════════════════════════════════════════════════════════════
# CSS — pixel-perfect match to the reference mockup
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {{
    --gold:       #c29d66;
    --gold-dim:   #8b7355;
    --gold-faint: rgba(194,157,102,.10);
    --tan:        #e3d4c1;
    --wood:       rgba(34,26,18,.92);
    --vine:       rgba(13,25,16,.92);
    --vine-b:     #1e3a25;
    --stone:      #3a3a3a;
    --green:      #4ade80;
}}

/* ── Full-bleed background ────────────────────────────────────────────── */
html, body, .stApp {{
    background: url('{BG}') no-repeat center top / cover fixed !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}}
#MainMenu, footer, header, [data-testid="stToolbar"] {{ display:none!important; }}

.block-container {{
    padding: 1.8rem 2rem 1.2rem;
    max-width: 1100px;
}}

/* ═══════════════ HEADER ═══════════════════════════════════════════════ */
.mh {{
    text-align: center;
    padding-bottom: .8rem;
}}
.mh h1 {{
    font-family: 'Cinzel', serif !important;
    font-weight: 700 !important;
    font-size: 2.8rem !important;
    color: var(--gold) !important;
    margin: 0 !important;
    line-height: 1.15 !important;
    text-shadow: 0 2px 20px rgba(0,0,0,.9), 0 0 60px rgba(194,157,102,.18);
}}

/* ═══════════════ BADGES ══════════════════════════════════════════════ */
.br {{
    display: flex; gap: .6rem;
    justify-content: center; flex-wrap: wrap;
    margin-top: .7rem;
}}
.hb {{
    background: var(--wood);
    border: 1.5px solid var(--gold-dim);
    color: var(--tan);
    font-size: .82rem; font-weight: 600;
    padding: .32rem .85rem;
    border-radius: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,.7), inset 0 1px 0 rgba(255,255,255,.04);
    backdrop-filter: blur(6px);
    white-space: nowrap;
}}

/* ═══════════════ SEARCH BAR (bottom) ════════════════════════════════ */
div[data-testid="stForm"] {{
    background: var(--vine) !important;
    border: 1.5px solid var(--vine-b) !important;
    border-radius: 14px !important;
    padding: .6rem 1rem !important;
    box-shadow: 0 4px 30px rgba(0,0,0,.6) !important;
    backdrop-filter: blur(10px) !important;
    margin-top: .3rem !important;
}}
div[data-baseweb="input"] {{
    background: rgba(0,0,0,.35) !important;
    border: 1px solid rgba(30,58,37,.7) !important;
    border-radius: 10px !important;
}}
div[data-baseweb="input"]:focus-within {{
    border-color: var(--green) !important;
    box-shadow: 0 0 0 2px rgba(74,222,128,.12) !important;
}}
input {{
    color: var(--tan) !important;
    font-size: 1rem !important; font-weight: 500 !important;
}}
input::placeholder {{ color: #7a6f5f !important; opacity:1!important; }}

/* submit */
div[data-testid="stFormSubmitButton"] > button {{
    background: var(--wood) !important;
    border: 1.5px solid var(--gold-dim) !important;
    color: var(--green) !important;
    font-size: .95rem !important; font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    border-radius: 8px !important;
    padding: .45rem 1.3rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.5) !important;
    transition: all .15s;
}}
div[data-testid="stFormSubmitButton"] > button:hover {{
    background: rgba(194,157,102,.18) !important;
    border-color: var(--gold) !important;
}}

/* ═══════════════ CONTAINERS ═════════════════════════════════════════ */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: rgba(8,14,10,.82) !important;
    backdrop-filter: blur(18px) !important;
    -webkit-backdrop-filter: blur(18px) !important;
    border: 1px solid rgba(139,115,85,.22) !important;
    border-radius: 12px !important;
    padding: 1.4rem !important;
    box-shadow: 0 6px 24px rgba(0,0,0,.45) !important;
}}

/* ═══════════════ STATUS ═════════════════════════════════════════════ */
div[data-testid="stStatusWidget"] {{
    background: rgba(13,25,16,.9) !important;
    border: 1px solid var(--vine-b) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(8px) !important;
}}

/* ═══════════════ TYPOGRAPHY ═════════════════════════════════════════ */
p, span, label,
div.stMarkdown, div.stMarkdown p, div.stMarkdown li,
div.stMarkdown span, div.stMarkdown a {{
    font-family: 'Inter', system-ui, sans-serif !important;
    color: var(--tan) !important;
    line-height: 1.75 !important;
    font-size: 1rem !important;
}}
h2, h3, h4 {{
    font-family: 'Cinzel', serif !important;
    color: var(--gold) !important;
    font-weight: 600 !important;
}}
h3 {{ font-size: 1.15rem !important; margin-bottom: .6rem !important; }}

div.stMarkdown code {{
    font-family: 'Inter', sans-serif !important;
    background: var(--gold-faint) !important;
    color: var(--gold) !important;
    padding: .1rem .35rem; border-radius: 4px;
}}
div.stMarkdown ul {{ padding-left: 1.3rem !important; }}
div.stMarkdown li {{ margin-bottom: .5rem !important; }}

/* ── Section labels ──────────────────────────────────────────────────── */
.sl {{
    color: var(--gold);
    font-family: 'Cinzel', serif;
    font-size: .78rem; font-weight: 600;
    letter-spacing: .12em; text-transform: uppercase;
    margin-bottom: .8rem;
    display: flex; align-items: center; gap: .5rem;
}}
.sl::before {{
    content: ""; width: 6px; height: 6px;
    border-radius: 50%; background: var(--gold);
    box-shadow: 0 0 6px var(--gold); display: block;
}}

/* ── Source rows ──────────────────────────────────────────────────────── */
.sr {{
    display: flex; align-items: baseline; gap: .8rem;
    padding: .7rem 1rem; margin-bottom: .5rem;
    background: rgba(0,0,0,.25);
    border: 1px solid rgba(139,115,85,.12);
    border-left: 3px solid var(--gold);
    border-radius: 7px;
    text-decoration: none !important;
    transition: all .18s ease;
}}
.sr:hover {{
    background: var(--gold-faint);
    border-color: rgba(194,157,102,.3);
    transform: translateX(3px);
}}
.sr span {{ color: var(--tan) !important; }}
.sr .ix {{
    color: var(--gold) !important;
    font-weight: 700; font-size: .88rem; flex-shrink: 0;
}}

/* ── Metrics ──────────────────────────────────────────────────────────── */
div[data-testid="stMetric"] {{
    background: rgba(0,0,0,.3) !important;
    border: 1px solid rgba(139,115,85,.18) !important;
    border-radius: 10px; padding: 1.2rem; text-align: center;
}}
div[data-testid="stMetricValue"] {{
    color: var(--gold) !important;
    font-family: 'Cinzel', serif !important;
    font-size: 2.6rem !important; font-weight: 500 !important;
}}
div[data-testid="stMetricLabel"] {{
    color: var(--tan) !important;
    font-size: .78rem !important; font-weight: 600 !important;
    letter-spacing: .12em !important; text-transform: uppercase;
    justify-content: center;
}}

/* ── Alerts ───────────────────────────────────────────────────────────── */
div[data-testid="stAlertContentSuccess"] {{
    background: rgba(74,222,128,.06) !important;
    border: 1px solid rgba(74,222,128,.15) !important;
    border-radius: 8px !important;
}}
div[data-testid="stAlertContentWarning"] {{
    background: rgba(250,204,21,.06) !important;
    border: 1px solid rgba(250,204,21,.15) !important;
    border-radius: 8px !important;
}}

details {{ background: rgba(0,0,0,.2) !important; border-radius: 7px !important; }}
hr {{ border-color: rgba(139,115,85,.12) !important; }}

.stButton > button {{
    background: var(--wood) !important;
    border: 1px solid var(--gold-dim) !important;
    color: var(--gold) !important;
    border-radius: 7px !important; font-weight: 600 !important;
}}
.stButton > button:hover {{
    background: rgba(194,157,102,.12) !important;
    border-color: var(--gold) !important;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<div class="mh">
    <h1>🐘 MARA (Multi-Agent Research assistant)</h1>
    <div class="br">
        <span class="hb">🐾 Core Agent: Baloo (Wisdom &amp; Knowledge)</span>
        <span class="hb">🍁 Forest Knowledge: 2.89 Billion Scents</span>
        <span class="hb">🟢 Hidden Jungle Path</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════
# WORKER
# ═══════════════════════════════════════════════════════════════════════════
class ResearchThread(threading.Thread):
    def __init__(self, query: str):
        super().__init__()
        self.query = query
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = _run_research(self.query)
        except Exception as exc:
            self.error = str(exc)


# ═══════════════════════════════════════════════════════════════════════════
# RESULTS AREA (above search bar)
# ═══════════════════════════════════════════════════════════════════════════
result_area = st.container()

# ═══════════════════════════════════════════════════════════════════════════
# SEARCH BAR (bottom)
# ═══════════════════════════════════════════════════════════════════════════
with st.form("search_form", clear_on_submit=False):
    query = st.text_input(
        "Query",
        label_visibility="collapsed",
        placeholder=(
            "Explore the Jungle's wisdom, life, or history... "
            "Ask about 'The Red Flower', 'Hathi's Law', "
            "or 'The Seeonee Pack'..."
        ),
    )
    submit = st.form_submit_button("🍃 Search the Jungle")


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════
if submit and query:
    thread = ResearchThread(query)
    add_script_run_ctx(thread)
    thread.start()

    with result_area:
        with st.status("Awakening the jungle spirits…", expanded=True) as status:
            stages = [
                "🐻 Baloo is consulting the ancient stone tablets…",
                "🐆 Bagheera is tracking the scent through the canopy…",
                "🐍 Kaa is unwinding the hidden knowledge…",
                "🐘 Hathi is remembering the oldest law…",
            ]
            step = 0
            while thread.is_alive():
                status.write(stages[step] if step < len(stages) else "✨ Gathering the final wisdom…")
                step += 1
                time.sleep(2.5)

            if thread.error:
                status.update(label="Trail went cold", state="error")
                st.error(f"Error: {thread.error}")
            else:
                status.update(label="Wisdom recovered ✨", state="complete")

        if thread.result and not thread.error:
            data = thread.result
            st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

            col_main, col_hud = st.columns([7, 3], gap="large")

            with col_main:
                sources = data.get("sources", [])
                if sources:
                    with st.container(border=True):
                        st.markdown('<div class="sl">Ancient Carvings</div>', unsafe_allow_html=True)
                        html = ""
                        for i, src in enumerate(sources):
                            t = src.get("title", "Source Document")
                            u = src.get("url", "#")
                            html += (
                                f'<a href="{u}" class="sr" target="_blank">'
                                f'<span class="ix">[{i+1:02d}]</span>'
                                f"<span>{t}</span></a>"
                            )
                        st.markdown(html, unsafe_allow_html=True)

                st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

                overview = data.get("overview")
                findings = data.get("key_findings", [])

                if overview:
                    with st.container(border=True):
                        st.markdown('<div class="sl">Jungle Lore</div>', unsafe_allow_html=True)
                        st.markdown(overview)
                        if findings:
                            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
                            st.markdown('<div class="sl">Key Findings</div>', unsafe_allow_html=True)
                            for f in findings:
                                st.markdown(f"- {f}")
                else:
                    st.warning("Data incomplete — overview missing.")
                    with st.expander("Raw payload"):
                        st.json(data)

            with col_hud:
                with st.container(border=True):
                    st.markdown('<div class="sl">Path Confidence</div>', unsafe_allow_html=True)
                    st.metric(label="Score", value=data.get("confidence", "—"))

                st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

                with st.container(border=True):
                    st.markdown('<div class="sl">Anomalies</div>', unsafe_allow_html=True)
                    contradictions = data.get("contradictions", [])
                    if contradictions:
                        st.warning(
                            "False trails:\n\n"
                            + "\n".join(f"- {c}" for c in contradictions)
                        )
                    else:
                        st.success("No false trails. The path is true.")

                errors = data.get("errors", [])
                if errors:
                    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
                    with st.container(border=True):
                        st.markdown('<div class="sl">Pipeline Notes</div>', unsafe_allow_html=True)
                        for e in errors:
                            st.caption(f"⚠️ {e}")
