# ShipTriage — Product Requirements Document (PRD)

**Product:** ShipTriage  
**Version:** v1.1.0  
**Target Audience:** Warehouse Operations Associates, Hub Shift Supervisors, APM Evaluation Team  
**Author:** Product Management & Engineering  
**Status:** Approved for v1.1 Prototype Release  

---

## 1. Executive Summary & Problem Framing

### 1.1 Context
In high-throughput e-commerce and retail fulfillment logistics (line-haul transit centers, sorting hubs, and delivery stations), package flows are subject to physical and digital discrepancies termed **Shipment Exceptions**. Exceptions include damaged cartons, missing parcels, unmapped/orphan barcodes, line-haul delays, and SKU pack errors.

Currently, exception intake relies on free-text tickets entered by dock workers, bag de-stuffing operators, and customer service teams.

### 1.2 The Core Problem
1. **High Cognitive Overhead & Fatigue:** Warehouse issue-resolution associates must read through dense, non-standardized exception notes (often written under time pressure during shift turnover) to identify the failure root cause.
2. **Inconsistent Triage Quality:** Without standardized decision support, different associates assign conflicting priorities and categories to identical operational issues.
3. **SLA Breach Risk:** High-priority exceptions (escalated customer commitments, SLA-breached line-haul delays) are buried in flat queues, delaying immediate physical intervention.
4. **Automation Traps:** Pure black-box machine learning poses catastrophic operational risks if allowed to make autonomous routing or refund decisions without physical verification.

---

## 2. Target Personas & Jobs to Be Done (JTBD)

### 2.1 Personas

#### Primary Persona: Ramesh — Warehouse Issue-Resolution Associate
- **Role:** Resolves 150–250 physical exception packages daily at a regional distribution center.
- **Pain Points:** Faced with vague ticket descriptions; pressured to clear the exception cage before the line-haul cutoff; fears misrouting a package that gets returned 3 days later.
- **Tech Fluency:** Operational software user; prefers clear, actionable guidance over complex predictive analytics.
- **Needs:** Fast issue categorization, instant urgency cues, clear next-step SOP checklist.

#### Secondary Persona: Priya — Logistics Hub Operations Lead
- **Role:** Manages facility throughput, SLA compliance, and dispatch manifests across shifts.
- **Pain Points:** Lacks aggregate visibility into shift-level exception patterns; struggles to monitor associate triage accuracy and escalation compliance.
- **Needs:** Shift batch triage, review queue monitoring, exportable structured data.

### 2.2 Jobs to Be Done (JTBD)
- **Core Functional Job:** *"When an exception ticket arrives, help me immediately determine the correct failure category and urgency level, and provide the approved operational next step, so I can resolve the package before our line-haul dispatch deadline."*
- **Emotional Job:** *"Give me confidence that I have not overlooked an urgent customer escalation, while keeping me in complete control of the physical verification."*
- **Social Job:** *"Ensure our hub maintains a reputation for high SLA adherence and low downstream misroute rates."*

---

## 3. Product Principles & Guardrails

1. **Human-in-the-Loop Supremacy:** ShipTriage is a *decision-support system*, never an autonomous dispatch agent. It never closes tickets, reroutes trucks, issues refunds, or messages customers.
2. **Transparent Uncertainty:** The system exposes model decision scores and dynamically flags low-scoring tickets for mandatory manual review.
3. **Simplest Working Solution:** Do not favor complex ML when simple domain rules perform more reliably. Employ a hybrid architecture that balances domain precision with linguistic generalization.
4. **Data Privacy & Synthetic Rigor:** No confidential tracking IDs, customer PII, or internal corporate records are ever ingested or stored.

---

## 4. MVP Feature Specifications (v1.1)

### 4.1 Single Ticket Triage
- **Input:** Free-text exception description (up to 5,000 characters).
- **Processing:**
  - Hybrid classification engine: Evaluates ordered domain keywords first; falls back to TF-IDF + Logistic Regression when keywords are absent (`needs_review`).
  - Priority classifier: Logistic Regression assigning `low`, `medium`, or `high` urgency based on SLA and escalation terminology.
- **Dynamic Review Threshold:** Slider in sidebar (0.40 to 0.90, default 0.60).
  - *Dynamic State Rule:* If `min(category_score, priority_score) < active_threshold`, system immediately renders "Review Required" status, dynamically updating without requiring re-submission.
