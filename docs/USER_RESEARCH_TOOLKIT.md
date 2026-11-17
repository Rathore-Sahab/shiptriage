# ShipTriage — User Research & Validation Toolkit

**Purpose:** Comprehensive field research, discovery interview, and usability testing framework for warehouse operations.  
**Target Sample:** 5–8 consenting logistics and warehouse professionals (shift associates, inventory leads, facility supervisors).  
**Compliance Guardrail:** No confidential company data, live tracking numbers, or internal credentials are to be requested or recorded. All participation is strictly voluntary and anonymized.  
**Validation Status:** Planned toolkit; pending execution upon participant recruitment.

---

## 1. Interview Protocol: Warehouse Issue-Resolution Associates

**Objective:** Understand the cognitive workflow, time constraints, and pain points of associates handling physical shipment exceptions.

### Introduction & Consent (3 mins)
- *"Thank you for taking time to speak with me. I am researching how warehouse teams interpret and resolve shipment exception notes (damaged parcels, missing items, unmapped barcodes). We are testing a prototype concept designed to assist—not replace—associates. We will not record any company confidential data, tracking numbers, or customer details. Is it okay if I take anonymous notes?"*

### Warm-up & Context (5 mins)
1. Walk me through your typical shift. At what point do you interact with shipment exceptions?
2. Approximately how many exception packages or tickets do you personally review in a single shift?
3. Where do these tickets come from (dock de-stuffing, sorter reject bins, customer escalations, or driver returns)?

### Deep Dive: Reading & Triage Workflow (15 mins)
4. When you open an exception note, what are the first 2 or 3 pieces of information your eyes look for?
5. How do you distinguish between a package that is genuinely *missing* versus one that is simply *delayed in transit*?
6. How do you determine urgency? What makes an issue "high priority" in your facility?
7. How often is the ticket description vague, incomplete, or confusing? What do you do when a description doesn't make sense?
8. When you decide on a next step, do you rely on memory, a written SOP manual, or an informal consensus with senior teammates?

### Pain Points & Edge Cases (10 mins)
9. What is the most frustrating part of resolving exceptions during a peak shift?
10. Have you ever misrouted a package because the initial note was misleading? What happened?
11. If an AI tool suggested a category and priority for a ticket, what would make you trust it? What would make you distrust it?

---

## 2. Interview Protocol: Logistics Hub Operations Leads

**Objective:** Understand shift-level SLA monitoring, escalation bottlenecks, and reporting needs.

1. What are your facility’s primary KPIs regarding shipment exceptions (e.g. line-haul cutoff adherence, DPU, dock-to-stock time)?
2. How do you currently monitor whether associates are prioritizing SLA-breached shipments over routine exceptions?
3. What percentage of exception tickets typically require cross-hub escalation or manual investigation?
4. How do you handle shifts where exception volume spikes unexpectedly (e.g. rainy season carton damage, festival sales)?
5. What guardrails would you demand before allowing an AI decision-support tool into your associates' daily workflow?

---

## 3. Problem Discovery Questionnaire (Pre-Interview Survey)

*Format: 5-point Likert scale (1 = Strongly Disagree, 5 = Strongly Agree)*

1. [ ] I spend too much time reading and interpreting vague ticket notes before taking physical action.
2. [ ] Our team has inconsistent definitions of what qualifies as an urgent exception.
3. [ ] Delayed shipments and missing shipments frequently get confused in our initial logging.
4. [ ] I feel confident that our current process never misses an SLA-critical customer escalation.
5. [ ] I would find it valuable to have an immediate suggestion of the standard operating procedure next step.
6. [ ] I would prefer an AI tool that admits when it is uncertain rather than guessing a category.

---

## 4. Operational Workflow Mapping Template

Map the participant's current journey against the proposed ShipTriage-assisted journey:

