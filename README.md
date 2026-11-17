# ShipTriage v1.1.0

**AI-Assisted Shipment Exception Triage · Google APM Portfolio Prototype · Synthetic Data Only**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit 1.40+](https://img.shields.io/badge/streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4%2B-F7931E.svg)](https://scikit-learn.org/)
[![Tests Passing](https://img.shields.io/badge/tests-17%20passed-brightgreen.svg)](tests/)
[![Live Application](https://img.shields.io/badge/demo-live%20app-success.svg)](https://shiptriage-dtvzbqvymfb9mfzetgx3nq.streamlit.app/)

ShipTriage transforms unstructured, free-text shipment exception notes into structured issue categories, urgency priorities, and conservative next-step prompts. Designed as a Google Associate Product Manager (APM) portfolio prototype, it demonstrates product discovery, human-in-the-loop AI safety, evidence-based machine learning trade-offs, and operational systems engineering.

> **Important Disclosure:** ShipTriage is an educational portfolio prototype. It is not connected to Flipkart, Ekart, any carrier, or any production warehouse system. All bundled records are fictional and synthetic. Model decision scores are uncalibrated and are not evidence of production performance. Do not input real customer, employee, tracking, or confidential operational data.

---

## Live Application & Code
- **Live Demo:** [https://shiptriage-dtvzbqvymfb9mfzetgx3nq.streamlit.app/](https://shiptriage-dtvzbqvymfb9mfzetgx3nq.streamlit.app/)
- **GitHub Repository:** [https://github.com/Rathore-Sahab/shiptriage](https://github.com/Rathore-Sahab/shiptriage)

---

## Product Preview

- **Overview:** Executive operations snapshot, synthetic exception mix, and guided decision lifecycle.
- **Single Triage:** Hybrid category prediction (`Keyword Match` vs `Statistical ML`), priority suggestion, uncalibrated score indicators, dynamic threshold review routing, feature contribution signals, and an interactive human verification checklist.
- **Batch Triage:** In-memory CSV validation, shift backlog processing, queue filtering (*All, Review Required, Above Threshold, High Priority*), and enriched export.
- **Model Insights:** Transparent benchmarking of Keyword Rules vs Pure ML vs Hybrid Engine, confusion matrix heatmaps, false-negative root cause analysis, and alternate-phrasing challenge evaluation.
- **About the Product:** Comprehensive APM Product Brief covering user problem, persona, jobs-to-be-done, scope guardrails, and proposed pilot success metrics.

---

## Supported Taxonomy

| Dimension | Supported Labels |
|---|---|
| **Exception Category** | `missing`, `damaged`, `orphan`, `delayed`, `wrong_item` |
| **Urgency Priority** | `low`, `medium`, `high` |

---

## System Architecture

```text
CSV Batch / Single Ticket Description
                 │
                 ▼
     Input Validation & Sanitization (data.py)
                 │
                 ├──────────────────────────────────────────┐
                 ▼                                          ▼
   Domain Keyword Rules (rules.py)              TF-IDF Vectorizer (ngram 1-2)
  (Specific physical logistics terms)                       │
                 │                                          ▼
                 │                          Logistic Regression Classifiers
                 │                           • Category Model (5 classes)
                 │                           • Priority Model (3 classes)
                 │                                          │
                 ▼                                          ▼
           Rule Matched?                           Uncalibrated Scores
          /             \                                   │
      Yes/               \No (needs_review)                 │
        /                 \─────────────────────────────────┘
       ▼
   Hybrid Output Category (100% Holdout / 90% Challenge Accuracy)
       │
       ▼
   Dynamic Uncertainty Gate: min(cat_score, pri_score) < Active Threshold
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                                                   ▼
   Flagged: Human Review Queue                                Passed: Suggestion Ready
       │                                                                   │
       └─────────────────────────────────┬─────────────────────────────────┘
                                         ▼
                     Conservative SOP Action Prompt (recommendations.py)
                                         ▼
                     Human Verification Checklist (No automated action)
```

**Stack:** Python 3.10+ · pandas · scikit-learn · Streamlit · Plotly · pytest

---

## Empirical ML Evaluation & The "Hybrid" Turnaround

When evaluated using a **template-group holdout** (`template_group_holdout`) to isolate template leakage, a simple keyword baseline outperformed the statistical machine learning model:

| Evaluation Benchmark | Test Rows | Keyword Baseline | Pure ML (TF-IDF + LogReg) | Hybrid Engine (v1.1) | High-Priority Recall |
|---|---:|---:|---:|---:|---:|
| **Template-Group Holdout** | 233 | **100.0%** | 78.5% | **100.0%** | **100.0%** |
| **Alternate-Phrasing Challenge** | 10 | 60.0% | 70.0% | **90.0%** | **100.0%** |

### The Root Cause Discovery
Investigating the confusion matrix revealed that **pure ML had 0.0% recall on held-out delayed shipments**, misclassifying all 50 delayed test cases as "missing" due to shared tracking vocabulary (*"scan"*, *"transit"*, *"hub"*). Transparent keyword rules anchored on invariant domain phrases (*"sla"*, *"transit window"*, *"held at hub"*) caught all 50.

Conversely, on colloquial alternate phrasing, keyword rules dropped to 60.0% because synonyms were missing from the keyword dictionary. 

**The APM Decision:** We engineered a **Hybrid Rules + ML Fallback Engine**. High-precision rules catch known physical patterns; statistical ML generalizes colloquial phrasing. This hybrid architecture achieves **100.0% on the holdout and 90.0% on alternate phrasing**.

Read the full investigation in [docs/MODEL_EVALUATION_REPORT.md](docs/MODEL_EVALUATION_REPORT.md).

---

## Google APM Portfolio Documentation Suite

| Document | Purpose & Key Topics |
|---|---|
| [Product Requirements Document (PRD)](docs/PRODUCT_REQUIREMENTS_DOCUMENT.md) | Personas, JTBD, RICE feature prioritization, MVP scope, and safety guardrails. |
| [Technical Architecture Document](docs/TECHNICAL_ARCHITECTURE.md) | Component architecture, latency profiles, dynamic threshold state design, and security. |
| [Model Evaluation Report](docs/MODEL_EVALUATION_REPORT.md) | Holdout design, failure analysis (delayed vs missing), calibration caveats, and hybrid results. |
| [User Research & Validation Toolkit](docs/USER_RESEARCH_TOOLKIT.md) | 5–8 associate interview protocol, discovery questionnaire, workflow mapping, and usability scripts. |
| [Product Experimentation Plan](docs/PRODUCT_EXPERIMENTATION_PLAN.md) | Cluster-randomized shift crossover A/B experiment, power calculations, and stop rules. |
| [Product Roadmap (v1.1 $\to$ v2.5)](docs/PRODUCT_ROADMAP.md) | Multi-horizon strategy from prototype to WMS API integration and computer vision. |
| [Google APM Interview Case Study](docs/APM_CASE_STUDY.md) | End-to-end APM case study detailing problem discovery, data pivots, trade-offs, and metrics. |
| [Two-Minute Product Demo Script](docs/TWO_MINUTE_DEMO_SCRIPT.md) | Timed 120-second interview demo narrative for hiring managers and recruiters. |
| [Resume & Portfolio Descriptions](docs/RESUME_PROJECT_DESCRIPTION.md) | Google-style XYZ resume bullet points and LinkedIn project descriptions. |

---

## Quick Start (Local Development)

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_model.py
python scripts/evaluate_model.py
pytest -q
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_model.py
python scripts/evaluate_model.py
pytest -q
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Automated Verification Suite

Run the complete 17-test automated verification suite:

```bash
pytest -q
# Or with standard library unittest (zero extra dependency):
python -m unittest discover -s tests -p "test_*.py"
```

Tests cover:
- Reproducible synthetic ticket generation and size bounds
- Keyword baseline category detection and safety fallback recommendations
- Batch CSV validation (missing columns, row overflows, 5MB ceiling, empty values)
- Model predictions, feature signal extraction, and overlength string handling (>5,000 chars)
- Dynamic threshold recalculation (verifying zero stale review state)
- Hybrid classification behavior (rule hit vs ML fallback)
- Holdout metrics and alternate-phrasing evaluation generation

---

## Deploy to Streamlit Community Cloud

ShipTriage v1.1.0 includes an idempotent initialization lifecycle (`ensure_models_and_evaluation()`). When deployed to a fresh Streamlit Cloud instance:
1. It automatically trains the classifiers from the bundled synthetic dataset.
2. It generates both holdout and alternate-phrasing evaluation metrics in memory.
3. It launches without requiring manual terminal commands or committing binary artifacts.

See the complete guide in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Product Limitations & Safety Boundaries

- **Synthetic Data Boundary:** All tickets are synthetic. Real-world warehouse tickets exhibit typos, regional abbreviations, and operational slang not present in synthetic data.
- **Uncalibrated Model Scores:** Logistic regression outputs represent margin decision scores, not calibrated probabilities. They must never be treated as guaranteed odds.
- **Zero Autonomous Actions:** ShipTriage never automatically modifies manifests, reroutes trucks, refunds customers, or closes tickets. All physical actions require human associate audit.

---

## License

Created for Google APM portfolio and educational demonstration.