- **Outputs:**
  - Predicted Category with strategy badge (`Keyword Match` vs `Statistical ML`).
  - Suggested Urgency Priority with visual color code.
  - Model Decision Score indicators with explicit uncalibrated score disclosures.
  - Feature contribution tokens (top positive n-grams).
  - Conservative Standard Operating Procedure action recommendation.
  - Interactive Human Verification Checklist (Physical barcode audit, package inspection, SLA check, SOP confirmation).

### 4.2 Batch CSV Triage
- **Input:** CSV file with required `description` column (up to 5 MB, maximum 5,000 rows).
- **Validation:** Rejects missing columns, oversized files, row overflows; normalizes null/blank rows into graceful `needs_review` rows without crashing.
- **Outputs:**
  - Summary metrics: Ingested count, Manual review queue count (% of batch), Above-threshold count, High-priority count.
  - Filtering view: "All exceptions", "Review required queue", "Above threshold only", "High priority only".
  - Downloadable enriched CSV containing input attributes plus `predicted_category`, `predicted_priority`, `category_score`, `priority_score`, `review_required`, `triage_strategy`, `suggested_next_action`.

### 4.3 Model Insights & Transparency
- Side-by-side benchmarking: Keyword Rules vs Pure ML vs Hybrid Model on both template holdouts and alternate phrasing.
- Per-class Precision, Recall, and F1 bar charts.
- Category and Priority Confusion Matrices (Plotly interactive heatmaps).
- Documented False-Negative investigation explaining the "delayed vs missing" vocabulary overlap.

---

## 5. Metrics Framework

### 5.1 Proposed North Star Metric
$$\text{Median Time to Correct Initial Triage Decision} = \text{Median}(T_{\text{decision}} - T_{\text{open}})$$
- **Target:** Reduce median triage time from ~120s (manual inspection) to <35s per ticket in a warehouse pilot.

### 5.2 Proposed Guardrail Metrics
1. **High-Priority Recall:** $\ge 99.0\%$ on urgent/SLA-critical tickets. (Zero tolerance for silent escalations).
2. **Misrouted-Ticket Rate:** $< 2.5\%$ downstream reopened tickets due to triage categorization errors.
3. **Manual Review Rate:** Operational sweet spot of $15\% - 25\%$ routing to human queue under active threshold.
4. **Associate Override Rate:** $< 12\%$ alteration of suggestions, tracking user trust and model alignment.

*(Note: Above metrics represent proposed validation measures for a live pilot; all current application metrics reflect synthetic benchmark evaluation.)*

---

## 6. Feature Prioritization (RICE Framework)

| Feature | Reach (Shift tickets) | Impact (0.5-3) | Confidence (%) | Effort (Person-wks) | RICE Score | Release |
|---|---|---|---|---|---|---|
| Dynamic Review Threshold Gate | 100% | 3.0 (Critical safety) | 100% | 1.0 | **300** | v1.1 (Shipped) |
| Hybrid Rule + ML Fallback | 100% | 3.0 (Eliminates delayed blindspot) | 90% | 1.5 | **180** | v1.1 (Shipped) |
| Batch CSV Queue Filtering | 80% | 2.0 (High operational speed) | 90% | 1.0 | **144** | v1.1 (Shipped) |
| Human Verification Checklist | 100% | 2.0 (Compliance) | 95% | 0.5 | **380** | v1.1 (Shipped) |
| WMS / ERP API Webhook Integration | 100% | 3.0 | 50% (Pilot dependency) | 6.0 | **25** | v2.0 (Roadmap) |
| Fine-Tuned Domain LLM Triage | 40% | 1.0 | 40% | 8.0 | **5** | Deprioritized |

---

## 7. Risk Analysis & Mitigation

| Identified Risk | Severity | Mitigation Strategy |
|---|---|---|
| **Associate Over-reliance (Automation Bias)** | High | Explicit "Review Required" banners; interactive verification checkboxes; disclaimers that scores are uncalibrated. |
| **High-Priority Misclassification** | High | Class-weighted logistic regression prioritizing high urgency; keyword overrides for SLA breach terms; high-priority recall guardrail metric. |
| **Data Drift on Warehouse Slang** | Medium | Hybrid architecture allows immediate keyword patching without full model retraining; periodic alternate-phrasing benchmarking. |
| **Cloud Cold Start Latency** | Low | In-memory artifact auto-initialization (`ensure_models_and_evaluation`) completes in <2.5 seconds on Streamlit Cloud. |
