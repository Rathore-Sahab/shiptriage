# Codex prompts — safe iterations after the v1 portfolio release

The current repository is already a runnable portfolio MVP. Read `AGENTS.md` before making changes. Make one change at a time and preserve the safety/product guardrails.

## 1. Audit before editing

```text
Read AGENTS.md, README.md, docs/PRODUCT_BRIEF.md, docs/EVALUATION_NOTES.md,
and the complete codebase. Explain the architecture and the current metrics.
Do not rewrite files without a clear reason. Run pytest and Python compilation.
List risks, limitations, and the highest-value next improvement.
```

## 2. Improve category quality without hiding the baseline

```text
Inspect the category errors on the template-group holdout and alternate-
phrasing challenge set. Compare TF-IDF + Logistic Regression with the keyword
baseline. Identify false positives and false negatives by class. Propose a
hybrid or rules-first approach only when the evidence supports it. Never tune
on the test set and then report that same set as an unbiased evaluation.
Keep all data synthetic and add tests for changes.
```

## 3. Design a user-research experiment

```text
Read docs/PRODUCT_BRIEF.md. Write an interview guide for 5–8 consenting
warehouse/logistics professionals. Ask about their current triage workflow,
where ambiguity occurs, what information is missing, how urgency is decided,
and what makes a recommendation trustworthy. Do not ask for confidential
company/customer/shipment details. Separate observed facts from assumptions.
```

## 4. Improve the product workflow

```text
Review the app as an issue-resolution associate. Identify the top usability
frictions in single-ticket and batch workflows. Propose a small prioritized
change set with user benefit, effort, risk, and success metric. Implement one
small change at a time. Preserve manual review and do not add automatic
shipment actions or real company integrations.
```

## 5. Prepare a credible APM interview story

```text
Use only facts supported by the repository. Prepare a 2-minute demo narrative
and STAR story covering the problem hypothesis, target user, MVP decisions,
model-vs-rule baseline result, failure/limitation, and next experiment. Do not
claim real business impact, production performance, or user validation unless
that evidence has actually been collected and documented.
```

## Quality gates

After changes, run:

```bash
python scripts/generate_data.py   # only if generator/data logic changed
python scripts/train_model.py     # after data/model changes
python scripts/evaluate_model.py  # after model changes
pytest -q
python -m py_compile app.py scripts/*.py src/shiptriage/*.py
```
