"""Training, evaluation, inference, and lightweight prediction explanations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import random

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from shiptriage.constants import (
    CATEGORIES,
    CATEGORY_MODEL_PATH,
    DATASET_PATH,
    METRICS_PATH,
    MODELS_DIR,
    PRIORITIES,
    PRIORITY_MODEL_PATH,
    UNSEEN_METRICS_PATH,
    UNSEEN_PATH,
)
from shiptriage.rules import rule_based_category


def _build_text_classifier() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=12000,
                    sublinear_tf=True,
                ),
            ),
            ("classifier", LogisticRegression(max_iter=1500, class_weight="balanced")),
        ]
    )


def _split_dataset(dataset: pd.DataFrame, random_state: int) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Prefer template-family holdout to reduce near-duplicate leakage."""
    if "template_id" in dataset.columns and dataset["template_id"].nunique() >= 10:
        # Choose held-out template families within each category so every class
        # is represented in both folds and no family crosses the split.
        rng = random.Random(random_state)
        held_out_groups: set[str] = set()
        for category in CATEGORIES:
            groups = sorted(dataset.loc[dataset["category"] == category, "template_id"].dropna().astype(str).unique())
            if len(groups) < 2:
                held_out_groups = set()
                break
            count = max(1, round(len(groups) * 0.20))
            held_out_groups.update(rng.sample(groups, count))
        if held_out_groups:
            test_mask = dataset["template_id"].astype(str).isin(held_out_groups)
            train_df = dataset.loc[~test_mask].copy()
            test_df = dataset.loc[test_mask].copy()
            if set(train_df["category"]) == set(CATEGORIES) and set(test_df["category"]) == set(CATEGORIES):
                return train_df, test_df, "template_group_holdout"
    train_df, test_df = train_test_split(
        dataset,
        test_size=0.20,
        random_state=random_state,
        stratify=dataset["category"],
    )
    return train_df.copy(), test_df.copy(), "stratified_random_holdout"


def _report(y_true: pd.Series, y_pred: np.ndarray, labels: list[str]) -> dict[str, Any]:
    return classification_report(
        y_true, y_pred, labels=labels, output_dict=True, zero_division=0
    )


def hybrid_predict_category(
    description: str,
    category_model: Pipeline,
) -> tuple[str, str, float]:
    """Combine high-precision domain rules with statistical ML fallback.

    Returns:
        tuple of (predicted_category, strategy_used, decision_score)
        where strategy_used is 'keyword_rule', 'ml_fallback', or 'empty_input'.
    """
    rule_cat = rule_based_category(description)
    if rule_cat != "needs_review":
        return rule_cat, "keyword_rule", 0.95
    clean_text = (description or "").strip()
    if not clean_text:
        return "needs_review", "empty_input", 0.0
    probabilities = category_model.predict_proba([clean_text])[0]
    class_index = int(np.argmax(probabilities))
    return str(category_model.classes_[class_index]), "ml_fallback", float(probabilities[class_index])


