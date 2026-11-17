"""Shared labels, paths, and product defaults."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
DATASET_PATH = DATA_DIR / "synthetic_tickets.csv"
UNSEEN_PATH = DATA_DIR / "unseen_tickets.csv"
CATEGORY_MODEL_PATH = MODELS_DIR / "category_model.joblib"
PRIORITY_MODEL_PATH = MODELS_DIR / "priority_model.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"
UNSEEN_METRICS_PATH = MODELS_DIR / "unseen_evaluation.json"

CATEGORIES = ["missing", "damaged", "orphan", "delayed", "wrong_item"]
PRIORITIES = ["low", "medium", "high"]
CONFIDENCE_THRESHOLD = 0.60
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_BATCH_ROWS = 5000
