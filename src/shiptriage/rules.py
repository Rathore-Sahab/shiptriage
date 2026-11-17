"""Simple, transparent keyword baseline used for model comparison.

The baseline is intentionally small and interpretable; it cannot reliably infer
context that is not present in the ticket text.
"""

RULE_KEYWORDS = {
    "damaged": [
        "damaged", "crushed", "torn", "leakage", "broken seal", "puncture",
        "wet carton", "split open", "crack", "seeped", "open packaging",
    ],
    "wrong_item": [
        "wrong item", "different product", "sku does not match", "sku",
        "mismatch", "substitution", "wrong colour", "wrong size",
        "incorrect product", "charger", "phone case",
    ],
    "orphan": [
        "no matching order", "unassigned", "unmapped", "not linked",
        "no associated", "orphan", "no owner", "no route owner",
        "no manifest link", "no order reference",
    ],
    "delayed": [
        "delayed", "no onward movement", "missed connection", "stationary",
        "transfer centre", "transfer center", "transit window", "sla",
        "held at the hub", "repeated scans", "no movement", "missed its planned",
    ],
    "missing": [
        "missing", "cannot locate", "cannot be found", "not found",
        "not located", "non-receipt", "not accounted", "not present",
        "no arrival scan", "no proof of arrival", "cannot be located",
    ],
}


def rule_based_category(description: str) -> str:
    """Predict a category using ordered keyword rules; return review if unclear."""
    text = (description or "").lower()
    # More specific issue signatures are checked before general tracking phrases.
    for category in ("damaged", "wrong_item", "orphan", "delayed", "missing"):
        if any(keyword in text for keyword in RULE_KEYWORDS[category]):
            return category
    return "needs_review"