def train_and_evaluate(dataset: pd.DataFrame, random_state: int = 42) -> dict[str, Any]:
    """Train both classifiers and save artifacts plus class-level metrics."""
    required = {"description", "category", "priority"}
    missing = required.difference(dataset.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    if dataset[list(required)].isna().any().any():
        raise ValueError("Descriptions and labels cannot contain missing values")
    if set(dataset["category"].unique()) != set(CATEGORIES):
        raise ValueError(f"Category labels must be exactly: {CATEGORIES}")
    if set(dataset["priority"].unique()) != set(PRIORITIES):
        raise ValueError(f"Priority labels must be exactly: {PRIORITIES}")

    train_df, test_df, split_strategy = _split_dataset(dataset, random_state)
    category_model = _build_text_classifier()
    priority_model = _build_text_classifier()
    category_model.fit(train_df["description"], train_df["category"])
    priority_model.fit(train_df["description"], train_df["priority"])

    category_predictions = category_model.predict(test_df["description"])
    priority_predictions = priority_model.predict(test_df["description"])
    rule_predictions = np.array([rule_based_category(text) for text in test_df["description"]])
    hybrid_tuples = [hybrid_predict_category(text, category_model) for text in test_df["description"]]
    hybrid_predictions = np.array([item[0] for item in hybrid_tuples])

    category_report = _report(test_df["category"], category_predictions, CATEGORIES)
    priority_report = _report(test_df["priority"], priority_predictions, PRIORITIES)
    high_recall = recall_score(
        (test_df["priority"] == "high").astype(int),
        (priority_predictions == "high").astype(int),
        zero_division=0,
    )

    metrics: dict[str, Any] = {
        "dataset_rows": int(len(dataset)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "split_strategy": split_strategy,
        "category_accuracy": float(accuracy_score(test_df["category"], category_predictions)),
        "priority_accuracy": float(accuracy_score(test_df["priority"], priority_predictions)),
        "keyword_baseline_accuracy": float(accuracy_score(test_df["category"], rule_predictions)),
        "hybrid_accuracy": float(accuracy_score(test_df["category"], hybrid_predictions)),
        "high_priority_recall": float(high_recall),
        "category_report": category_report,
        "priority_report": priority_report,
        "category_confusion_matrix": confusion_matrix(
            test_df["category"], category_predictions, labels=CATEGORIES
        ).tolist(),
        "priority_confusion_matrix": confusion_matrix(
            test_df["priority"], priority_predictions, labels=PRIORITIES
        ).tolist(),
        "category_labels": CATEGORIES,
        "priority_labels": PRIORITIES,
        "evaluation_note": (
            "Holdout scores on synthetic data. Template groups are held out when metadata is available; "
            "this is not evidence of real-world or production performance."
        ),
    }

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(category_model, CATEGORY_MODEL_PATH)
    joblib.dump(priority_model, PRIORITY_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def load_models() -> tuple[Pipeline, Pipeline]:
    """Load the trained inference artifacts."""
    if not CATEGORY_MODEL_PATH.exists() or not PRIORITY_MODEL_PATH.exists():
        raise FileNotFoundError("Model files missing. Run `python scripts/train_model.py` first.")
    return joblib.load(CATEGORY_MODEL_PATH), joblib.load(PRIORITY_MODEL_PATH)


def evaluate_alternate_phrasings(
    unseen_path: Path = UNSEEN_PATH,
    output_path: Path = UNSEEN_METRICS_PATH,
    category_model: Pipeline | None = None,
    priority_model: Pipeline | None = None,
) -> dict[str, Any]:
    """Evaluate models and hybrid baseline on alternate-phrasing challenge set."""
    if not unseen_path.exists():
        raise FileNotFoundError(f"Alternate-phrasing set not found: {unseen_path}")
    if category_model is None or priority_model is None:
        category_model, priority_model = load_models()

    unseen = pd.read_csv(unseen_path)
    category_pred = category_model.predict(unseen["description"])
    priority_pred = priority_model.predict(unseen["description"])
    baseline = [rule_based_category(text) for text in unseen["description"]]
    hybrid_results = [hybrid_predict_category(text, category_model) for text in unseen["description"]]
    hybrid_pred = [h[0] for h in hybrid_results]

    results: dict[str, Any] = {
        "unseen_rows": int(len(unseen)),
        "category_accuracy": float(accuracy_score(unseen["category"], category_pred)),
        "priority_accuracy": float(accuracy_score(unseen["priority"], priority_pred)),
        "hybrid_category_accuracy": float(accuracy_score(unseen["category"], hybrid_pred)),
        "high_priority_recall": float(recall_score(
            (unseen["priority"] == "high").astype(int),
            (priority_pred == "high").astype(int),
            zero_division=0,
        )),
        "keyword_baseline_accuracy": float(accuracy_score(unseen["category"], baseline)),
        "category_report": classification_report(unseen["category"], category_pred, output_dict=True, zero_division=0),
        "priority_report": classification_report(unseen["priority"], priority_pred, output_dict=True, zero_division=0),
        "predictions": [
            {
                "ticket_id": str(row.ticket_id),
                "actual_category": str(row.category),
                "predicted_category": str(category_pred[index]),
                "hybrid_category": str(hybrid_pred[index]),
                "hybrid_strategy": str(hybrid_results[index][1]),
                "actual_priority": str(row.priority),
                "predicted_priority": str(priority_pred[index]),
                "keyword_baseline_category": str(baseline[index]),
            }
            for index, row in enumerate(unseen.itertuples(index=False))
        ],
        "evaluation_note": "Small manually authored challenge set; exploratory only, not a representative operational benchmark.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def ensure_models_and_evaluation() -> tuple[Pipeline, Pipeline, dict[str, Any], dict[str, Any]]:
    """Ensure models, holdout metrics, and alternate-phrasing metrics exist and are loaded.

    Guarantees clean startup on fresh deployments (e.g., Streamlit Community Cloud)
    without relying on manual terminal commands.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    needs_training = (
        not CATEGORY_MODEL_PATH.exists()
        or not PRIORITY_MODEL_PATH.exists()
        or not METRICS_PATH.exists()
    )
    if needs_training:
        if not DATASET_PATH.exists():
            from shiptriage.data import generate_synthetic_tickets
            DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
            dataset = generate_synthetic_tickets(rows_per_category=275, seed=42)
            dataset.to_csv(DATASET_PATH, index=False)
        else:
            dataset = pd.read_csv(DATASET_PATH)
        metrics = train_and_evaluate(dataset)
        cat_model, pri_model = load_models()
    else:
        try:
            cat_model, pri_model = load_models()
            metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except Exception:
            dataset = pd.read_csv(DATASET_PATH)
            metrics = train_and_evaluate(dataset)
            cat_model, pri_model = load_models()

    needs_unseen_eval = not UNSEEN_METRICS_PATH.exists()
    if needs_unseen_eval and UNSEEN_PATH.exists():
        unseen_metrics = evaluate_alternate_phrasings(
            unseen_path=UNSEEN_PATH,
            output_path=UNSEEN_METRICS_PATH,
            category_model=cat_model,
            priority_model=pri_model,
        )
    else:
        try:
            unseen_metrics = json.loads(UNSEEN_METRICS_PATH.read_text(encoding="utf-8"))
        except Exception:
            unseen_metrics = {}

    return cat_model, pri_model, metrics, unseen_metrics


def explain_prediction(description: str, model: Pipeline, top_n: int = 5) -> list[dict[str, float | str]]:
    """Return influential present tokens for the predicted class (not causal explanations)."""
    vectorizer: TfidfVectorizer = model.named_steps["tfidf"]
    classifier: LogisticRegression = model.named_steps["classifier"]
    vector = vectorizer.transform([description])
    probabilities = model.predict_proba([description])[0]
    class_index = int(np.argmax(probabilities))
    feature_names = vectorizer.get_feature_names_out()
    row = vector.tocsr()
    if classifier.coef_.shape[0] == 1:
        weights = classifier.coef_[0] if class_index == 1 else -classifier.coef_[0]
    else:
        weights = classifier.coef_[class_index]
    contributions = row.toarray()[0] * weights
    indices = np.argsort(contributions)[::-1]
    output: list[dict[str, float | str]] = []
    for index in indices:
        if contributions[index] <= 0:
            break
        term = str(feature_names[index])
        if term.strip():
            output.append({"term": term, "contribution": float(contributions[index])})
        if len(output) >= top_n:
            break
    return output


def predict_ticket(
    description: str,
    category_model: Pipeline,
    priority_model: Pipeline,
    confidence_threshold: float = 0.60,
) -> dict[str, Any]:
    """Predict ticket labels and flag low-scoring results for human review."""
    clean_text = (description or "").strip()
    if not clean_text:
        raise ValueError("Please enter a shipment ticket description.")
    if len(clean_text) > 5000:
        raise ValueError("Ticket descriptions must be 5,000 characters or fewer.")

    category_probabilities = category_model.predict_proba([clean_text])[0]
    priority_probabilities = priority_model.predict_proba([clean_text])[0]
    category_index = int(category_probabilities.argmax())
    priority_index = int(priority_probabilities.argmax())
    category_score = float(category_probabilities[category_index])
    priority_score = float(priority_probabilities[priority_index])

    hybrid_category, hybrid_strategy, _ = hybrid_predict_category(clean_text, category_model)

    return {
        "category": str(category_model.classes_[category_index]),
        "priority": str(priority_model.classes_[priority_index]),
        "hybrid_category": hybrid_category,
        "hybrid_strategy": hybrid_strategy,
        "category_score": category_score,
        "priority_score": priority_score,
        "category_confidence": category_score,
        "priority_confidence": priority_score,
        "review_required": min(category_score, priority_score) < confidence_threshold,
        "review_threshold": float(confidence_threshold),
        "category_scores": {
            str(label): float(score)
            for label, score in zip(category_model.classes_, category_probabilities)
        },
        "priority_scores": {
            str(label): float(score)
            for label, score in zip(priority_model.classes_, priority_probabilities)
        },
        "category_signals": explain_prediction(clean_text, category_model),
        "priority_signals": explain_prediction(clean_text, priority_model),
    }
