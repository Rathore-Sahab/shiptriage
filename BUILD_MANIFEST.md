# Build manifest — ShipTriage 1.0.0

## Included

- Streamlit product UI: overview, single triage, CSV batch triage, model insights, product brief.
- Synthetic dataset: 1,375 fictional examples across five categories and three priorities.
- TF-IDF + Logistic Regression model artifacts and evaluation reports.
- Template-family holdout evaluation and alternate-phrasing diagnostic.
- Batch input validation, human-review threshold, text-feature signals, and category recommendations.
- Pytest suite, GitHub Actions quality workflow, Dockerfile, Streamlit Community Cloud instructions.
- Product case study and two-minute APM demo narrative.

## Verification completed in the build environment

- `pytest -q`: 9 passed.
- `python -m py_compile app.py scripts/*.py src/shiptriage/*.py`: passed.
- Synthetic generation, training, and alternate-phrasing evaluation: completed.
- Streamlit UI runtime: not launched in this build environment because Streamlit is not installed here and package installation could not reach the package index. Install `requirements.txt` locally or use the provided hosted deployment path to run the UI.
- Docker image: not built in this build environment because Docker is not installed.

## Included evaluation snapshot

| Set | Rows | Category accuracy | Priority accuracy | Keyword category baseline |
|---|---:|---:|---:|---:|
| Template-group holdout | 233 | 78.5% | 100.0% | 100.0% |
| Alternate-phrasing challenge | 10 | 70.0% | 100.0% | 60.0% |

These are metrics on synthetic data only. See `docs/EVALUATION_NOTES.md` for interpretation and limitations.
