# ShipTriage — Product Experimentation Plan

**Objective:** Design a statistically rigorous, operationally feasible controlled experiment to evaluate ShipTriage in an operational warehouse environment.  
**Experiment Lead:** Product Management & Analytics  
**Status:** Pre-Pilot Experimentation Design (Not yet executed)  

---

## 1. Experiment Overview & Hypotheses

### 1.1 Core Problem & Business Rationale
In fulfillment centers, exception handling is a major labor bottleneck and source of line-haul cutoff misses. Associates spend up to 2 minutes per ticket manually deciphering unstructured text notes.

### 1.2 Hypotheses

#### Primary Hypothesis ($H_1$)
Providing warehouse associates with real-time hybrid triage suggestions (category, priority, feature signals, and conservative SOP prompts) will reduce the **median time to initial triage decision by at least 40%** compared to manual baseline triage.
$$H_0: \tilde{T}_{\text{assisted}} \ge \tilde{T}_{\text{manual}} \quad \text{vs.} \quad H_1: \tilde{T}_{\text{assisted}} < \tilde{T}_{\text{manual}}$$

#### Safety Guardrail Hypothesis ($H_{\text{guardrail}}$)
The assisted triage workflow will **not increase downstream ticket misroutes** ($\le 2.5\%$) and will maintain **high-priority recall at $\ge 99.0\%$** on SLA-critical shipments.

---

## 2. Experimental Design & Methodology

### 2.1 Unit of Randomization: Cluster-Randomized Shift Design
- **Why not individual ticket randomization?** Randomizing ticket-by-ticket causes severe cognitive contamination: an associate switching between manual and assisted modes on consecutive packages experiences cognitive interference, biasing latency measurements.
- **Why not individual associate randomization?** Associates on the same sorting deck share physical space; an associate using the tool will informally advise a peer working in manual control.
- **Selected Design:** **Cluster-Randomized Shift Crossover (4-Week Balanced Design)**:
  - Unit: Operational Shifts (Morning Inbound vs Evening Dispatch across 2 comparable fulfillment facilities).
  - Week 1–2: Hub A runs Treatment (ShipTriage Assisted); Hub B runs Control (Standard Manual Triage).
  - Week 3–4: Washout (2 days) followed by crossover: Hub A runs Control; Hub B runs Treatment.

### 2.2 Experiment Variants

| Variant | Description | User Interface | Decision Engine |
|---|---|---|---|
| **Control ($V_0$)** | Standard Operating Procedure | Standard warehouse ticketing interface (unstructured text box, manual dropdowns). | None (Associate manual inspection). |
| **Treatment A ($V_1$)** | Statistical ML Assisted | ShipTriage UI with pure TF-IDF + Logistic Regression suggestions. | Statistical ML only. |
| **Treatment B ($V_2$)** | Hybrid Engine Assisted | ShipTriage UI with Hybrid Rules + ML fallback and dynamic review threshold. | High-precision rules + ML fallback + threshold gate. |

---

## 3. Metrics Matrix & Success Criteria

| Metric | Role | Target Benchmark | Minimum Detectable Effect (MDE) | Data Source |
|---|---|---|---|---|
| **Median Initial Triage Latency ($T_{\text{triage}}$)** | **North Star** | Baseline: ~120s $\to$ Target: <35s | 25 seconds ($\alpha=0.05, \beta=0.20$) | WMS ticket timestamp logs. |
| **High-Priority Recall** | **Guardrail 1** | $\ge 99.0\%$ | 0.5% drop triggers rollback | Independent senior associate audit. |
| **Downstream Misroute Rate** | **Guardrail 2** | $\le 2.5\%$ | $+0.5\%$ increase triggers rollback | Reopened/re-dispatched ticket tags. |
| **Manual Review Queue Rate** | **Operational** | $15\% - 25\%$ | Operational bandwidth balance | ShipTriage threshold trigger logs. |
| **Associate Override Rate** | **Trust/Adoption** | $< 12\%$ | $> 25\%$ indicates model rejection | Logged manual category/priority edits. |

---

## 4. Sample Size & Statistical Power

- **Baseline Metric Distribution:** Historical exception triage duration is log-normally distributed with $\mu = 115\text{ seconds}$, $\sigma = 45\text{ seconds}$.
- **Power Parameters:** Significance level $\alpha = 0.05$ (two-tailed), Power $1 - \beta = 0.80$.
- **Required Sample Size:** To detect an MDE of a 30-second reduction with cluster intra-class correlation ($\text{ICC} = 0.03$), the experiment requires:
  $$N_{\text{tickets}} \approx 1,200 \text{ tickets per variant}$$
  At an average facility rate of $150 \text{ exceptions/shift}$, a 2-week active testing window per hub yields $\approx 2,100 \text{ tickets}$, providing statistical power $> 90\%$.

---

## 5. Threats to Validity & Mitigation

1. **Hawthorne Effect (Novelty Bias):**
   - *Risk:* Associates perform faster simply because an observer or new tool is present.
   - *Mitigation:* Conduct a 3-day non-measured "burn-in" period prior to active data collection so the tool becomes routine.
2. **Shift Volume Volatility (Seasonality):**
   - *Risk:* A sudden rainfall or supplier promotion spikes package damage in Week 2, distorting duration metrics.
   - *Mitigation:* Difference-in-Differences (DiD) regression modeling controlling for shift package volume and day-of-week fixed effects.
3. **Automation Complacency:**
   - *Risk:* Associates blindly accept suggestions without inspecting physical packages.
   - *Mitigation:* The 4-step Human Verification Checklist remains mandatory; periodic synthetic "dummy audit" tickets are injected to monitor operator attention.

---

## 6. Rollback & Ethical Stop Rules

The experiment will be paused immediately if:
1. High-priority recall drops below **98.0%** in any 24-hour evaluation window.
2. Misrouted package rate exceeds **4.0%** over a 48-hour rolling window.
3. Associate reported fatigue or system failure causes line-haul dispatch delay.
