# ShipTriage

**AI-assisted shipment exception triage · Google APM portfolio prototype · Synthetic data only**

ShipTriage turns a free-text shipment exception note into a predicted issue category, a suggested priority, and a conservative next action. It includes single-ticket and CSV batch workflows, a human-review threshold, model evaluation views, and text-feature signals to make predictions easier to inspect.

> **Important:** ShipTriage is an educational portfolio prototype. It is not connected to Flipkart, Ekart, a carrier, or a real warehouse system. The bundled data is fictional and synthetic. Its model scores are not evidence of real-world performance. Do not enter customer, employee, tracking, shipment, or confidential operational data.

## Product preview

- **Overview:** synthetic dataset snapshot and guided workflow.
- **Single triage:** category, priority, score indicators, review status, suggested next action, and positive text-feature signals.
- **Batch triage:** CSV upload, row validation, review queue filtering, and CSV export.
- **Model insights:** per-class precision/recall/F1, confusion matrices, high-priority recall, keyword baseline, and alternate-phrasing challenge evaluation.
- **Product brief:** user problem, scope, success metrics, and guardrails.

## Supported labels

| Dimension | Labels |
|---|---|
| Exception category | Missing, damaged, orphan, delayed, wrong item |
| Priority | Low, medium, high |

## Architecture

```text
CSV / single ticket
        ↓
Input validation
        ↓
TF-IDF vectorization
        ↓
Logistic Regression classifiers
    ↙                 ↘
Category             Priority
    ↓                   ↓
Model score + review threshold
        ↓
Category-based next-step suggestion
        ↓
Human verification (no automated action)
```

**Stack:** Python · pandas · scikit-learn · Streamlit · Plotly · pytest

## Quick start (Windows PowerShell)

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

Open the local URL shown in the terminal (normally `http://localhost:8501`).

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

The app can rebuild missing or incompatible model artifacts from the included synthetic CSV on first startup. For reproducible local experiments, run the scripts explicitly before launching the app.

### One-command setup scripts

- Windows PowerShell: `./setup_windows.ps1`
- macOS / Linux: `./setup_unix.sh`

These scripts create the virtual environment, install dependencies, generate synthetic data, train/evaluate the models, run tests, and launch the app.

## Deploy

### Streamlit Community Cloud

1. Push this project to a GitHub repository.
2. Visit <https://share.streamlit.io/> and sign in with GitHub.
3. Select **Create app**, choose the repository and branch, and set the app file to `app.py`.
4. Deploy. The app will install `requirements.txt` and create local model artifacts from the synthetic dataset if needed.

See the [official Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) or [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

### Docker

```bash
docker build -t shiptriage:latest .
docker run --rm -p 8501:8501 shiptriage:latest
```

Open `http://localhost:8501`. The included Dockerfile generates the sample data and trains the models during image build.

## Project structure

```text
shiptriage/
├── app.py
├── requirements.txt
├── Dockerfile
├── Procfile
├── AGENTS.md
├── data/
│   ├── synthetic_tickets.csv
│   ├── unseen_tickets.csv
│   └── batch_demo.csv
├── docs/
│   ├── PRODUCT_BRIEF.md
│   ├── EVALUATION_NOTES.md
│   └── DEPLOYMENT.md
├── scripts/
│   ├── generate_data.py
│   ├── train_model.py
│   └── evaluate_model.py
├── src/shiptriage/
│   ├── constants.py
│   ├── data.py
│   ├── modeling.py
│   ├── recommendations.py
│   └── rules.py
└── tests/
    └── test_pipeline.py
```

## Evaluation methodology

The generator records `template_id` metadata. Model evaluation uses a template-group holdout when available to reduce near-duplicate template leakage. The model does not receive `template_id` as input. A fallback stratified split is used for datasets without suitable metadata. Metrics include per-class precision, recall, F1, confusion matrices, high-priority recall, and a keyword baseline.

A small manually authored alternate-phrasing set is also evaluated. It is exploratory, not statistically representative. See [docs/EVALUATION_NOTES.md](docs/EVALUATION_NOTES.md).

## Product thinking

Read [docs/PRODUCT_BRIEF.md](docs/PRODUCT_BRIEF.md) for the persona, problem hypothesis, MVP scope, guardrails, proposed success measures, and validation plan.

## Limitations

- Synthetic data is not a substitute for independently labeled operational tickets.
- The alternate-phrasing challenge set is small.
- Logistic Regression top-class scores are not calibrated probabilities.
- Text signals are feature contributions, not causal explanations.
- Priority depends on SLA and customer context that may be missing from a short ticket note.
- The application has no authentication, database, audit logging, or production monitoring.
- All suggested actions require human verification.

## License

For portfolio and learning use. Add a license file before distributing under a specific open-source license.
