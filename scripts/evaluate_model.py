"""Evaluate the models on a small, manually authored alternate-phrasing set."""

import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, recall_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiptriage.constants import UNSEEN_METRICS_PATH, UNSEEN_PATH  # noqa: E402
from shiptriage.modeling import load_models  # noqa: E402
from shiptriage.rules import rule_based_category  # noqa: E402


def main() -> None:
    if not UNSEEN_PATH.exists():
        raise FileNotFoundError(f"Alternate-phrasing set not found: {UNSEEN_PATH}")
    unseen = pd.read_csv(UNSEEN_PATH)
    category_model, priority_model = load_models()
    category_pred = category_model.predict(unseen["description"])
    priority_pred = priority_model.predict(unseen["description"])
    baseline = [rule_based_category(text) for text in unseen["description"]]
    results = {
        "unseen_rows": int(len(unseen)),
        "category_accuracy": float(accuracy_score(unseen["category"], category_pred)),
        "priority_accuracy": float(accuracy_score(unseen["priority"], priority_pred)),
        "high_priority_recall": float(recall_score(
            (unseen["priority"] == "high").astype(int), (priority_pred == "high").astype(int), zero_division=0
        )),
        "keyword_baseline_accuracy": float(accuracy_score(unseen["category"], baseline)),
        "category_report": classification_report(unseen["category"], category_pred, output_dict=True, zero_division=0),
        "priority_report": classification_report(unseen["priority"], priority_pred, output_dict=True, zero_division=0),
        "predictions": [
            {
                "ticket_id": str(row.ticket_id),
                "actual_category": str(row.category),
                "predicted_category": str(category_pred[index]),
                "actual_priority": str(row.priority),
                "predicted_priority": str(priority_pred[index]),
                "keyword_baseline_category": str(baseline[index]),
            }
            for index, row in enumerate(unseen.itertuples(index=False))
        ],
        "evaluation_note": "Small manually authored challenge set; exploratory only, not a representative operational benchmark.",
    }
    UNSEEN_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNSEEN_METRICS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in results.items() if key.endswith("accuracy") or key.endswith("recall")}, indent=2))
    print(f"Detailed results saved to {UNSEEN_METRICS_PATH}")


if __name__ == "__main__":
    main()
