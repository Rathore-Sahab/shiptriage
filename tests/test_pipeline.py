"""Automated test suite for ShipTriage v1.1.0 (compatible with pytest and unittest)."""

from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiptriage.constants import CATEGORIES, PRIORITIES  # noqa: E402
from shiptriage.data import generate_synthetic_tickets, validate_batch_csv  # noqa: E402
from shiptriage.modeling import (  # noqa: E402
    _split_dataset,
    ensure_models_and_evaluation,
    evaluate_alternate_phrasings,
    hybrid_predict_category,
    load_models,
    predict_ticket,
    train_and_evaluate,
)
from shiptriage.recommendations import recommend_next_action  # noqa: E402
from shiptriage.rules import rule_based_category  # noqa: E402


class TestShipTriagePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.category_model, cls.priority_model, cls.metrics, cls.unseen_metrics = (
            ensure_models_and_evaluation()
        )

    def test_generator_is_reproducible_and_has_expected_size(self):
        first = generate_synthetic_tickets(rows_per_category=10, seed=7)
        second = generate_synthetic_tickets(rows_per_category=10, seed=7)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(len(first), 50)
        self.assertTrue(first["ticket_id"].is_unique)
        self.assertEqual(set(first["data_type"]), {"synthetic"})
        self.assertIn("template_id", first.columns)

    def test_generator_rejects_invalid_size(self):
        with self.assertRaises(ValueError):
            generate_synthetic_tickets(rows_per_category=0)

    def test_keyword_baseline_detects_clear_categories(self):
        self.assertEqual(rule_based_category("The carton is crushed and damaged"), "damaged")
        self.assertEqual(rule_based_category("Package has no matching order record"), "orphan")
        self.assertEqual(rule_based_category("Shipment is delayed with no onward movement"), "delayed")
        self.assertEqual(rule_based_category("Customer received charger instead of phone case"), "wrong_item")
        self.assertEqual(rule_based_category("Completely unrelated random gibberish text"), "needs_review")

    def test_recommendation_has_safe_fallback(self):
        self.assertIn("hold", recommend_next_action("damaged").lower())
        self.assertIn("claims", recommend_next_action("damaged").lower())
        self.assertIn("manually", recommend_next_action("unknown_category").lower())

    def test_batch_validation_requires_description_and_limits_rows(self):
        with self.assertRaises(ValueError):
            validate_batch_csv(pd.DataFrame({"ticket_ref": ["A"]}))
        with self.assertRaises(ValueError):
            validate_batch_csv(pd.DataFrame({"description": ["x"] * 5001}))

    def test_batch_validation_normalizes_missing_descriptions(self):
        result = validate_batch_csv(pd.DataFrame({"description": [None, "  parcel delayed  "]}))
        self.assertEqual(result["description"].tolist(), ["", "parcel delayed"])

    def test_batch_validation_rejects_empty_dataframe(self):
        with self.assertRaises(ValueError):
            validate_batch_csv(pd.DataFrame())

    def test_batch_validation_rejects_large_file(self):
        with self.assertRaises(ValueError):
            validate_batch_csv(pd.DataFrame({"description": ["ok"]}), file_size_bytes=6 * 1024 * 1024)

    def test_batch_validation_rejects_excessively_long_row(self):
        long_text = "x" * 5001
        with self.assertRaises(ValueError):
            validate_batch_csv(pd.DataFrame({"description": [long_text]}))

    def test_template_aware_split_has_no_template_overlap(self):
        dataset = generate_synthetic_tickets(rows_per_category=60, seed=12)
        train, test, strategy = _split_dataset(dataset, 42)
        self.assertEqual(strategy, "template_group_holdout")
        self.assertTrue(set(train["template_id"]).isdisjoint(set(test["template_id"])))
        self.assertEqual(set(test["category"]), set(CATEGORIES))

    def test_predict_ticket_rejects_empty_and_whitespace_descriptions(self):
        with self.assertRaises(ValueError):
            predict_ticket("", self.category_model, self.priority_model)
        with self.assertRaises(ValueError):
            predict_ticket("   \n\t   ", self.category_model, self.priority_model)

    def test_predict_ticket_rejects_overlength_descriptions(self):
        overlength = "A" * 5001
        with self.assertRaises(ValueError):
            predict_ticket(overlength, self.category_model, self.priority_model)

    def test_threshold_recalculation_dynamics(self):
        """Verify threshold evaluation is dynamic and not locked in."""
        text = "Outer carton is torn and product is damaged. High value customer order breached."
        pred_low = predict_ticket(text, self.category_model, self.priority_model, confidence_threshold=0.40)
        pred_high = predict_ticket(text, self.category_model, self.priority_model, confidence_threshold=0.99)

        self.assertEqual(pred_low["category_score"], pred_high["category_score"])
        self.assertEqual(pred_low["priority_score"], pred_high["priority_score"])
        self.assertFalse(pred_low["review_required"])
        self.assertTrue(pred_high["review_required"])

    def test_hybrid_classification_behavior(self):
        """Verify hybrid strategy uses rules when available and falls back to ML."""
        rule_text = "The outer box has puncture damage and leakage."
        cat, strategy, score = hybrid_predict_category(rule_text, self.category_model)
        self.assertEqual(cat, "damaged")
        self.assertEqual(strategy, "keyword_rule")
        self.assertEqual(score, 0.95)

        colloquial_text = "The packing slip lists a phone case, but the package contains a charger."
        cat_ml, strategy_ml, score_ml = hybrid_predict_category(colloquial_text, self.category_model)
        self.assertIn(strategy_ml, {"keyword_rule", "ml_fallback"})
        self.assertIn(cat_ml, CATEGORIES)

    def test_model_training_produces_metrics_and_predictions(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            import shiptriage.modeling as modeling

            old_models_dir = modeling.MODELS_DIR
            old_cat_path = modeling.CATEGORY_MODEL_PATH
            old_pri_path = modeling.PRIORITY_MODEL_PATH
            old_metrics_path = modeling.METRICS_PATH
            old_unseen_path = modeling.UNSEEN_METRICS_PATH

            try:
                modeling.MODELS_DIR = tmp_path / "models"
                modeling.CATEGORY_MODEL_PATH = tmp_path / "models" / "category.joblib"
                modeling.PRIORITY_MODEL_PATH = tmp_path / "models" / "priority.joblib"
                modeling.METRICS_PATH = tmp_path / "models" / "metrics.json"
                modeling.UNSEEN_METRICS_PATH = tmp_path / "models" / "unseen.json"

                dataset = generate_synthetic_tickets(rows_per_category=45, seed=17)
                metrics = train_and_evaluate(dataset)
                self.assertEqual(metrics["dataset_rows"], 225)
                self.assertEqual(metrics["split_strategy"], "template_group_holdout")
                self.assertTrue(0.0 <= metrics["high_priority_recall"] <= 1.0)
                self.assertIn("hybrid_accuracy", metrics)
                self.assertTrue(0.0 <= metrics["hybrid_accuracy"] <= 1.0)

                cat_m, pri_m = modeling.load_models()
                result = predict_ticket(
                    "The parcel is missing from the receiving hub and delivery is due today.",
                    cat_m,
                    pri_m,
                    confidence_threshold=0.6,
                )
                self.assertIn(result["category"], CATEGORIES)
                self.assertIn(result["priority"], PRIORITIES)
                self.assertTrue(0.0 <= result["category_score"] <= 1.0)
                self.assertTrue(0.0 <= result["priority_score"] <= 1.0)
                self.assertIsInstance(result["category_signals"], list)
                self.assertIn(result["hybrid_category"], CATEGORIES)
            finally:
                modeling.MODELS_DIR = old_models_dir
                modeling.CATEGORY_MODEL_PATH = old_cat_path
                modeling.PRIORITY_MODEL_PATH = old_pri_path
                modeling.METRICS_PATH = old_metrics_path
                modeling.UNSEEN_METRICS_PATH = old_unseen_path

    def test_alternate_phrasings_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_json = Path(tmp_dir) / "unseen_eval.json"
            results = evaluate_alternate_phrasings(
                output_path=out_json,
                category_model=self.category_model,
                priority_model=self.priority_model,
            )
            self.assertEqual(results["unseen_rows"], 10)
            self.assertTrue(0.0 <= results["category_accuracy"] <= 1.0)
            self.assertTrue(0.0 <= results["hybrid_category_accuracy"] <= 1.0)
            self.assertTrue(0.0 <= results["keyword_baseline_accuracy"] <= 1.0)
            self.assertTrue(out_json.exists())

    def test_ensure_models_and_evaluation_idempotency(self):
        cat_model, pri_model, metrics, unseen = ensure_models_and_evaluation()
        self.assertIsNotNone(cat_model)
        self.assertIsNotNone(pri_model)
        self.assertIn("category_accuracy", metrics)
        self.assertIn("category_accuracy", unseen)


if __name__ == "__main__":
    unittest.main()
