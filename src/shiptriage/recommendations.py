"""Conservative, human-directed next-step suggestions."""

RECOMMENDATIONS = {
    "missing": "Check the last confirmed scan, reconcile the dispatch manifest, and contact the relevant hub to locate the shipment.",
    "damaged": "Place the parcel on hold, capture packaging and item evidence, record the damage, and follow the approved claims process.",
    "orphan": "Verify the shipment reference against the manifest and master data, then correct the mapping through the approved workflow.",
    "delayed": "Review the latest scan and route handoff, check the delivery SLA, and escalate to the responsible hub if at risk.",
    "wrong_item": "Hold further dispatch, verify the item against the order, document the mismatch, and route it for approved correction.",
}


def recommend_next_action(category: str) -> str:
    return RECOMMENDATIONS.get(
        category,
        "Review the ticket manually and follow the team's approved standard operating procedure.",
    )
