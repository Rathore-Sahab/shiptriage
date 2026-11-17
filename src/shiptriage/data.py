"""Reproducible synthetic shipment-ticket dataset generation and validation."""

from __future__ import annotations

import random
from typing import Any

import pandas as pd

from shiptriage.constants import CATEGORIES, MAX_BATCH_ROWS, MAX_UPLOAD_BYTES

CATEGORY_TEMPLATES = {
    "missing": [
        "Tracking has no scan after dispatch from {origin}; the parcel has not reached {destination}.",
        "The manifest lists this parcel, but the receiving hub cannot locate it and no arrival scan is recorded.",
        "Shipment status stopped updating after the origin handover; the package is not present in the destination cage.",
        "The recipient reports non-receipt and tracking has no delivery or destination scan.",
        "A dispatch scan exists, but the parcel is not accounted for during the hub reconciliation count.",
        "The bag was received at {destination}, but this individual shipment is not accounted for.",
    ],
    "damaged": [
        "The parcel arrived with torn outer packaging and a crushed corner; the item may be damaged.",
        "A hub associate found leakage and a broken seal during inbound inspection.",
        "The package is visibly crushed and the contents are rattling; damage evidence needs to be recorded.",
        "The delivery team reported a wet carton and damaged packaging before handover.",
        "The shipment has a puncture mark and the item appears exposed inside the parcel.",
        "The recipient refused the parcel because the box was open and the product was damaged.",
    ],
    "orphan": [
        "A parcel with an AWB label is present at {destination}, but no matching order appears in the system.",
        "The shipment is visible in the physical sort area but is not linked to any manifest or order reference.",
        "An unassigned package was found during scanning; the barcode does not map to a valid shipment record.",
        "The hub received a parcel with an unreadable order reference and no matching record in the dispatch file.",
        "A loose shipment has a valid-looking label but the system shows no associated customer order.",
        "The parcel appears in facility inventory without an owner, route assignment, or manifest mapping.",
    ],
    "delayed": [
        "The shipment has remained at {origin} for {hours} hours with no onward movement and the delivery SLA is at risk.",
        "Tracking shows repeated scans at the same hub and the parcel has missed its planned line-haul departure.",
        "The route handoff is pending and the delivery promise may be missed because the shipment is held at the hub.",
        "The parcel is moving later than the estimated schedule after a connection was missed at {origin}.",
        "No new tracking event has appeared for {hours} hours while the shipment is in transit to {destination}.",
        "The shipment has not reached the next facility within the expected transit window.",
    ],
    "wrong_item": [
        "The received SKU does not match the item on the order; the label and parcel contents disagree.",
        "The recipient received a different product variant from the one listed in the order details.",
        "The pick list shows one item but the packed shipment contains a different SKU and description.",
        "The barcode scan resolves to another product, indicating a possible item substitution in the parcel.",
        "The shipment contains the wrong colour or size compared with the confirmed order.",
        "The item inside the parcel does not match the invoice and needs a mismatch investigation.",
    ],
}

PRIORITY_PHRASES = {
    "high": [
        "A customer escalation has been received and the delivery promise is due today.",
        "The service-level agreement has been breached and urgent attention is required.",
        "This is a high-value order with an immediate customer impact.",
        "The customer is waiting for an update and the committed delivery date is today.",
    ],
    "medium": [
        "The delivery is expected within the next 24 hours and the customer has requested an update.",
        "The shipment is approaching its service target and needs follow-up during this shift.",
        "The issue has been open since the previous shift and a resolution update is pending.",
        "The delivery commitment is approaching, but there is no formal escalation yet.",
    ],
    "low": [
        "There is no customer escalation and the delivery promise is more than 48 hours away.",
        "This is a routine exception with sufficient time remaining before the expected delivery.",
        "The ticket is being monitored as part of the standard daily reconciliation process.",
        "No immediate customer impact has been reported; review can follow the normal queue.",
    ],
}

CONTEXT_PHRASES = [
    "Please investigate and update the exception queue.",
    "The shift team added this note during routine checks.",
    "The issue was raised by an operations associate for review.",
    "A follow-up is required in the shipment control workflow.",
    "The ticket is awaiting ownership by the responsible team.",
    "Please verify the latest scan before taking further action.",
]
ORIGINS = ["Pune", "Nashik", "Nagpur", "Indore", "Surat", "Navi Mumbai"]
DESTINATIONS = ["Mumbai", "Aurangabad", "Kolhapur", "Thane", "Hyderabad", "Bengaluru"]


def generate_synthetic_tickets(rows_per_category: int = 275, seed: int = 42) -> pd.DataFrame:
    """Generate a reproducible labeled dataset with template-family metadata.

    `template_id` is metadata used for group-aware holdout splitting. It is never
    passed as a model feature. All rows are fictional synthetic examples.
    """
    if rows_per_category < 1:
        raise ValueError("rows_per_category must be at least 1")

    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    counter = 1
    for category in CATEGORIES:
        templates = CATEGORY_TEMPLATES[category]
        for index in range(rows_per_category):
            priority = ("low", "medium", "high")[index % 3]
            template_index = rng.randrange(len(templates))
            description = templates[template_index].format(
                origin=rng.choice(ORIGINS),
                destination=rng.choice(DESTINATIONS),
                hours=rng.choice([8, 12, 18, 24, 30, 36]),
            )
            urgency = rng.choice(PRIORITY_PHRASES[priority])
            context = rng.choice(CONTEXT_PHRASES)
            rows.append(
                {
                    "ticket_id": f"ST-{counter:05d}",
                    "description": f"{description} {urgency} {context}",
                    "category": category,
                    "priority": priority,
                    "template_id": f"{category}_template_{template_index}",
                    "data_type": "synthetic",
                }
            )
            counter += 1

    return pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)


def validate_batch_csv(
    dataframe: pd.DataFrame,
    file_size_bytes: int | None = None,
) -> pd.DataFrame:
    """Validate an uploaded ticket CSV and return a safe normalized copy."""
    if file_size_bytes is not None and file_size_bytes > MAX_UPLOAD_BYTES:
        raise ValueError("File is larger than 5 MB. Please upload a smaller CSV.")
    if dataframe.empty:
        raise ValueError("The uploaded CSV has no rows.")
    if len(dataframe) > MAX_BATCH_ROWS:
        raise ValueError(f"Please upload no more than {MAX_BATCH_ROWS:,} rows at a time.")
    if "description" not in dataframe.columns:
        raise ValueError("CSV must include a column named 'description'.")
    result = dataframe.copy()
    result["description"] = result["description"].fillna("").astype(str).str.strip()
    if result["description"].str.len().max() > 5000:
        raise ValueError("A ticket description exceeds 5,000 characters.")
    return result
