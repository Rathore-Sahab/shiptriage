# Deployment Guide

ShipTriage is packaged for a Streamlit-hosted demo and a Docker-based deployment. It is not a hardened production service: there is no authentication, database, audit log, SLA, or production data governance.

## Option A — Streamlit Community Cloud

1. Create an empty GitHub repository (for example, `shiptriage`).
2. Open a terminal in this project folder and push the project:

   ```bash
   git init
   git add .
   git commit -m "Build ShipTriage portfolio prototype"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/shiptriage.git
   git push -u origin main
   ```

   Replace `YOUR_USERNAME` with your GitHub username.
3. Keep `app.py`, `requirements.txt`, `src/`, and `data/` at the repository root/paths shown in the project tree.
4. Sign in at <https://share.streamlit.io/> with GitHub.
5. Select **Create app**, choose your repository and branch, and set the main file path to `app.py`.
6. Deploy. On first startup, the app loads the included synthetic dataset and trains model artifacts automatically if they are missing or incompatible.
7. Open the deployed URL and check Overview, Single triage, Batch triage, and Model insights.

Official instructions: <https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy>

## Option B — Docker

Build and run locally:

```bash
docker build -t shiptriage:latest .
docker run --rm -p 8501:8501 shiptriage:latest
```

Open <http://localhost:8501>.

The container builds the synthetic dataset, trains models, and writes evaluation artifacts during image build. At runtime, Streamlit listens on the injected `PORT` variable or port 8501.

## Local development

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_model.py
python scripts/evaluate_model.py
pytest -q
streamlit run app.py
```

## Pre-deployment checklist

- [ ] Confirm no personal, customer, shipment, tracking, or company confidential data is in the repository.
- [ ] Run tests and inspect the latest model metrics.
- [ ] Confirm the app title and description clearly say prototype / synthetic data.
- [ ] Confirm the GitHub repository has no secrets or `.env` files.
- [ ] Test the deployed app with the supplied sample CSV.
- [ ] Do not present synthetic evaluation as production performance.

## Limitations and security

The demo has no login or role-based access. Do not use it for real operational records. The application code does not save uploaded ticket CSVs to persistent storage, but the hosting platform may have its own operational logs and retention behavior. Review the hosting provider's policies before sharing any uploaded content. For real deployment, add authentication, authorization, privacy review, secure storage controls, audit logging, monitoring, and independently validated models before handling real data.
