"""Train the category and priority classifiers."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiptriage.constants import DATASET_PATH  # noqa: E402
from shiptriage.modeling import train_and_evaluate  # noqa: E402


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError("Dataset not found. Run `python scripts/generate_data.py` first.")
    metrics = train_and_evaluate(pd.read_csv(DATASET_PATH))
    print("Training complete.")
    print(f"Split strategy: {metrics['split_strategy']}")
    print(f"Category accuracy: {metrics['category_accuracy']:.3f}")
    print(f"Priority accuracy: {metrics['priority_accuracy']:.3f}")
    print(f"High-priority recall: {metrics['high_priority_recall']:.3f}")
    print(f"Keyword baseline accuracy: {metrics['keyword_baseline_accuracy']:.3f}")
    print("Artifacts saved in models/.")


if __name__ == "__main__":
    main()
