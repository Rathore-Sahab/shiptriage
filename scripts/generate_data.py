"""Generate the reproducible synthetic training dataset."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiptriage.constants import DATASET_PATH  # noqa: E402
from shiptriage.data import generate_synthetic_tickets  # noqa: E402


def main() -> None:
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset = generate_synthetic_tickets(rows_per_category=275, seed=42)
    dataset.to_csv(DATASET_PATH, index=False)
    print(f"Generated {len(dataset):,} synthetic tickets at {DATASET_PATH}")
    print("Labels:")
    print(dataset.groupby(["category", "priority"]).size().to_string())


if __name__ == "__main__":
    main()
