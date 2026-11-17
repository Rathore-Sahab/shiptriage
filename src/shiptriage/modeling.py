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
    METRICS_PATH,
    MODELS_DIR,
    PRIORITIES,
    PRIORITY_MODEL_PATH,
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
    return {
        "category": str(category_model.classes_[category_index]),
        "priority": str(priority_model.classes_[priority_index]),
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