| Stage | Current As-Is Manual Process | Pain Point / Friction | ShipTriage Assisted Process | Expected Impact |
|---|---|---|---|---|
| **1. Intake** | Read unstructured text note in dock terminal. | Non-standard acronyms, typos, varying detail. | Ingest text; normalize formatting. | Standardized presentation. |
| **2. Categorization** | Associate mental lookup; assigns class manually. | Inconsistent tags; delayed vs missing confusion. | Hybrid Engine suggests category + strategy tag. | Immediate structured baseline. |
| **3. Prioritization** | Scan text for dates/times; estimate SLA urgency. | High-priority tickets missed in large queues. | Logistic Regression flags urgency + signals. | High-priority recall $\ge 99\%$. |
| **4. Uncertainty Gate** | Unsure associate asks supervisor or guesses. | Supervisor bottleneck; silent errors. | Dynamic Threshold routes to Review Queue. | Explicit review of low-score tickets. |
| **5. Action Execution** | Look up SOP or remember from experience. | Inconsistent claim logging; missed audits. | Pre-populated SOP prompt + verification checklist. | Standardized compliance & safety. |

---

## 5. Usability Testing Script (Think-Aloud Protocol)

**Participant:** Warehouse Associate / Logistics Professional  
**Facilitator:** APM Researcher  
**Prototype URL:** Local or hosted ShipTriage instance  

### Task 1: Single Ticket Triage (5 mins)
- **Prompt:** *"Imagine you are working the morning inbound shift. You receive the following note from the sorting deck: 'Tracking has no arrival scan after dispatch from Pune; package not in destination cage and delivery is due today.' Please use ShipTriage to triage this ticket."*
- **Observer Checkpoints:**
  - Does the user understand the category suggestion?
  - Does the user notice the suggested priority and urgency signal?
  - Does the user review the "Suggested Next Action" prompt?
  - Does the user interact with the Human Verification Checklist?
- **Prompt for Feedback:** *"What does the 'Model decision score' mean to you? How confident do you feel acting on this suggestion?"*

### Task 2: Testing Threshold Dynamics (5 mins)
- **Prompt:** *"Now look at the sidebar slider called 'Manual-review threshold'. Currently it is at 60%. Move it to 85%. What changed on your screen? Why do you think that happened?"*
- **Observer Checkpoints:**
  - Does the user notice the status pill flip from "Above Threshold" to "Review Required"?
  - Does the user understand that the higher threshold demands higher certainty?

### Task 3: Shift Batch Processing (5 mins)
- **Prompt:** *"You have just received an export of 4 exception tickets from the shift handoff. Use the Batch Triage tab to process them, filter out the review queue, and download the results."*
- **Observer Checkpoints:**
  - Can the user upload the CSV without guidance?
  - Does the user navigate the summary metrics (Total, Review Queue, High Priority)?
  - Does the user apply the filter to inspect the "Review required queue"?

---

## 6. Experiment Tracking Sheet (Cohort Pilot Template)

| Participant ID | Role & Experience | Task 1 Time (s) | Task 1 Outcome | Task 2 Comprehension | Task 3 Time (s) | Override? (Y/N) | User Trust Score (1-5) | Qualitative Notes |
|---|---|---|---|---|---|---|---|---|
| **P-01** | Associate (2 yrs) | [ ] | Success / Fail | Understood / Confused | [ ] | [ ] | [ ] | |
| **P-02** | Associate (6 mos) | [ ] | Success / Fail | Understood / Confused | [ ] | [ ] | [ ] | |
| **P-03** | Inventory Lead (4 yrs) | [ ] | Success / Fail | Understood / Confused | [ ] | [ ] | [ ] | |
| **P-04** | Associate (1 yr) | [ ] | Success / Fail | Understood / Confused | [ ] | [ ] | [ ] | |
| **P-05** | Hub Supervisor (5 yrs) | [ ] | Success / Fail | Understood / Confused | [ ] | [ ] | [ ] | |

---

## 7. Feedback Analysis & Synthesis Framework

Categorize interview and usability test findings into the Google APM Product Matrix:

1. **User Empathy & Ergonomics:**
   - Was the interface readable on warehouse displays under ambient industrial lighting?
   - Did associates find the 4-step checklist helpful or burdensome?
2. **Model Transparency & Trust:**
   - Did users understand that scores are not guaranteed probabilities?
   - Did associates trust the keyword rules more than the statistical ML?
3. **Safety & Guardrail Compliance:**
   - Did any associate attempt to use the tool to automatically close or refund a shipment?
   - Did the manual-review threshold catch the user's ambiguous cases?
4. **Roadmap Prioritization Inputs:**
   - Which suggested feature was requested most frequently (e.g. barcode scanner integration, voice-to-text ticket logging, or multi-language support)?
