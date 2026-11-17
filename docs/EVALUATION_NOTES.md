# Model Evaluation Notes

## Evaluation design
The generated training dataset includes `template_id` metadata. The primary split groups examples by source template family so that template families are held out from model fitting. `template_id` is metadata only and is never used as a model feature. A fallback stratified random holdout is used only when a dataset does not contain enough compatible template metadata.

The evaluation script reports:
- Category accuracy and per-class precision, recall, and F1.
- Priority accuracy and per-class precision, recall, and F1.
- High-priority recall.
- Category and priority confusion matrices.
- Accuracy of a transparent keyword category baseline.

A separate small, manually authored alternate-phrasing set is evaluated by `scripts/evaluate_model.py`. This set is a qualitative stress test, not a statistically representative benchmark.

## Included reproducible run

The latest run included in this package used 1,375 generated examples:

| Evaluation set | Rows | Category accuracy | Priority accuracy | High-priority recall | Keyword category baseline |
|---|---:|---:|---:|---:|---:|
| Template-group holdout | 233 | 78.5% | 100.0% | 100.0% | 100.0% |
| Alternate-phrasing challenge | 10 | 70.0% | 100.0% | 100.0% | 60.0% |

The holdout split used 1,142 training examples and 233 test examples. Exact values are in `models/metrics.json` and `models/unseen_evaluation.json`.

## Interpretation

- All labels and text are synthetic. These values do not represent warehouse performance.
- On the template-group holdout, the keyword baseline outperformed the ML classifier for category prediction. That is a meaningful finding: the more complex ML approach is not automatically the better product choice on this dataset.
- The alternate-phrasing set gives a different pattern and contains only 10 examples. A single example materially changes its accuracy, so interpret it as a diagnostic rather than a stable benchmark.
- High priority recall is 100% on these synthetic tests only. It is not evidence that real urgent shipments would never be missed.
- Logistic Regression's maximum class score is not calibrated confidence.
- Before a real pilot, obtain properly approved and anonymized operational examples, create an independently labeled evaluation set, and measure class-level recall—especially recall for high-priority tickets.

## Reproduce

```bash
python scripts/generate_data.py
python scripts/train_model.py
python scripts/evaluate_model.py
pytest -q
```

The scripts replace the actual metrics with the results from your current environment and code. Do not quote metrics in a resume or interview without naming the evaluation set, sample size, and synthetic-data limitation.
