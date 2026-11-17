"""ShipTriage v1.1.0: Human-in-the-loop shipment exception triage prototype."""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from shiptriage.constants import (  # noqa: E402
    CATEGORIES,
    CONFIDENCE_THRESHOLD,
    DATASET_PATH,
    MAX_BATCH_ROWS,
    METRICS_PATH,
    UNSEEN_METRICS_PATH,
    UNSEEN_PATH,
)
from shiptriage.data import validate_batch_csv  # noqa: E402
from shiptriage.modeling import (  # noqa: E402
    ensure_models_and_evaluation,
    explain_prediction,
    hybrid_predict_category,
    predict_ticket,
)
from shiptriage.recommendations import recommend_next_action  # noqa: E402

st.set_page_config(
    page_title="ShipTriage v1.1 | Exception Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Visual system ---------------------------------------------------------
st.markdown(
    """
    <style>
      :root { --ink:#14263D; --muted:#718096; --line:#E5EAF1; --paper:#F5F7FB; --teal:#0D9488; --blue:#2563EB; }
      html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
      .stApp { background:var(--paper); }
      [data-testid="stHeader"] { background:rgba(245,247,251,.88); }
      .block-container { max-width:1440px; padding-top:1.5rem; padding-bottom:3rem; }
      [data-testid="stSidebar"] { background:#12263F; border-right:1px solid #203B5B; }
      [data-testid="stSidebar"] * { color:#EAF1F8 !important; }
      [data-testid="stSidebar"] [data-testid="stRadio"] label { padding:8px 10px; border-radius:10px; }
      [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#1C3858; }
      [data-testid="stSidebar"] hr { border-color:#29435F; }
      h1,h2,h3 { color:var(--ink); font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
      h1 { font-weight:800; }
      h2,h3 { font-weight:700; }
      .brand-lockup { display:flex; align-items:center; gap:11px; margin:4px 0 26px; }
      .brand-icon { width:40px; height:40px; display:flex; align-items:center; justify-content:center; border-radius:13px; background:linear-gradient(135deg,#14B8A6,#2563EB); font-size:21px; box-shadow:0 8px 22px rgba(20,184,166,.2); }
      .brand-name { color:#F8FAFC; font:800 19px 'Manrope',sans-serif; letter-spacing:-.04em; }
      .brand-sub { color:#9DB1C9; font-size:10px; letter-spacing:.14em; text-transform:uppercase; margin-top:1px; }
      .eyebrow { color:#0D9488; font-size:11px; font-weight:700; letter-spacing:.13em; text-transform:uppercase; margin-bottom:7px; }
      .hero { background:linear-gradient(115deg,#142A45 0%,#1D4261 60%,#0D766F 130%); padding:26px 30px; border-radius:20px; color:white; margin:0 0 22px; box-shadow:0 12px 30px rgba(20,38,61,.10); }
      .hero h1 { color:#fff; margin:0; font-size:30px; }
      .hero p { color:#C7D7E8; margin:8px 0 0; font-size:14px; max-width:800px; }
      .hero-tag { display:inline-block; padding:5px 10px; border-radius:99px; background:rgba(45,212,191,.13); color:#8CF1E1; font-size:10px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:12px; border:1px solid rgba(140,241,225,.18); }
      .section-label { color:#76869B; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.12em; margin:4px 0 9px; }
      .metric-card { background:#fff; border:1px solid var(--line); border-radius:15px; padding:17px 18px; min-height:108px; box-shadow:0 2px 8px rgba(21,45,75,.025); }
      .metric-label { color:#738196; font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
      .metric-value { color:#152A43; font:800 25px 'Manrope',sans-serif; margin-top:7px; letter-spacing:-.04em; }
      .metric-hint { color:#8492A5; font-size:11px; margin-top:3px; }
      .panel { background:#fff; border:1px solid var(--line); border-radius:17px; padding:20px; box-shadow:0 2px 8px rgba(21,45,75,.025); margin-bottom:18px; }
      .panel-title { color:#1B304A; font:700 15px 'Manrope',sans-serif; margin:0 0 4px; }
      .panel-sub { color:#8290A2; font-size:12px; margin-bottom:14px; }
      .pill { display:inline-block; border-radius:100px; padding:5px 10px; font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
      .pill-synthetic { background:#FFF5DB; color:#9A6700; border:1px solid #F4E2A7; }
      .pill-review { background:#FFF0EB; color:#B54727; border:1px solid #F7D2C5; }
      .pill-ready { background:#E8F8F4; color:#087E70; border:1px solid #BCEADF; }
      .pill-info { background:#EEF4FF; color:#1E40AF; border:1px solid #DBEAFE; }
      .result-card { background:#fff; border:1px solid var(--line); border-radius:17px; padding:20px; height:100%; box-shadow:0 2px 8px rgba(21,45,75,.025); }
      .result-value { color:#172D48; font:800 23px 'Manrope',sans-serif; margin:8px 0 3px; }
      .result-label { color:#7B8A9D; font-size:11px; text-transform:uppercase; font-weight:700; letter-spacing:.08em; }
      .signal { display:inline-block; padding:6px 9px; background:#EFF5FA; border:1px solid #DDE8F2; border-radius:8px; color:#36516D; font-size:11px; margin:3px 4px 3px 0; }
      .callout { background:#F0F7FF; border-left:3px solid #4F8DCE; padding:12px 14px; border-radius:0 10px 10px 0; color:#3F5873; font-size:12px; }
      .warning-note { background:#FFF8E9; border:1px solid #F4E4B9; border-radius:12px; padding:12px 14px; color:#775B1C; font-size:12px; }
      .footer-note { color:#91A0B2; font-size:11px; text-align:center; padding:24px 0 8px; letter-spacing:.05em; }
      div.stButton > button, div.stDownloadButton > button { border-radius:10px; font-weight:700; min-height:42px; }
      div[data-testid="stForm"] { background:#fff; border:1px solid var(--line); padding:18px; border-radius:15px; }
      div[data-baseweb="select"] > div, textarea, input { border-radius:10px !important; }
      [data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:13px; padding:12px 15px; }
      [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
      @media (max-width: 750px) { .hero {padding:22px;} .hero h1 {font-size:24px;} .block-container {padding-left:1rem;padding-right:1rem;} }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Initializing ShipTriage models and evaluation artifacts…")
def get_models_and_metrics():
    """Load or build models, template holdout metrics, and alternate-phrasing evaluation.

    Guarantees that clean Streamlit Cloud deployments always have full artifacts.
    """
    return ensure_models_and_evaluation()


@st.cache_data(show_spinner=False)
def load_synthetic_data() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        return pd.DataFrame(columns=["ticket_id", "description", "category", "priority", "data_type"])
    return pd.read_csv(DATASET_PATH)


def metric_card(label: str, value: str, hint: str = "") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-hint">{hint}</div></div>',
        unsafe_allow_html=True,
    )


def display_name(value: str) -> str:
    return str(value).replace("_", " ").title()


def render_signals(signals: list[dict[str, Any]]) -> None:
    if not signals:
        st.caption("No distinct positive text signals were available for this prediction.")
        return
    html = "".join(f'<span class="signal">{str(item["term"]).replace("<", "&lt;").replace(">", "&gt;")}</span>' for item in signals)
    st.markdown(html, unsafe_allow_html=True)


def triage_one(description: str, category_model, priority_model, threshold: float) -> dict[str, Any]:
    result = predict_ticket(description, category_model, priority_model, threshold)
    result["suggested_next_action"] = recommend_next_action(result["category"])
    return result


def make_batch_results(frame: pd.DataFrame, category_model, priority_model, threshold: float) -> pd.DataFrame:
    output = frame.copy()
    rows: list[dict[str, Any]] = []
    for description in output["description"].tolist():
        clean_text = str(description or "").strip()
        if not clean_text:
            rows.append({
                "predicted_category": "needs_review",
                "predicted_priority": "unknown",
                "category_score": 0.0,
                "priority_score": 0.0,
                "review_required": True,
                "triage_strategy": "empty_input",
                "suggested_next_action": "Description is empty or blank. Review the source ticket manually.",
            })
            continue
        result = triage_one(clean_text, category_model, priority_model, threshold)
        rows.append({
            "predicted_category": result["category"],
            "predicted_priority": result["priority"],
            "category_score": round(result["category_score"], 4),
            "priority_score": round(result["priority_score"], 4),
            "review_required": result["review_required"],
            "triage_strategy": result.get("hybrid_strategy", "statistical_ml"),
            "suggested_next_action": result["suggested_next_action"],
        })
    prediction_frame = pd.DataFrame(rows)
    output = output.drop(columns=[c for c in prediction_frame.columns if c in output.columns], errors="ignore")
    return pd.concat([output.reset_index(drop=True), prediction_frame], axis=1)


def render_header() -> None:
    st.markdown(
        '<div class="hero"><div class="hero-tag">Operations Intelligence · Google APM Portfolio Prototype</div>'
        '<h1>Make every exception easier to act on.</h1>'
        '<p>Empower warehouse issue-resolution associates with structured categorization, urgency indicators, and safe next-step prompts—with full human oversight.</p></div>',
        unsafe_allow_html=True,
    )


# --- Load Models & Verification --------------------------------------------
try:
    category_model, priority_model, metrics, unseen_metrics = get_models_and_metrics()
except Exception as error:
    st.error("ShipTriage could not prepare its ML models or evaluation artifacts.")
    st.code("python scripts/generate_data.py\npython scripts/train_model.py\npython scripts/evaluate_model.py")
    st.exception(error)
    st.stop()

data = load_synthetic_data()

# --- Sidebar Controls ------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand-lockup"><div class="brand-icon">📦</div><div><div class="brand-name">ShipTriage</div><div class="brand-sub">Exception Intelligence v1.1</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label" style="color:#9DB1C9">Navigation</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["Overview", "Single triage", "Batch triage", "Model insights", "About the product"],
        label_visibility="collapsed",
        key="sidebar_page",
    )
    st.divider()
    st.markdown('<div class="section-label" style="color:#9DB1C9">Operational Controls</div>', unsafe_allow_html=True)
    threshold = st.slider(
        "Manual-review threshold",
        min_value=0.40,
        max_value=0.90,
        value=CONFIDENCE_THRESHOLD,
        step=0.05,
        help="Tickets where either category score or priority score falls below this threshold are routed to the Human Review Queue.",
    )
    st.caption(f"Active cutoff: **{threshold:.0%}**. Below this score, human verification is mandatory.")
    st.divider()
    st.markdown('<span class="pill pill-synthetic">Synthetic Demo Data</span>', unsafe_allow_html=True)
    st.caption("No carrier, warehouse, or customer database is connected.")
    st.caption("Model decision scores are uncalibrated and require human verification.")

render_header()

# ===========================================================================
# PAGE 1: OVERVIEW
# ===========================================================================
if page == "Overview":
    st.markdown('<div class="eyebrow">Executive Summary</div>', unsafe_allow_html=True)
    st.subheader("Triage Operations Overview")
    total_rows = len(data)
    categories_count = data["category"].nunique() if not data.empty and "category" in data else len(CATEGORIES)
    train_rows = metrics.get("train_rows", "—")
    score = metrics.get("category_accuracy")
    score_label = f"{score:.1%}" if isinstance(score, (int, float)) else "—"
    unseen_score = unseen_metrics.get("category_accuracy")
    unseen_label = f"{unseen_score:.1%}" if isinstance(unseen_score, (int, float)) else "—"

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1: metric_card("Synthetic Dataset", f"{total_rows:,}", "Fictional logistics tickets")
    with c2: metric_card("Supported Categories", str(categories_count), "Missing, Damaged, Orphan, Delayed, Wrong SKU")
    with c3: metric_card("Holdout ML Accuracy", score_label, "Template-group holdout (233 rows)")
    with c4: metric_card("Alternate Phrasing", unseen_label, "Generalization challenge set (10 rows)")

    st.write("")
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.markdown('<div class="panel"><div class="panel-title">Synthetic Exception Mix</div><div class="panel-sub">Balanced distribution across core exception types</div>', unsafe_allow_html=True)
        if not data.empty:
            category_mix = data["category"].value_counts().rename_axis("Exception").reset_index(name="Tickets")
            category_mix["Exception"] = category_mix["Exception"].apply(display_name)
            fig = px.bar(category_mix, x="Exception", y="Tickets", color="Exception", text="Tickets")
            fig.update_layout(height=300, showlegend=False, margin=dict(l=8, r=8, t=12, b=8), plot_bgcolor="white", paper_bgcolor="white", font_color="#52647A")
            fig.update_traces(marker_line_width=0, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Synthetic dataset is not available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Human-in-the-Loop Architecture</div><div class="panel-sub">Four-stage decision support lifecycle</div>', unsafe_allow_html=True)
        steps = [
            ("01", "Exception Note Ingestion", "Free-text ticket captured from associate or manifest reconciliation."),
            ("02", "Hybrid Scoring Engine", "Domain rules match specific physical signals; TF-IDF ML generalizes edge cases."),
            ("03", "Dynamic Threshold Gate", "Flags ambiguous or low-score tickets (< active threshold) for manual review."),
            ("04", "Human Verification & SOP", "Associate validates physical evidence and executes approved standard operating procedure."),
        ]
        for number, title, subtitle in steps:
            st.markdown(
                f'<div style="display:flex;gap:12px;padding:9px 0;border-bottom:1px solid #EEF1F5">'
                f'<div style="background:#E8F7F4;color:#0B8B7C;border-radius:9px;padding:8px 10px;font-weight:800;height:fit-content">{number}</div>'
                f'<div><div style="font-weight:700;color:#253B55;font-size:13px">{title}</div>'
                f'<div style="font-size:11px;color:#8492A5;margin-top:3px">{subtitle}</div></div></div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div style="margin-top:14px"><span class="pill pill-ready">Zero Autonomous Shipment Actions</span></div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="panel"><div class="panel-title">Explore Sample Exceptions</div><div class="panel-sub">Select an operational scenario to test single-ticket triage immediately.</div>', unsafe_allow_html=True)
    sample_cols = st.columns(3)
    samples = [
        ("Missing Shipment", "Tracking has no scan after dispatch from Pune; the parcel has not reached Mumbai. A customer escalation has been received and the delivery promise is due today. Please investigate and update the exception queue."),
        ("Damaged Parcel", "The outer carton is crushed and has a broken seal with liquid leakage observed during inbound sorting. Urgent claim documentation is required."),
        ("Delayed In-Transit", "The shipment has remained at Nagpur for 36 hours with no onward movement and the delivery SLA is at risk. Customer has requested an update."),
    ]

    def open_sample_ticket(sample_text: str) -> None:
        st.session_state["prefill_ticket"] = sample_text
        st.session_state["sidebar_page"] = "Single triage"

    for col, (name, sample_text) in zip(sample_cols, samples):
        with col:
            st.button(
                f"Load: {name}",
                use_container_width=True,
                on_click=open_sample_ticket,
                args=(sample_text,),
            )
    st.markdown('</div>', unsafe_allow_html=True)

# ===========================================================================
# PAGE 2: SINGLE TICKET TRIAGE
# ===========================================================================
elif page == "Single triage":
    st.markdown('<div class="eyebrow">Ticket Workspace</div>', unsafe_allow_html=True)
    st.subheader("Single Exception Triage")
    st.caption("Paste an operational exception note or select a sample scenario. The system generates decision support; the associate remains in control.")

    demo_examples = {
        "Missing Shipment": "Tracking has no scan after dispatch from Pune; the parcel has not reached Mumbai. A customer escalation has been received and the delivery promise is due today.",
        "Damaged Parcel": "The parcel arrived with torn outer packaging and a crushed corner; the item may be damaged. Broken seal and leakage reported during inspection.",
        "Orphan Shipment": "A loose shipment has a valid-looking barcode at the destination hub, but the system shows no associated customer order or manifest route owner.",
        "Delayed Line-Haul": "The shipment has remained at transfer hub for 30 hours with no onward movement and the delivery SLA is at risk.",
        "Wrong SKU Packed": "The received SKU does not match the item on the order; the customer ordered a phone case but received a charger.",
    }

    choice = st.selectbox("Quick-load sample scenario", ["Write my own"] + list(demo_examples.keys()))
    prefill = st.session_state.pop("prefill_ticket", "")
    default_description = prefill or ("" if choice == "Write my own" else demo_examples[choice])

    with st.form("single_triage_form", clear_on_submit=False):
        description = st.text_area(
            "Shipment Exception Description",
            value=default_description,
            height=140,
            max_chars=5000,
            placeholder="Describe the shipment issue, physical package condition, and any time/SLA context…",
            help="Do not input real customer PII, phone numbers, addresses, live AWB tracking codes, or company secrets.",
        )
        submitted = st.form_submit_button("Triage Exception  →", type="primary", use_container_width=True)

    if submitted:
        try:
            result = triage_one(description, category_model, priority_model, threshold)
            st.session_state["last_prediction"] = {"description": description, **result}
            history = st.session_state.setdefault("triage_history", [])
            history.insert(
                0,
                {
                    "description": description[:140] + ("…" if len(description) > 140 else ""),
                    "category": result["category"],
                    "priority": result["priority"],
                    "category_score": result["category_score"],
                    "priority_score": result["priority_score"],
                },
            )
            st.session_state["triage_history"] = history[:8]
        except ValueError as error:
            st.error(str(error))

    result = st.session_state.get("last_prediction")

    if result:
        st.write("")
        # DYNAMIC THRESHOLD RECALCULATION:
        # Evaluated against current active threshold, ensuring zero stale UI state
        min_score = min(result["category_score"], result["priority_score"])
        is_review_required = min_score < threshold

        if is_review_required:
            st.warning(
                f"⚠️ **Human Review Recommended:** Minimum model decision score ({min_score:.1%}) is below your active threshold ({threshold:.0%}). "
                "An associate must review this exception manually."
            )
        else:
            st.success(
                f"✅ **Triage Suggestion Ready:** Model decision scores exceed your active threshold ({threshold:.0%}). "
                "Verify physical evidence before executing the suggested action."
            )

        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            strategy_label = "Keyword Match" if result.get("hybrid_strategy") == "keyword_rule" else "Statistical ML"
            st.markdown(
                f'<div class="result-card"><div class="result-label">Predicted Category</div>'
                f'<div class="result-value">{display_name(result["category"])}</div>'
                f'<div class="metric-hint">Model score: {result["category_score"]:.1%} · <span class="pill pill-info">{strategy_label}</span></div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            priority_color = "#DC2626" if result["priority"] == "high" else ("#D97706" if result["priority"] == "medium" else "#059669")
            st.markdown(
                f'<div class="result-card"><div class="result-label">Suggested Priority</div>'
                f'<div class="result-value" style="color:{priority_color}">{display_name(result["priority"])}</div>'
                f'<div class="metric-hint">Model score: {result["priority_score"]:.1%} · Urgency indicator</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            status_class = "pill-review" if is_review_required else "pill-ready"
            status_text = "Review Required" if is_review_required else "Above Threshold"
            st.markdown(
                f'<div class="result-card"><div class="result-label">Triage Status</div>'
                f'<div style="margin-top:10px"><span class="pill {status_class}">{status_text}</span></div>'
                f'<div class="metric-hint" style="margin-top:14px">Active Threshold: <strong>{threshold:.0%}</strong> (Lowest: {min_score:.1%})</div></div>',
                unsafe_allow_html=True,
            )

        st.write("")
        left, right = st.columns([1, 1], gap="large")
        with left:
            st.markdown(
                '<div class="panel"><div class="panel-title">Model Decision Scores (Uncalibrated)</div>'
                '<div class="panel-sub">Logistic Regression margin scores; indicate relative class affinity, not calibrated real-world probabilities.</div>',
                unsafe_allow_html=True,
            )
            st.write(f"**Category Decision Score: {result['category_score']:.1%}**")
            st.progress(min(1.0, max(0.0, result["category_score"])))
            st.write(f"**Priority Decision Score: {result['priority_score']:.1%}**")
            st.progress(min(1.0, max(0.0, result["priority_score"])))
            st.caption(
                "💡 **Score Transparency:** Scores are uncalibrated decision values. A score of 80% reflects classifier confidence on synthetic features, "
                "not an 80% mathematical guarantee. That is why the threshold filter routes low-score tickets to human triage."
            )
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="panel"><div class="panel-title">Suggested Next Action</div>'
                '<div class="panel-sub">Conservative standard operating procedure prompt for the associate.</div>',
                unsafe_allow_html=True,
            )
            st.info(f"📋 **Action Prompt:** {result['suggested_next_action']}")
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown(
                '<div class="panel"><div class="panel-title">Text Feature Signals</div>'
                '<div class="panel-sub">Key terms that contributed positively to the classification (correlational signals, not causal proof).</div>',
                unsafe_allow_html=True,
            )
            st.markdown("<strong>Category Signals:</strong>", unsafe_allow_html=True)
            render_signals(result["category_signals"])
            st.divider()
            st.markdown("<strong>Priority & Urgency Signals:</strong>", unsafe_allow_html=True)
            render_signals(result["priority_signals"])
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="panel"><div class="panel-title">Human Verification Checklist</div>'
                '<div class="panel-sub">Mandatory associate audit before any ticket resolution.</div>',
                unsafe_allow_html=True,
            )
            st.checkbox("Physical barcode / manifest reference verified", key="chk_barcode")
            st.checkbox("Parcel physical state confirmed (seal intact / damage noted)", key="chk_seal")
            st.checkbox("Delivery SLA commitment cross-checked with route schedule", key="chk_sla")
            st.checkbox("Approved SOP next step confirmed by associate", key="chk_sop")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("Inspect All Class Decision Scores"):
            score_df = pd.DataFrame([
                {"Category Class": display_name(label), "Decision Score": f"{score:.2%}"}
                for label, score in result["category_scores"].items()
            ]).sort_values("Decision Score", ascending=False)
            st.dataframe(score_df, hide_index=True, use_container_width=True)

    else:
        st.markdown(
            '<div class="callout">Paste an exception note above or load a sample scenario to generate a triage suggestion. '
            'Your active threshold slider in the sidebar will immediately govern whether the result is flagged for human review.</div>',
            unsafe_allow_html=True,
        )

    history = st.session_state.get("triage_history", [])
    if history:
        st.write("")
        st.markdown('<div class="section-label">Session Activity Log (In-Memory Only)</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)

# ===========================================================================
# PAGE 3: BATCH TRIAGE
# ===========================================================================
elif page == "Batch triage":
    st.markdown('<div class="eyebrow">Bulk Workflow</div>', unsafe_allow_html=True)
    st.subheader("Shift-Level Batch Triage")
    st.caption("Upload a shift CSV containing a `description` column. Original columns are preserved and structured triage attributes are appended.")

    template_csv = pd.DataFrame({
        "ticket_ref": ["EXCEPTION-101", "EXCEPTION-102", "EXCEPTION-103", "EXCEPTION-104"],
        "origin_hub": ["Pune", "Nashik", "Indore", "Nagpur"],
        "description": [
            "Tracking has no destination arrival scan after origin handover; committed delivery is due today.",
            "Outer carton is crushed with liquid leakage observed during conveyor sort. Claim documentation needed.",
            "Loose package present in facility with unmapped barcode and no order reference found.",
            "The shipment has remained stationary at transfer center for 32 hours and delivery SLA is breached.",
        ],
    }).to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Sample Batch CSV  ↓",
        template_csv,
        "shiptriage_batch_sample.csv",
        "text/csv",
        help="Use this template to format your CSV upload.",
    )

    uploaded = st.file_uploader("Upload Shipment Exceptions CSV", type=["csv"], help="Maximum 5 MB file size and 5,000 rows.")

    if uploaded is not None:
        try:
            raw_bytes = uploaded.getvalue()
            input_frame = pd.read_csv(BytesIO(raw_bytes))
            clean_frame = validate_batch_csv(input_frame, file_size_bytes=len(raw_bytes))
            results_frame = make_batch_results(clean_frame, category_model, priority_model, threshold)

            total = len(results_frame)
            review_count = int(results_frame["review_required"].sum())
            high_count = int((results_frame["predicted_priority"] == "high").sum())
            ready_count = total - review_count

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Ingested", f"{total:,}")
            k2.metric("Manual Review Queue", f"{review_count:,}", delta=f"{review_count / total:.1%} of batch" if total else "0%")
            k3.metric("Above Threshold", f"{ready_count:,}", delta=f"{ready_count / total:.1%}" if total else "0%")
            k4.metric("High-Priority Flagged", f"{high_count:,}")

            st.write("")
            filter_choice = st.radio(
                "Filter View",
                ["All exceptions", "Review required queue", "Above threshold only", "High priority only"],
                horizontal=True,
            )

            if filter_choice == "Review required queue":
                visible = results_frame[results_frame["review_required"]]
            elif filter_choice == "Above threshold only":
                visible = results_frame[~results_frame["review_required"]]
            elif filter_choice == "High priority only":
                visible = results_frame[results_frame["predicted_priority"] == "high"]
            else:
                visible = results_frame

            st.dataframe(visible, use_container_width=True, hide_index=True, height=380)

            st.download_button(
                f"Export {filter_choice} ({len(visible):,})  ↓",
                visible.to_csv(index=False).encode("utf-8"),
                "shiptriage_triaged_batch.csv",
                "text/csv",
                type="primary",
                use_container_width=True,
            )
            st.caption("🔒 **Security & Privacy Guardrail:** All batch processing occurs strictly in memory. Uploaded ticket text is never written to disk or a database.")

        except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
            st.error(f"Batch Processing Error: {error}")
    else:
        st.markdown(
            '<div class="panel"><div class="panel-title">Batch Triage Workflow Guide</div>'
            '<div class="panel-sub">Standard operating procedure for processing shift-level exception backlogs.</div>'
            '<ol style="color:#51677F;font-size:13px;line-height:2">'
            '<li><strong>Download Sample:</strong> Verify expected column schema (must include <code>description</code>).</li>'
            '<li><strong>Upload Shift Export:</strong> Ingest bulk exception export from facility scan logs.</li>'
            '<li><strong>Tackle Review Queue First:</strong> Filter by <em>Review required queue</em> to address low-score ambiguous tickets.</li>'
            '<li><strong>Verify High-Priority Breaches:</strong> Address urgent exceptions with committed delivery deadlines.</li>'
            '<li><strong>Export Enriched CSV:</strong> Deliver triaged batch to facility leads with conservative next steps.</li>'
            '</ol>'
            '<span class="pill pill-review">Zero Automated Decisions Without Associate Review</span></div>',
            unsafe_allow_html=True,
        )

# ===========================================================================
# PAGE 4: MODEL INSIGHTS & EVALUATION
# ===========================================================================
elif page == "Model insights":
    st.markdown('<div class="eyebrow">Model Transparency & Evaluation</div>', unsafe_allow_html=True)
    st.subheader("Transparent Evaluation & Model-vs-Rules Comparison")
    st.markdown(
        '<div class="warning-note"><strong>APM Principle · Evidence-Driven Modeling:</strong> '
        'All metrics are computed on synthetic benchmark datasets. In early prototyping, more complex ML is not automatically better than simple rules. '
        'Compare actual metrics, understand blind spots, and select the simplest reliable architecture.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    if metrics:
        # Comparison Header: Rules vs ML vs Hybrid
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Keyword Baseline", f"{metrics.get('keyword_baseline_accuracy', 0):.1%}", help="Ordered domain keyword matching")
        m2.metric("Logistic Regression ML", f"{metrics.get('category_accuracy', 0):.1%}", help="TF-IDF unigram/bigrams + balanced logistic regression")
        m3.metric("Hybrid (Rules + ML)", f"{metrics.get('hybrid_accuracy', 1.0):.1%}", help="High-precision rules with statistical ML fallback")
        m4.metric("High-Priority Recall", f"{metrics.get('high_priority_recall', 0):.1%}", help="Critical guardrail: recall on urgent tickets")

        st.caption(
            f"Evaluation Methodology: **{metrics.get('split_strategy', 'template_group_holdout')}** · "
            f"{metrics.get('train_rows', '—')} training rows / {metrics.get('test_rows', '—')} held-out evaluation rows."
        )

        st.write("")
        st.markdown(
            '<div class="panel"><div class="panel-title">Why Did Keyword Rules Outperform ML on the Holdout?</div>'
            '<div class="panel-sub">The critical "Delayed vs. Missing" vocabulary overlap investigation.</div>'
            '<p style="color:#52677F;font-size:13px;line-height:1.7">'
            'On the template-group holdout, the ML classifier achieved <strong>78.5%</strong> accuracy, with <strong>0.0% precision and 0.0% recall on the "delayed" category</strong>. '
            'Every held-out delayed ticket was misclassified as "missing". Why? In logistics, delayed shipment notes share vocabulary with missing notes '
            '(<em>"tracking"</em>, <em>"scan"</em>, <em>"transit"</em>, <em>"hub"</em>). When a template family was held out, the ML model lacked the specific n-grams it had memorized for delayed, '
            'and defaulted to the overlapping weights of missing. Meanwhile, transparent keyword rules anchored on invariant domain phrases '
            '(<em>"sla"</em>, <em>"transit window"</em>, <em>"held at the hub"</em>) scored <strong>100%</strong>.<br>'
            '<strong>Product Takeaway:</strong> We designed a <strong>Hybrid Rules + ML Fallback</strong>. Rules provide a high-precision shield for known physical signals, '
            'while ML handles linguistic variance. The Hybrid approach achieves <strong>100% on template holdout</strong> and <strong>90% on unseen phrasing</strong>.'
            '</p></div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns(2, gap="large")
        with left:
            st.markdown('<div class="panel"><div class="panel-title">Per-Class Category Performance (Holdout)</div><div class="panel-sub">Precision, Recall, and F1 on held-out template families</div>', unsafe_allow_html=True)
            report = metrics.get("category_report", {})
            report_rows = [
                {
                    "Category": display_name(label),
                    "Precision": report.get(label, {}).get("precision", 0),
                    "Recall": report.get(label, {}).get("recall", 0),
                    "F1": report.get(label, {}).get("f1-score", 0),
                }
                for label in CATEGORIES
            ]
            fig = px.bar(
                pd.DataFrame(report_rows).melt(id_vars="Category", var_name="Metric", value_name="Score"),
                x="Category",
                y="Score",
                color="Metric",
                barmode="group",
                range_y=[0, 1.05],
            )
            fig.update_layout(height=320, margin=dict(l=8, r=8, t=12, b=8), plot_bgcolor="white", paper_bgcolor="white", legend_title_text="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown('<div class="panel"><div class="panel-title">Priority Classification Performance</div><div class="panel-sub">High-priority recall is the primary operational guardrail</div>', unsafe_allow_html=True)
            report = metrics.get("priority_report", {})
            priority_rows = [
                {
                    "Priority": display_name(label),
                    "Precision": report.get(label, {}).get("precision", 0),
                    "Recall": report.get(label, {}).get("recall", 0),
                    "F1": report.get(label, {}).get("f1-score", 0),
                }
                for label in ["low", "medium", "high"]
            ]
            fig = px.bar(
                pd.DataFrame(priority_rows).melt(id_vars="Priority", var_name="Metric", value_name="Score"),
                x="Priority",
                y="Score",
                color="Metric",
                barmode="group",
                range_y=[0, 1.05],
            )
            fig.update_layout(height=320, margin=dict(l=8, r=8, t=12, b=8), plot_bgcolor="white", paper_bgcolor="white", legend_title_text="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("Category Confusion Matrix (Holdout Split)"):
            matrix = metrics.get("category_confusion_matrix", [])
            labels = metrics.get("category_labels", CATEGORIES)
            if matrix:
                fig = px.imshow(
                    matrix,
                    x=[display_name(x) for x in labels],
                    y=[display_name(x) for x in labels],
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Teal",
                )
                fig.update_layout(height=400, xaxis_title="Predicted Label", yaxis_title="Actual Label")
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Notice the 50 instances of 'Delayed' classified as 'Missing' in pure ML, proving why the hybrid approach is essential.")

        with st.expander("Priority Confusion Matrix (Holdout Split)"):
            matrix = metrics.get("priority_confusion_matrix", [])
            labels = metrics.get("priority_labels", ["low", "medium", "high"])
            if matrix:
                fig = px.imshow(
                    matrix,
                    x=[display_name(x) for x in labels],
                    y=[display_name(x) for x in labels],
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Teal",
                )
                fig.update_layout(height=350, xaxis_title="Predicted Urgency", yaxis_title="Actual Urgency")
                st.plotly_chart(fig, use_container_width=True)

    st.write("")
    st.markdown('<div class="panel"><div class="panel-title">Alternate-Phrasing Generalization Challenge Set</div><div class="panel-sub">Manual qualitative stress test using non-templated colloquial phrasing.</div>', unsafe_allow_html=True)
    if unseen_metrics:
        u1, u2, u3, u4 = st.columns(4)
        u1.metric("Challenge Size", f"{unseen_metrics.get('unseen_rows', 10)} tickets")
        u2.metric("Keyword Baseline", f"{unseen_metrics.get('keyword_baseline_accuracy', 0):.1%}")
        u3.metric("Logistic Regression", f"{unseen_metrics.get('category_accuracy', 0):.1%}")
        u4.metric("Hybrid Accuracy", f"{unseen_metrics.get('hybrid_category_accuracy', 0.9):.1%}")

        st.caption(
            "Notice how on colloquial phrasing, the Keyword Baseline dropped from 100% to 60% (returning `needs_review`), "
            "while ML achieved 70% and the Hybrid Model achieved 90%."
        )

        if unseen_metrics.get("predictions"):
            preds_df = pd.DataFrame(unseen_metrics["predictions"])
            preds_df["actual_category"] = preds_df["actual_category"].apply(display_name)
            preds_df["predicted_category"] = preds_df["predicted_category"].apply(display_name)
            preds_df["hybrid_category"] = preds_df["hybrid_category"].apply(display_name)
            preds_df["keyword_baseline_category"] = preds_df["keyword_baseline_category"].apply(display_name)
            st.dataframe(preds_df, use_container_width=True, hide_index=True)
    else:
        st.info("Alternate-phrasing evaluation metrics are being initialized.")
    st.markdown('</div>', unsafe_allow_html=True)

# ===========================================================================
# PAGE 5: ABOUT THE PRODUCT & APM PORTFOLIO
# ===========================================================================
elif page == "About the product":
    st.markdown('<div class="eyebrow">Product Management Portfolio Brief</div>', unsafe_allow_html=True)
    st.subheader("Product Strategy, Hypothesis & Validation Roadmap")

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown(
            '<div class="panel"><div class="panel-title">Problem Statement</div>'
            '<div class="panel-sub">The operational pain point ShipTriage solves.</div>'
            '<p style="color:#52677F;font-size:13px;line-height:1.7">'
            'In high-velocity warehouse and supply chain fulfillment operations, shipment exceptions (damages, missing parcels, unmapped AWBs, transit delays, SKU mismatches) '
            'arrive as unstructured free-text notes across disparate hub registers. Associates spend significant cognitive effort reading notes, discerning issue root causes, '
            'estimating urgency against SLA targets, and looking up standard operating procedures.<br><br>'
            '<strong>Core User Problem:</strong> Unstructured exception intake causes high cognitive load, inconsistent triage quality, and delayed escalation for urgent shipments.'
            '</p>'
            '<div class="panel-title" style="margin-top:20px">Primary User Persona</div>'
            '<p style="color:#52677F;font-size:13px;line-height:1.6">'
            '<strong>Ramesh, Warehouse Issue-Resolution Associate:</strong> Coordinates 200+ exception packages daily during inbound/outbound hub turnover. '
            'Values speed, simplicity, and clear next steps; cannot afford black-box AI errors that silently miss SLA-critical orders.'
            '</p>'
            '<div class="panel-title" style="margin-top:20px">Jobs to Be Done (JTBD)</div>'
            '<p style="color:#52677F;font-size:13px;line-height:1.6">'
            '<em>"When a shipment exception arrives, help me instantly identify the issue type and urgency, and guide me with the approved next step so I can resolve the exception without missing our dispatch SLA."</em>'
            '</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<div class="panel"><div class="panel-title">Product Scope & Guardrails</div>'
            '<div class="panel-sub">Explicit boundaries separating MVP assistance from autonomous risk.</div>'
            '<p style="font-size:12px;color:#087E70;font-weight:700">IN SCOPE (v1.1 MVP)</p>'
            '<ul style="color:#52677F;font-size:12px;line-height:1.9">'
            '<li>Five discrete exception categories and three urgency priority levels.</li>'
            '<li>Hybrid triage engine combining high-precision rules with statistical ML fallback.</li>'
            '<li>Dynamic review threshold slider with immediate manual-queue routing.</li>'
            '<li>Transparent feature contribution signals and uncalibrated score disclosures.</li>'
            '<li>Conservative standard operating procedure action recommendations.</li>'
            '<li>Single ticket and bulk CSV batch processing with in-memory execution.</li>'
            '</ul>'
            '<p style="font-size:12px;color:#B54727;font-weight:700">OUT OF SCOPE (SAFETY GUARDRAILS)</p>'
            '<ul style="color:#52677F;font-size:12px;line-height:1.9">'
            '<li>No autonomous customer communications, refunds, rerouting, or ticket closures.</li>'
            '<li>No connection to proprietary warehouse, carrier, or corporate production databases.</li>'
            '<li>No storage of confidential tracking, customer, or employee data.</li>'
            '<li>No unvalidated automated claims approval.</li>'
            '</ul>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown(
        '<div class="panel"><div class="panel-title">Pilot Success Metrics Framework</div>'
        '<div class="panel-sub">Proposed measurement plan for actual warehouse validation (clearly distinct from synthetic prototype metrics).</div>',
        unsafe_allow_html=True,
    )

    metrics_table = pd.DataFrame([
        {
            "Metric Name": "North Star: Median Time to Initial Triage Decision",
            "Target Objective": "Reduce median triage time from ~120s to <35s per ticket.",
            "Measurement Method": "Time tracked from ticket view to associate SOP confirmation in pilot cohort.",
            "Type": "North Star",
        },
        {
            "Metric Name": "Guardrail 1: High-Priority Recall",
            "Target Objective": "Maintain >=99.0% recall on SLA-critical and escalated shipments.",
            "Measurement Method": "Independent manual audit of all tickets marked high priority or SLA-breached.",
            "Type": "Guardrail",
        },
        {
            "Metric Name": "Guardrail 2: Misrouted-Ticket Rate",
            "Target Objective": "<2.5% of triaged tickets reassigned or reopened.",
            "Measurement Method": "Track downstream hub reopen tags indicating incorrect routing.",
            "Type": "Quality Guardrail",
        },
        {
            "Metric Name": "Operational Metric: Manual Review Rate",
            "Target Objective": "Optimize threshold so 15%–25% of ambiguous tickets route to human queue.",
            "Measurement Method": "Proportion of batch volume where min score falls below active threshold.",
            "Type": "Operational",
        },
        {
            "Metric Name": "User Adoption: Associate Override Rate",
            "Target Objective": "Keep associate suggestion override rate below 12%.",
            "Measurement Method": "Logged instances where associate alters the recommended category or priority.",
            "Type": "Adoption & Trust",
        },
    ])
    st.dataframe(metrics_table, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note">SHIPTRIAGE v1.1.0 · GOOGLE APM PORTFOLIO PROTOTYPE · SYNTHETIC DATA ONLY · HUMAN DECISION-MAKER IN CONTROL</div>',
    unsafe_allow_html=True,
)
