#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_model.py
python scripts/evaluate_model.py
pytest -q
streamlit run app.py
