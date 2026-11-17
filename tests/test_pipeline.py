from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiptriage.constants import CATEGORIES  # noqa: E402
from shiptriage.data import generate_synthetic_tickets, validate_batch_csv  # noqa: E402
from shiptriage.modeling import _split_dataset, predict_ticket, train_and_evaluate  # noqa: E402
from shiptriage.recommendations import recommend_next_action  # noqa: E402
from shiptriage.rules import rule_based_category  # noqa: E402


def test_generator_is_reproducible_and_has_expected_size():
    first = generate_synthetic_tickets(rows_per_category=10, seed=7)
    second = generate_synthetic_tickets(rows_per_category=10, seed=7)
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 50
    assert first["ticket_id"].is_unique
    assert set(first["data_type"]) == {"synthetic"}
    assert "template_id" in first.columns


def test_generator_rejects_invalid_size():
    with pytest.raises(ValueError):
        generate_synthetic_tickets(rows_per_category=0)


def test_keyword_baseline_detects_clear_categories():
    assert rule_based_category("The carton is crushed and damaged") == "damaged"
    assert rule_based_category("Package has no matching order record") == "orphan"
    assert rule_based_category("Shipment is delayed with no onward movement") == "delayed"


def test_recommendation_has_safe_fallback():
    assert "hold" in recommend_next_action("damaged").lower()
    assert "manually" in recommend_next_action("unknown").lower()


def test_batch_validation_requires_description_and_limits_rows():
    with pytest.raises(ValueError, match="description"):
        validate_batch_csv(pd.DataFrame({"ticket_ref": ["A"]}))
    with pytest.raises(ValueError, match="5,000"):
        validate_batch_csv(pd.DataFrame({"description": ["x"] * 5001}))


def test_batch_validation_normalizes_missing_descriptions():
    result = validate_batch_csv(pd.DataFrame({"description": [None, "  parcel delayed  "]}))
    assert result["description"].tolist() == ["", "parcel delayed"]


def test_batch_validation_rejects_large_file():
    with pytest.raises(ValueError, match="5 MB"):
        validate_batch_csv(pd.DataFrame({"description": ["ok"]}), file_size_bytes=6 * 1024 * 1024)


def test_template_aware_split_has_no_template_overlap():
    dataset = generate_synthetic_tickets(rows_per_category=60, seed=12)
    train, test, strategy = _split_dataset(dataset, 42)
    assert strategy == "template_group_holdout"
    assert set(train["template_id"]).isdisjoint(set(test["template_id"]))
    assert set(test["category"]) == set(CATEGORIES)


def test_model_training_produces_metrics_and_predictions(tmp_path, monkeypatch):
    import shiptriage.modeling as modeling
    dataset = generate_synthetic_tickets(rows_per_category=45, seed=17)
    monkeypatch.setattr(modeling, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(modeling, "CATEGORY_MODEL_PATH", tmp_path / "models" / "category.joblib")
    monkeypatch.setattr(modeling, "PRIORITY_MODEL_PATH", tmp_path / "models" / "priority.joblib")
    monkeypatch.setattr(modeling, "METRICS_PATH", tmp_path / "models" / "metrics.json")
    metrics = train_and_evaluate(dataset)
    assert metrics["dataset_rows"] == 225
    assert metrics["split_strategy"] == "template_group_holdout"
    assert 0.0 <= metrics["high_priority_recall"] <= 1.0
    category_model, priority_model = modeling.load_models()
    result = predict_ticket(
        "The parcel is missing from the receiving hub and delivery is due today.",
        category_model,
        priority_model,
        confidence_threshold=0.6,
    )
    assert result["category"] in CATEGORIES
    assert result["priority"] in {"low", "medium", "high"}
    assert 0.0 <= result["category_confidence"] <= 1.0
    assert isinstance(result["category_signals"], list)
    with pytest.raises(ValueError):
        predict_ticket("   ", category_model, priority_model)
