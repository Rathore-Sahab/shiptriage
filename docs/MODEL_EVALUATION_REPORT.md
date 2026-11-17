# ShipTriage — Model Evaluation & ML Engineering Report

**Version:** v1.1.0  
**Evaluator:** Product AI/ML Engineering  
**Dataset:** Synthetic Logistics Exception Corpus (1,375 rows) + Alternate-Phrasing Challenge Set (10 rows)  
**Date:** November 2026  

---

## 1. Executive Summary & Core Findings

In building machine learning products for high-stakes operational environments, an associate product manager must balance model sophistication with empirical reliability. 

ShipTriage v1.1.0 evaluates three distinct classification approaches across two synthetic benchmark sets:
1. **Keyword Domain Rules:** Deterministic substring dictionary matching based on warehouse physical and transit signatures.
2. **Statistical ML:** TF-IDF unigrams/bigrams ($12,000$ features) + class-balanced Multinomial Logistic Regression.
3. **Hybrid Engine:** High-precision domain rules evaluated first, with statistical ML serving as a fallback for tickets where rules return `needs_review`.

### Primary Empirical Results

| Architecture | Template-Group Holdout Accuracy (233 rows) | Alternate-Phrasing Challenge Accuracy (10 rows) | High-Priority Recall (Holdout) | High-Priority Recall (Challenge) |
|---|---:|---:|---:|---:|
| **Keyword Rules Baseline** | **100.0%** | 60.0% | N/A (Category only) | N/A |
| **Statistical ML (TF-IDF + LogReg)** | 78.5% | 70.0% | **100.0%** | **100.0%** |
| **Hybrid (Rules + ML Fallback)** | **100.0%** | **90.0%** | **100.0%** | **100.0%** |

> **Key Takeaway:** The keyword baseline outperformed pure ML on the template holdout because pure ML developed an acute blind spot on delayed shipments. However, keyword rules proved brittle on colloquial, unseen phrasing (dropping to 60%). The **Hybrid approach combines the precision of domain rules with the linguistic adaptability of ML**, achieving the highest overall reliability across both datasets.

---

## 2. Evaluation Methodology & Holdout Design

### 2.1 The Danger of Naive Random Splits
In synthetic and template-generated NLP datasets, a standard stratified random split creates severe **data leakage**: identical sentence stems appear in both training and test sets with only minor slot variations (e.g. city names changing from Pune to Nagpur). This inflates apparent test accuracy to near 100%, masking a model's inability to generalize.

### 2.2 Template-Group Holdout Strategy
To evaluate true generalization, ShipTriage embeds `template_id` metadata during synthetic generation. In `_split_dataset()`:
- 20% of template families within each category are selected randomly and held out entirely from training.
- No template family crosses the split boundary.
- The model never receives `template_id` as an input feature.
- Total split: **1,142 training examples** and **233 test examples**.

---

## 3. Deep Dive: Why Did Rules Outperform ML on the Holdout?

### 3.1 The "Delayed" Classification Failure
Examining the per-class performance of the pure ML model on the 233-row template holdout reveals an extreme disparity:

```json
"category_report": {
  "damaged":    { "precision": 1.00, "recall": 1.00, "f1-score": 1.00 },
  "orphan":     { "precision": 1.00, "recall": 1.00, "f1-score": 1.00 },
  "wrong_item": { "precision": 1.00, "recall": 1.00, "f1-score": 1.00 },
  "missing":    { "precision": 0.44, "recall": 1.00, "f1-score": 0.62 },
  "delayed":    { "precision": 0.00, "recall": 0.00, "f1-score": 0.00 }
}
```

Every single one of the 50 held-out "delayed" shipments was misclassified as "missing", causing delayed recall to collapse to **0.0%** and missing precision to drop to **44.4%**.

### 3.2 Root Cause Analysis
1. **Vocabulary Overlap:** In warehouse logistics, both missing and delayed tickets describe packages that have not completed their expected journey. Words like *"tracking"*, *"scan"*, *"destination"*, *"hub"*, and *"transit"* appear heavily in both classes.
2. **Feature Memorization vs Invariance:** In the 5 training templates for "delayed", the linear classifier assigned large weights to specific phrases like *"stationary"*, *"missed line-haul"*, or *"sla"*. When a 6th template was held out (*"The shipment has not reached the next facility within the expected transit window"*), it lacked those specific memorized n-grams. Because it shared common tracking words with "missing", the classifier's weights tilted toward "missing".
3. **Domain Invariance in Rules:** The keyword baseline searched for invariant logistics markers like `"transit window"` and `"delayed"`. Consequently, rules correctly identified all 50 delayed tickets.

