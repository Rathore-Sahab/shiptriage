$ErrorActionPreference = "Stop"

Write-Host "[1/5] Creating virtual environment..." -ForegroundColor Cyan
py -3 -m venv .venv
$Python = ".\.venv\Scripts\python.exe"

Write-Host "[2/5] Installing dependencies..." -ForegroundColor Cyan
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

Write-Host "[3/5] Generating synthetic data and training models..." -ForegroundColor Cyan
& $Python scripts\generate_data.py
& $Python scripts\train_model.py
& $Python scripts\evaluate_model.py

Write-Host "[4/5] Running tests..." -ForegroundColor Cyan
& $Python -m pytest -q

Write-Host "[5/5] Starting ShipTriage..." -ForegroundColor Cyan
& $Python -m streamlit run app.py
