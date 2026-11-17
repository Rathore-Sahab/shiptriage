# ShipTriage — Codex instructions

## Product context
ShipTriage is a portfolio prototype for human-assisted triage of synthetic shipment exception tickets. It is inspired by a warehouse issue-resolution workflow but is not affiliated with or connected to any employer, marketplace, carrier, or warehouse platform.

## Product scope
- Five categories: missing, damaged, orphan, delayed, wrong item.
- Three priority levels: low, medium, high.
- TF-IDF + Logistic Regression baseline classifiers.
- Explain positive text-feature signals with caveats.
- Show a configurable review threshold and keep a human decision-maker in control.
- Support one-ticket and CSV batch workflows.

## Non-negotiable safety/product rules
- Synthetic data only. Never add real customer, tracking, shipment, employee, or company records.
- Never automatically close, reroute, refund, or communicate about a shipment.
- Model top-class scores are not calibrated probabilities.
- Never describe synthetic scores as production accuracy or measured business impact.
- Uploaded CSVs must be validated for required columns, file size, row count, blanks, and excessively long descriptions.
- Do not add network integrations, APIs, databases, auth, or paid services unless explicitly requested.

## Technical conventions
- Python 3.10+; keep code readable and beginner-friendly.
- Keep model training separate from inference and UI.
- Use `template_id` only for grouped holdout evaluation, never as a model input.
- Add tests for new behavior and keep dependencies minimal.
- Keep Streamlit and scikit-learn dependencies within supported ranges.

## Quality gates
Before declaring a change complete:
1. Run `python scripts/generate_data.py` if data generation changed.
2. Run `python scripts/train_model.py` after data/model code changes.
3. Run `python scripts/evaluate_model.py` after training changes.
4. Run `pytest -q`.
5. Run `python -m py_compile app.py scripts/*.py src/shiptriage/*.py`.
6. Report any UI checks that could not be run due to unavailable Streamlit/runtime dependencies.
