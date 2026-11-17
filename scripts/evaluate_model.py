"""Evaluate the models on a small, manually authored alternate-phrasing set."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiptriage.constants import UNSEEN_METRICS_PATH, UNSEEN_PATH  # noqa: E402
from shiptriage.modeling import evaluate_alternate_phrasings, load_models  # noqa: E402


def main() -> None:
    category_model, priority_model = load_models()
    results = evaluate_alternate_phrasings(
        unseen_path=UNSEEN_PATH,
        output_path=UNSEEN_METRICS_PATH,
        category_model=category_model,
        priority_model=priority_model,
    )
    summary = {
        "unseen_rows": results["unseen_rows"],
        "category_accuracy": results["category_accuracy"],
        "keyword_baseline_accuracy": results["keyword_baseline_accuracy"],
        "hybrid_category_accuracy": results["hybrid_category_accuracy"],
        "priority_accuracy": results["priority_accuracy"],
        "high_priority_recall": results["high_priority_recall"],
    }
    print("Alternate-phrasing evaluation results:")
    print(json.dumps(summary, indent=2))
    print(f"Detailed results saved to {UNSEEN_METRICS_PATH}")


if __name__ == "__main__":
    main()
