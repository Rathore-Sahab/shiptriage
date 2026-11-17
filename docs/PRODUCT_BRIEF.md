# ShipTriage — Product Brief

## Product summary
ShipTriage is a human-in-the-loop prototype that turns free-text shipment exception notes into a structured category, a suggested priority, and a conservative next-step prompt. It is designed as a portfolio product, not as a live warehouse system.

## Problem hypothesis
Issue-resolution associates may need to read free-text shipment exception notes, identify the issue type, judge urgency, and decide what should happen next. A structured first-pass suggestion may reduce cognitive overhead and improve consistency. This is a hypothesis to validate with users, not an established operational result.

## Primary user
A warehouse issue-resolution associate coordinating inbound and outbound shipment exceptions.

## User need
“When a shipment exception arrives, help me understand the issue type and urgency quickly, and suggest a safe next step so I can focus on coordinating resolution.”

## MVP scope
- Five categories: missing, damaged, orphan, delayed, wrong item.
- Three priorities: low, medium, high.
- TF-IDF + Logistic Regression text classifiers.
- Model score indicators and configurable human-review threshold.
- Positive text signals from the linear classifier, with explanation caveats.
- Category-based next-action suggestions.
- Single-ticket and CSV batch workflows.
- Holdout and alternate-phrasing evaluation views.

## Product guardrails
- Human operator remains the decision-maker.
- Low-scoring predictions are flagged for manual review.
- The app never closes tickets, reroutes shipments, issues refunds, or contacts customers.
- No external API, database, analytics tracker, or company integration is included.
- Uploaded CSV content is processed in memory by the app and is not intentionally persisted by application code.
- Only synthetic sample records are bundled. Do not enter personal, customer, tracking, or confidential operational data.

## Proposed success metrics (not yet measured)
1. Median time from ticket opening to initial triage decision.
2. Correct categorization rate on an independently labeled pilot sample.
3. High-priority recall and number of urgent exceptions missed.
4. Manual-review rate at a chosen threshold.
5. Associate acceptance / override rate for suggestions.
6. Misrouted or reopened-ticket rate after triage.

## Known risks and limitations
- Synthetic examples do not represent real operational language.
- Template-group holdout reduces near-duplicate leakage, but is still a synthetic evaluation.
- The alternate-phrasing challenge set is small and exploratory.
- Logistic Regression's maximum class score is not calibrated confidence.
- Priority depends on real SLA/customer context that may not be present in the note.
- Missing and delayed categories can overlap.
- The top text signals are model-feature contributions, not causal explanations.

## Next validation steps
1. Conduct 5–8 short discovery interviews with consenting logistics or warehouse professionals.
2. Map how they currently read, classify, prioritize, and escalate exception tickets.
3. Ask qualified reviewers to independently label an approved, anonymized sample if data access is authorized.
4. Measure class-level precision/recall and high-priority recall on a held-out, independently labeled test set.
5. Run usability tests comparing manual and assisted triage; record time, correctness, overrides, and trust.
6. Revisit workflow and thresholds based on evidence rather than optimizing accuracy alone.
