"""ShipTriage: human-in-the-loop shipment exception triage prototype."""

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
from shiptriage.modeling import load_models, predict_ticket, train_and_evaluate  # noqa: E402
from shiptriage.recommendations import recommend_next_action  # noqa: E402

st.set_page_config(
    page_title="ShipTriage | Exception Intelligence",
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
      .hero p { color:#C7D7E8; margin:8px 0 0; font-size:14px; max-width:760px; }
      .hero-tag { display:inline-block; padding:5px 10px; border-radius:99px; background:rgba(45,212,191,.13); color:#8CF1E1; font-size:10px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:12px; border:1px solid rgba(140,241,225,.18); }
      .section-label { color:#76869B; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.12em; margin:4px 0 9px; }
      .metric-card { background:#fff; border:1px solid var(--line); border-radius:15px; padding:17px 18px; min-height:108px; box-shadow:0 2px 8px rgba(21,45,75,.025); }
      .metric-label { color:#738196; font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
      .metric-value { color:#152A43; font:800 25px 'Manrope',sans-serif; margin-top:7px; letter-spacing:-.04em; }
      .metric-hint { color:#8492A5; font-size:11px; margin-top:3px; }
      .panel { background:#fff; border:1px solid var(--line); border-radius:17px; padding:20px; box-shadow:0 2px 8px rgba(21,45,75,.025); }
      .panel-title { color:#1B304A; font:700 15px 'Manrope',sans-serif; margin:0 0 4px; }
      .panel-sub { color:#8290A2; font-size:12px; margin-bottom:14px; }
      .pill { display:inline-block; border-radius:100px; padding:5px 10px; font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
      .pill-synthetic { background:#FFF5DB; color:#9A6700; border:1px solid #F4E2A7; }
      .pill-review { background:#FFF0EB; color:#B54727; border:1px solid #F7D2C5; }
      .pill-ready { background:#E8F8F4; color:#087E70; border:1px solid #BCEADF; }
      .result-card { background:#fff; border:1px solid var(--line); border-radius:17px; padding:20px; height:100%; }
      .result-value { color:#172D48; font:800 23px 'Manrope',sans-serif; margin:8px 0 3px; }
      .result-label { color:#7B8A9D; font-size:11px; text-transform:uppercase; font-weight:700; letter-spacing:.08em; }
      .signal { display:inline-block; padding:6px 9px; background:#EFF5FA; border:1px solid #DDE8F2; border-radius:8px; color:#36516D; font-size:11px; margin:3px 4px 3px 0; }
      .callout { background:#F0F7FF; border-left:3px solid #4F8DCE; padding:12px 14px; border-radius:0 10px 10px 0; color:#3F5873; font-size:12px; }
      .warning-note { background:#FFF8E9; border:1px solid #F4E4B9; border-radius:12px; padding:12px 14px; color:#775B1C; font-size:12px; }
      .footer-note { color:#91A0B2; font-size:10px; text-align:center; padding:20px 0 4px; }
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


@st.cache_resource(show_spinner="Preparing the ShipTriage models…")
def get_models():
    """Load model artifacts; rebuild them from included synthetic data if absent/incompatible."""
    try:
        return load_models()
    except Exception:
        if not DATASET_PATH.exists():
            raise FileNotFoundError("The synthetic dataset is missing. Restore data/synthetic_tickets.csv.")
        dataset = pd.read_csv(DATASET_PATH)
        train_and_evaluate(dataset)
        return load_models()


@st.cache_data(show_spinner=False)
def read_json(path_string: str) -> dict[str, Any]:
    path = Path(path_string)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


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
    return value.replace("_", " ").title()


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
        if not description:
            rows.append({
                "predicted_category": "needs_review",
                "predicted_priority": "unknown",
                "category_score": 0.0,
                "priority_score": 0.0,
                "review_required": True,
                "suggested_next_action": "Description is empty. Review the source ticket manually.",
            })
            continue
        result = triage_one(description, category_model, priority_model, threshold)
        rows.append({
            "predicted_category": result["category"],
            "predicted_priority": result["priority"],
            "category_score": round(result["category_confidence"], 4),
            "priority_score": round(result["priority_confidence"], 4),
            "review_required": result["review_required"],
            "suggested_next_action": result["suggested_next_action"],
        })
    prediction_frame = pd.DataFrame(rows)
    # Avoid duplicate output columns if a file is re-uploaded after prior processing.
    output = output.drop(columns=[c for c in prediction_frame.columns if c in output.columns], errors="ignore")
    return pd.concat([output.reset_index(drop=True), prediction_frame], axis=1)


def render_header() -> None:
    st.markdown(
        '<div class="hero"><div class="hero-tag">Operations intelligence · Product prototype</div>'
        '<h1>Make every exception easier to act on.</h1>'
        '<p>Turn free-text shipment issues into a structured triage suggestion, a clear urgency signal, and a safe next step for the human operator.</p></div>',
        unsafe_allow_html=True,
    )


# --- Models and navigation -------------------------------------------------
try:
    category_model, priority_model = get_models()
except Exception as error:
    st.error("ShipTriage could not prepare its ML models.")
    st.code("python scripts/generate_data.py\npython scripts/train_model.py")
    st.exception(error)
    st.stop()

metrics = read_json(str(METRICS_PATH))
unseen_metrics = read_json(str(UNSEEN_METRICS_PATH))
data = load_synthetic_data()

with st.sidebar:
    st.markdown(
        '<div class="brand-lockup"><div class="brand-icon">📦</div><div><div class="brand-name">ShipTriage</div><div class="brand-sub">Exception intelligence</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label" style="color:#9DB1C9">Workspace</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["Overview", "Single triage", "Batch triage", "Model insights", "About the product"],
        label_visibility="collapsed",
        key="sidebar_page",
    )
    st.divider()
    threshold = st.slider(
        "Manual-review threshold",
        min_value=0.40,
        max_value=0.90,
        value=CONFIDENCE_THRESHOLD,
        step=0.05,
        help="A ticket is flagged when either model's top-class score falls below this threshold. Scores are not calibrated probabilities.",
    )
    st.divider()
    st.markdown('<span class="pill pill-synthetic">Synthetic demo data</span>', unsafe_allow_html=True)
    st.caption("No carrier, marketplace, customer, or warehouse system is connected.")
    st.caption("All recommendations require human verification.")

render_header()

if page == "Overview":
    st.markdown('<div class="eyebrow">Workspace overview</div>', unsafe_allow_html=True)
    st.subheader("Your triage workspace")
    total_rows = len(data)
    categories_count = data["category"].nunique() if not data.empty and "category" in data else len(CATEGORIES)
    train_rows = metrics.get("train_rows", "—")
    score = metrics.get("category_accuracy")
    score_label = f"{score:.1%}" if isinstance(score, (int, float)) else "—"
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1: metric_card("Synthetic tickets", f"{total_rows:,}", "Generated examples in local dataset")
    with c2: metric_card("Exception categories", str(categories_count), "Five supported exception types")
    with c3: metric_card("Training examples", f"{train_rows:,}" if isinstance(train_rows, int) else "—", "Template-aware training split")
    with c4: metric_card("Holdout category score", score_label, "Synthetic holdout only")

    st.write("")
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.markdown('<div class="panel"><div class="panel-title">Exception mix</div><div class="panel-sub">Distribution of fictional training examples</div>', unsafe_allow_html=True)
        if not data.empty:
            category_mix = data["category"].value_counts().rename_axis("Exception").reset_index(name="Tickets")
            fig = px.bar(category_mix, x="Exception", y="Tickets", color="Exception", text="Tickets")
            fig.update_layout(height=300, showlegend=False, margin=dict(l=8, r=8, t=12, b=8), plot_bgcolor="white", paper_bgcolor="white", font_color="#52647A")
            fig.update_traces(marker_line_width=0, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Synthetic dataset is not available.")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">How ShipTriage works</div><div class="panel-sub">A human-in-the-loop workflow</div>', unsafe_allow_html=True)
        steps = [
            ("01", "Read the ticket", "Start with free-text shipment context."),
            ("02", "Predict and score", "Estimate exception type and urgency."),
            ("03", "Review uncertainty", "Flag low-scoring predictions for a person."),
            ("04", "Choose the next step", "Use the suggestion as decision support, not an automatic action."),
        ]
        for number, title, subtitle in steps:
            st.markdown(f'<div style="display:flex;gap:12px;padding:9px 0;border-bottom:1px solid #EEF1F5"><div style="background:#E8F7F4;color:#0B8B7C;border-radius:9px;padding:8px 10px;font-weight:800;height:fit-content">{number}</div><div><div style="font-weight:700;color:#253B55;font-size:13px">{title}</div><div style="font-size:11px;color:#8492A5;margin-top:3px">{subtitle}</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-top:14px"><span class="pill pill-ready">Human review stays in control</span></div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="panel"><div class="panel-title">Try a sample exception</div><div class="panel-sub">Choose a workflow to explore the product prototype.</div>', unsafe_allow_html=True)
    sample_cols = st.columns(3)
    samples = [
        ("Missing shipment", "A dispatch scan exists, but the parcel is not present in the destination receiving area. The delivery promise is due today."),
        ("Damaged parcel", "The outer carton is crushed and has a broken seal. The product may be damaged and evidence needs to be recorded."),
        ("Delayed shipment", "The parcel has remained at the transfer hub with no onward movement. The delivery SLA is at risk."),
    ]
    def open_sample_ticket(sample_text: str) -> None:
        st.session_state["prefill_ticket"] = sample_text
        st.session_state["sidebar_page"] = "Single triage"

    for col, (name, sample_text) in zip(sample_cols, samples):
        with col:
            st.button(
                f"Analyse: {name}",
                use_container_width=True,
                on_click=open_sample_ticket,
                args=(sample_text,),
            )
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Single triage":
    st.markdown('<div class="eyebrow">Ticket workspace</div>', unsafe_allow_html=True)
    st.subheader("Analyse a shipment exception")
    st.caption("Paste an exception note or load a sample. The model returns a suggestion; an associate remains responsible for the decision.")
    demo_examples = {
        "Missing shipment": "Tracking has no arrival scan after dispatch from Pune. The parcel is not present in the destination cage and delivery is due today.",
        "Damaged parcel": "The outer carton is torn and the product inside appears cracked. Please record damage evidence before further movement.",
        "Orphan shipment": "A loose parcel is present at the destination hub, but no matching order or manifest reference exists in the system.",
        "Delayed shipment": "The parcel has remained at the transfer centre with no onward movement and the delivery SLA is at risk.",
        "Wrong item": "The SKU inside the parcel does not match the customer's confirmed order; the wrong product may have been packed.",
    }
    choice = st.selectbox("Load a sample ticket", ["Write my own"] + list(demo_examples.keys()))
    prefill = st.session_state.pop("prefill_ticket", "")
    default_description = prefill or ("" if choice == "Write my own" else demo_examples[choice])
    with st.form("single_triage_form", clear_on_submit=False):
        description = st.text_area(
            "Ticket description",
            value=default_description,
            height=150,
            max_chars=5000,
            placeholder="Example: Shipment has no destination scan after origin handover…",
            help="Do not paste customer names, phone numbers, addresses, live tracking IDs, or confidential operational data.",
        )
        submitted = st.form_submit_button("Analyse exception  →", type="primary", use_container_width=True)
    if submitted:
        try:
            result = triage_one(description, category_model, priority_model, threshold)
            st.session_state["last_prediction"] = {"description": description, **result}
            history = st.session_state.setdefault("triage_history", [])
            history.insert(0, {"description": description[:160], "category": result["category"], "priority": result["priority"], "review_required": result["review_required"]})
            st.session_state["triage_history"] = history[:10]
        except ValueError as error:
            st.error(str(error))
    result = st.session_state.get("last_prediction")
    if result:
        st.write("")
        if result["review_required"]:
            st.warning("Human review recommended — at least one model score is below the selected threshold.")
        else:
            st.success("Triage suggestion generated. Verify the details before acting.")
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.markdown(f'<div class="result-card"><div class="result-label">Exception category</div><div class="result-value">{display_name(result["category"])}</div><div class="metric-hint">Predicted issue type</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="result-card"><div class="result-label">Suggested priority</div><div class="result-value">{display_name(result["priority"])}</div><div class="metric-hint">Predicted urgency level</div></div>', unsafe_allow_html=True)
        with c3:
            status_class = "pill-review" if result["review_required"] else "pill-ready"
            status_text = "Review required" if result["review_required"] else "Above threshold"
            st.markdown(f'<div class="result-card"><div class="result-label">Triage status</div><div style="margin-top:14px"><span class="pill {status_class}">{status_text}</span></div><div class="metric-hint" style="margin-top:14px">Threshold: {threshold:.0%}</div></div>', unsafe_allow_html=True)

        st.write("")
        left, right = st.columns([1, 1], gap="large")
        with left:
            st.markdown('<div class="panel"><div class="panel-title">Model score indicators</div><div class="panel-sub">Top-class scores; not calibrated probabilities.</div>', unsafe_allow_html=True)
            st.write(f"**Category score · {result['category_confidence']:.1%}**")
            st.progress(result["category_confidence"])
            st.write(f"**Priority score · {result['priority_confidence']:.1%}**")
            st.progress(result["priority_confidence"])
            st.caption("A high score does not guarantee a correct prediction. Use the ticket context and local operating procedure.")
            st.markdown('</div>', unsafe_allow_html=True)
            st.write("")
            st.markdown('<div class="panel"><div class="panel-title">Suggested next action</div><div class="panel-sub">A conservative, category-based prompt for the associate.</div>', unsafe_allow_html=True)
            st.info(result["suggested_next_action"])
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="panel"><div class="panel-title">Text signals behind the category</div><div class="panel-sub">Terms that contributed positively to the predicted class. These are model signals, not causal explanations.</div>', unsafe_allow_html=True)
            render_signals(result["category_signals"])
            st.divider()
            st.markdown('<div class="panel-title">Text signals behind the priority</div><div class="panel-sub">Review the urgency language in the original ticket.</div>', unsafe_allow_html=True)
            render_signals(result["priority_signals"])
            st.markdown('</div>', unsafe_allow_html=True)
        with st.expander("View class score breakdown"):
            score_df = pd.DataFrame([
                {"Class": label, "Score": score}
                for label, score in result["category_scores"].items()
            ]).sort_values("Score", ascending=False)
            st.dataframe(score_df, hide_index=True, use_container_width=True)
    else:
        st.markdown('<div class="callout">Your result will appear here after you analyse a ticket. For best results, include the shipment status, issue observed, and time/SLA context—without personal or confidential data.</div>', unsafe_allow_html=True)

    history = st.session_state.get("triage_history", [])
    if history:
        st.write("")
        st.markdown('<div class="section-label">Recent session activity · stored only in this browser session</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)

elif page == "Batch triage":
    st.markdown('<div class="eyebrow">Bulk workflow</div>', unsafe_allow_html=True)
    st.subheader("Triage multiple exceptions")
    st.caption("Upload a CSV with a `description` column. The original columns are retained and prediction fields are appended.")
    template_csv = pd.DataFrame({
        "ticket_ref": ["DEMO-001", "DEMO-002", "DEMO-003"],
        "description": [
            "The parcel has no destination arrival scan after handover; delivery is due today.",
            "The outer carton is crushed and the item appears damaged during inbound inspection.",
            "The parcel is present at the hub but no matching order or manifest reference exists.",
        ],
    }).to_csv(index=False).encode("utf-8")
    st.download_button("Download sample CSV", template_csv, "shiptriage_upload_template.csv", "text/csv")
    uploaded = st.file_uploader("Choose a ticket CSV", type=["csv"], help="Maximum 5 MB and 5,000 rows.")
    if uploaded is not None:
        try:
            raw_bytes = uploaded.getvalue()
            input_frame = pd.read_csv(BytesIO(raw_bytes))
            clean_frame = validate_batch_csv(input_frame, file_size_bytes=len(raw_bytes))
            results_frame = make_batch_results(clean_frame, category_model, priority_model, threshold)
            total = len(results_frame)
            review_count = int(results_frame["review_required"].sum())
            high_count = int((results_frame["predicted_priority"] == "high").sum())
            k1, k2, k3 = st.columns(3)
            k1.metric("Tickets processed", f"{total:,}")
            k2.metric("Human review queue", f"{review_count:,}", delta=f"{review_count / total:.0%} of batch" if total else None)
            k3.metric("Predicted high priority", f"{high_count:,}")
            st.write("")
            filter_choice = st.radio("Show", ["All tickets", "Review required", "Above threshold"], horizontal=True)
            if filter_choice == "Review required":
                visible = results_frame[results_frame["review_required"]]
            elif filter_choice == "Above threshold":
                visible = results_frame[~results_frame["review_required"]]
            else:
                visible = results_frame
            st.dataframe(visible, use_container_width=True, hide_index=True, height=380)
            st.download_button(
                "Download triage results  ↓",
                results_frame.to_csv(index=False).encode("utf-8"),
                "shiptriage_results.csv",
                "text/csv",
                type="primary",
                use_container_width=True,
            )
            st.caption("Batch results are generated in memory. Uploaded ticket contents are not written to a database or persistent file by this app.")
        except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
            st.error(f"Could not process this CSV: {error}")
    else:
        st.markdown('<div class="panel"><div class="panel-title">Batch workflow</div><div class="panel-sub">A simple, repeatable flow for a shift-level queue.</div><ol style="color:#51677F;font-size:13px;line-height:2"><li>Download the sample CSV to check the required format.</li><li>Prepare a CSV with one shipment exception per row.</li><li>Upload the file and inspect low-score tickets first.</li><li>Download results and let the responsible associate verify every action.</li></ol><span class="pill pill-review">No automatic ticket updates</span></div>', unsafe_allow_html=True)

elif page == "Model insights":
    st.markdown('<div class="eyebrow">Model transparency</div>', unsafe_allow_html=True)
    st.subheader("Understand what the model can—and cannot—tell you")
    st.markdown('<div class="warning-note"><strong>Important:</strong> All model scores shown here come from generated synthetic examples. They are not evidence of production accuracy, savings, or operational impact.</div>', unsafe_allow_html=True)
    st.write("")
    if metrics:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Category accuracy", f"{metrics.get('category_accuracy', 0):.1%}")
        m2.metric("Priority accuracy", f"{metrics.get('priority_accuracy', 0):.1%}")
        m3.metric("High-priority recall", f"{metrics.get('high_priority_recall', 0):.1%}")
        m4.metric("Keyword baseline", f"{metrics.get('keyword_baseline_accuracy', 0):.1%}")
        st.caption(f"Evaluation split: {metrics.get('split_strategy', 'not recorded')} · {metrics.get('train_rows', '—')} train / {metrics.get('test_rows', '—')} holdout rows.")
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown('<div class="panel"><div class="panel-title">Category-level performance</div><div class="panel-sub">Precision, recall and F1 on the synthetic holdout.</div>', unsafe_allow_html=True)
            report = metrics.get("category_report", {})
            report_rows = [{"Category": label.title(), "Precision": report.get(label, {}).get("precision", 0), "Recall": report.get(label, {}).get("recall", 0), "F1": report.get(label, {}).get("f1-score", 0)} for label in CATEGORIES]
            fig = px.bar(pd.DataFrame(report_rows).melt(id_vars="Category", var_name="Metric", value_name="Score"), x="Category", y="Score", color="Metric", barmode="group", range_y=[0, 1])
            fig.update_layout(height=320, margin=dict(l=8,r=8,t=12,b=8), plot_bgcolor="white", paper_bgcolor="white", legend_title_text="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="panel"><div class="panel-title">Priority-level performance</div><div class="panel-sub">Recall is especially important for urgent exceptions.</div>', unsafe_allow_html=True)
            report = metrics.get("priority_report", {})
            priority_rows = [{"Priority": label.title(), "Precision": report.get(label, {}).get("precision", 0), "Recall": report.get(label, {}).get("recall", 0), "F1": report.get(label, {}).get("f1-score", 0)} for label in ["low", "medium", "high"]]
            fig = px.bar(pd.DataFrame(priority_rows).melt(id_vars="Priority", var_name="Metric", value_name="Score"), x="Priority", y="Score", color="Metric", barmode="group", range_y=[0, 1])
            fig.update_layout(height=320, margin=dict(l=8,r=8,t=12,b=8), plot_bgcolor="white", paper_bgcolor="white", legend_title_text="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)
        with st.expander("View category confusion matrix"):
            matrix = metrics.get("category_confusion_matrix", [])
            labels = metrics.get("category_labels", CATEGORIES)
            if matrix:
                fig = px.imshow(matrix, x=[display_name(x) for x in labels], y=[display_name(x) for x in labels], text_auto=True, aspect="auto", color_continuous_scale="Teal")
                fig.update_layout(height=420, xaxis_title="Predicted", yaxis_title="Actual")
                st.plotly_chart(fig, use_container_width=True)
        with st.expander("View priority confusion matrix"):
            matrix = metrics.get("priority_confusion_matrix", [])
            labels = metrics.get("priority_labels", ["low", "medium", "high"])
            if matrix:
                fig = px.imshow(matrix, x=[display_name(x) for x in labels], y=[display_name(x) for x in labels], text_auto=True, aspect="auto", color_continuous_scale="Teal")
                fig.update_layout(height=350, xaxis_title="Predicted", yaxis_title="Actual")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Evaluation metrics are unavailable. Run `python scripts/train_model.py`.")

    st.write("")
    st.markdown('<div class="panel"><div class="panel-title">Alternate-phrasing challenge set</div><div class="panel-sub">A small, manually authored set used to expose sensitivity to wording.</div>', unsafe_allow_html=True)
    if unseen_metrics:
        a, b, c = st.columns(3)
        a.metric("Challenge examples", unseen_metrics.get("unseen_rows", "—"))
        a.metric("Category accuracy", f"{unseen_metrics.get('category_accuracy', 0):.1%}")
        b.metric("Priority accuracy", f"{unseen_metrics.get('priority_accuracy', 0):.1%}")
        b.metric("High-priority recall", f"{unseen_metrics.get('high_priority_recall', 0):.1%}")
        c.metric("Keyword baseline", f"{unseen_metrics.get('keyword_baseline_accuracy', 0):.1%}")
        st.caption(unseen_metrics.get("evaluation_note", "Exploratory challenge set; interpret cautiously."))
        if unseen_metrics.get("predictions"):
            st.dataframe(pd.DataFrame(unseen_metrics["predictions"]), use_container_width=True, hide_index=True)
    else:
        st.info("Run `python scripts/evaluate_model.py` to generate the alternate-phrasing report.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "About the product":
    st.markdown('<div class="eyebrow">Product brief</div>', unsafe_allow_html=True)
    st.subheader("A decision-support layer for shipment exceptions")
    left, right = st.columns([1.05, .95], gap="large")
    with left:
        st.markdown('<div class="panel"><div class="panel-title">Problem</div><div class="panel-sub">The user problem ShipTriage is designed to explore.</div><p style="color:#52677F;font-size:13px;line-height:1.7">Issue-resolution associates may need to read free-text shipment exception notes, work out what went wrong, decide how urgent it is, and choose a safe next step. ShipTriage explores whether lightweight ML can make the first pass more structured and consistent.</p><div class="panel-title" style="margin-top:20px">Primary user</div><p style="color:#52677F;font-size:13px">A warehouse issue-resolution associate coordinating inbound and outbound shipment exceptions.</p><div class="panel-title" style="margin-top:20px">Product promise</div><p style="color:#52677F;font-size:13px">Faster understanding and clearer prioritization—with the associate retaining control.</p></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">Scope and guardrails</div><div class="panel-sub">What this prototype does and does not do.</div><p style="font-size:12px;color:#087E70;font-weight:700">IN SCOPE</p><ul style="color:#52677F;font-size:12px;line-height:1.9"><li>Five exception categories and three priority levels.</li><li>Single-ticket and CSV batch triage.</li><li>Score threshold and manual review.</li><li>Suggested next step and model transparency.</li></ul><p style="font-size:12px;color:#B54727;font-weight:700">OUT OF SCOPE</p><ul style="color:#52677F;font-size:12px;line-height:1.9"><li>No live carrier or warehouse integration.</li><li>No refunds, rerouting, closure, or customer communication.</li><li>No real company or customer data.</li><li>No claim of production readiness or measured ROI.</li></ul></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="panel"><div class="panel-title">Product success metrics to validate in a pilot</div><div class="panel-sub">These are proposed measures, not measured outcomes.</div>', unsafe_allow_html=True)
    success_metrics = pd.DataFrame([
        {"Metric": "Median time to initial triage", "Why it matters": "Measures time to reach a first decision."},
        {"Metric": "Correct categorization rate", "Why it matters": "Measures routing quality under associate audit."},
        {"Metric": "High-priority recall", "Why it matters": "Tracks urgent exceptions that are not missed."},
        {"Metric": "Manual-review rate", "Why it matters": "Shows how often human judgement is required."},
        {"Metric": "Associate override rate", "Why it matters": "Reveals disagreement and model blind spots."},
    ])
    st.dataframe(success_metrics, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="footer-note">SHIPTRIAGE · PORTFOLIO PROTOTYPE · SYNTHETIC DATA ONLY · HUMAN DECISION-MAKER IN CONTROL</div>', unsafe_allow_html=True)