### 3.3 The Failure Mode of Pure Rules on Alternate Phrasings
While rules scored 100% on the template holdout, they scored only **60.0%** on the 10-row manual alternate-phrasing set. In tickets like UT-003, UT-005, and UT-008, associates used natural, colloquial phrasing without the exact keywords in the rule dictionary. The rule engine safely returned `needs_review`, but failed to categorize.

### 3.4 The Hybrid Solution
By running the high-precision rule engine first and falling back to ML when rules return `needs_review`, the **Hybrid Engine achieved 90.0% accuracy** on the alternate-phrasing set and **100.0%** on the template holdout.

---

## 4. Alternate-Phrasing Challenge Set Analysis (10 Rows)

| Ticket ID | Description Excerpt | Actual Class | Keyword Rule | Pure ML | Hybrid Model |
|---|---|---|---|---|---|
| **UT-001** | "...cannot be found in receiving area..." | missing | missing | missing | **missing** |
| **UT-002** | "...carton is split open and device has visible crack..." | damaged | damaged | damaged | **damaged** |
| **UT-003** | "...loose package scanned, no matching customer order..." | orphan | needs_review | orphan | **orphan** |
| **UT-004** | "...consignment is stationary at transfer centre..." | delayed | delayed | delayed | **delayed** |
| **UT-005** | "...blue medium shirt while order is black large shirt..." | wrong_item | needs_review | wrong_item | **wrong_item** |
| **UT-006** | "...handover confirmed, yet no proof of arrival..." | missing | missing | delayed | **missing** |
| **UT-007** | "...liquid seeped through packaging, seal broken..." | damaged | damaged | damaged | **damaged** |
| **UT-008** | "...barcode readable but resolves to no order..." | orphan | needs_review | orphan | **orphan** |
| **UT-009** | "...consignment exceeded planned transit time..." | delayed | needs_review | missing (score: 0.35) | missing (score: 0.35) |
| **UT-010** | "...packing slip lists phone case, package contains charger..." | wrong_item | wrong_item | missing | **wrong_item** |

### Safety Net in Action: Analysis of UT-009
On ticket UT-009 (*"The consignment has exceeded the planned transit time and has not moved since the previous route scan"*), both rules and ML failed, predicting "missing" instead of "delayed".

**Crucial Product Finding:** Look at the ML decision score for UT-009:
$$\text{Missing Decision Score} = 0.350 \quad (35.0\%)$$
Because 35% is far below the default review threshold ($60\%$), **ShipTriage automatically flagged UT-009 for manual review!** The human-in-the-loop safety threshold prevented an automated error from propagating silently.

---

## 5. Model Score Transparency & Calibration Analysis

### 5.1 Why Model Scores are Not Probabilities
In scikit-learn's `LogisticRegression`, `predict_proba()` computes normalized exponentials of linear decision margins:
$$P(y = k \mid x) = \frac{\exp(w_k^T x + b_k)}{\sum_{j=1}^K \exp(w_j^T x + b_j)}$$
These outputs reflect classifier relative margin certainty under `class_weight="balanced"`. They **do not represent calibrated probabilities** of real-world event frequencies for three reasons:
1. **Unbalanced Operational Priors:** In a real warehouse, "delayed" and "missing" shipments do not occur in equal 20% proportions; damaged parcels may represent <2% of throughput.
2. **Extreme Softmax Confidence:** Linear classifiers with high-dimensional n-grams often push softmax values toward 0.90+ on familiar text, creating false overconfidence.
3. **Distribution Shift:** Real associate notes contain typos, regional abbreviations, and shorthand not present in synthetic training data.

### 5.2 UI & Documentation Guidelines
- UI labels are standardized to **Model Decision Score (Uncalibrated)**.
- Tooltips explain that scores represent relative ranking weights, not guaranteed statistical likelihoods.
- The review threshold acts as an operational routing heuristic to divert uncertain scores to human triage.

### 5.3 Future Calibration Roadmap (Post-Pilot)
Before any model scores could ever be interpreted as calibrated probabilities:
1. **Empirical Calibration Dataset:** Collect $\ge 500$ independently audited operational exception notes.
2. **Platt Scaling / Temperature Scaling:** Fit a single-parameter sigmoid over validation log-odds.
3. **Brier Score & Expected Calibration Error (ECE):** Independently validate calibration on held-out operational data before adjusting threshold defaults.
