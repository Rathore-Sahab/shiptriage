# ShipTriage — Product Case Study

## One-line summary
A human-in-the-loop prototype that structures free-text shipment exceptions into a suggested issue category, urgency level, and next operational step.

## Problem hypothesis
An issue-resolution associate may spend time reading free-text exception notes and deciding what type of issue they represent, how urgent they are, and what should happen next. A structured first-pass suggestion could reduce cognitive overhead and make triage more consistent. This hypothesis needs user validation.

## User
Warehouse issue-resolution associates coordinating inbound and outbound shipment exceptions.

## Product approach
1. Accept one ticket description or a CSV batch.
2. Use TF-IDF + Logistic Regression models to suggest a category and priority.
3. Display model scores and text-feature signals.
4. Flag low-scoring predictions for manual review.
5. Suggest a conservative next step based on the predicted category.
6. Keep the associate responsible for verification and action.

## Important product decision
The model is not allowed to close, reroute, refund, or communicate about a shipment. The first version focuses on decision support, uncertainty visibility, and human control.

## Evaluation and what was learned
The primary synthetic evaluation uses a template-family holdout to reduce near-duplicate phrase leakage. In the included 1,375-row synthetic run, the simple keyword category baseline outperformed the ML category model on this split, while the priority model performed strongly on the synthetic labels. A 10-row alternate-phrasing challenge set shows different behavior again. These are synthetic diagnostic results, not real-world performance claims.

**Product implication:** The model is not automatically the best choice just because it is more sophisticated. The next step should be to inspect the errors, validate ticket language with actual users, and compare the ML model with simpler rules on an independently labeled and approved dataset. If rules outperform ML for a category, use the simpler baseline or a hybrid approach until evidence supports a more complex model.

## Proposed pilot success measures (not yet measured)
- Median time to initial triage decision.
- Correct categorization rate from an independent reviewer audit.
- High-priority recall and urgent misses.
- Manual-review rate.
- Associate override / acceptance rate.
- Misrouted or reopened-ticket rate.

## Limitations
- The training and challenge data are synthetic.
- The alternate-phrasing set is small.
- Logistic Regression scores are not calibrated probabilities.
- Feature terms are model signals, not causal explanations.
- Priority may depend on SLA or customer context missing from text.
- No real operational usability study or impact measurement has been completed.

## Two-minute demo narrative

**0:00–0:20 — Problem:** “In an issue-resolution workflow, associates may need to interpret free-text shipment exceptions before deciding urgency and next steps.”

**0:20–0:45 — Product:** “ShipTriage structures a ticket into a category and priority, surfaces the text signals, and recommends a safe next step.”

**0:45–1:10 — Human control:** “Low-scoring predictions are flagged for manual review. The product never takes shipment actions automatically.”

**1:10–1:40 — Evidence:** “I evaluate with a template-group holdout and a separate alternate-phrasing set. In the current synthetic evaluation, the keyword baseline beats the ML classifier on category accuracy. That tells me the current model is not yet justified as the default.”

**1:40–2:00 — Next step:** “I would validate the workflow with associates, build an independently labeled evaluation set, and test whether a hybrid or rules-first approach produces better decisions without increasing urgent misses.”
