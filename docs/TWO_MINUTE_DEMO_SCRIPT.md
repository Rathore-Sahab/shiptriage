# ShipTriage — Two-Minute Product Demo Script

**Speaker:** Product Manager / Candidate  
**Target Audience:** Google APM Hiring Managers, Tech Leads, and Cross-Functional Interviewers  
**Duration:** Exactly 2 Minutes (120 Seconds)  
**Live Demo URL:** [shiptriage.streamlit.app](https://shiptriage-dtvzbqvymfb9mfzetgx3nq.streamlit.app/)  

---

## Demo Timing & Narrative Arc

```text
[0:00] ─── Problem & Operational Hook ───► [0:20]
[0:20] ─── Core Product: Single Triage ──► [0:45]
[0:45] ─── Uncertainty & Safety Gate ────► [1:10]
[1:10] ─── Learning From Failure & ML ───► [1:40]
[1:40] ─── Bulk Operations & APM Vision ─► [2:00]
```

---

### Segment 1: The Problem & The Operational Hook (0:00 – 0:20)
*Action: Display the ShipTriage Overview page on screen.*

> **Spoken:**  
> "In high-velocity warehouse fulfillment, shipment exceptions—like crushed cartons, unmapped barcodes, and line-haul delays—arrive as messy, free-text notes across dock terminals.
> 
> Associates like Ramesh spend up to two minutes per ticket manually deciphering what went wrong, whether an SLA breach is imminent, and where to route the parcel. Under pressure, high-priority orders get buried and packages get misrouted."

---

### Segment 2: Single Ticket Triage in Action (0:20 – 0:45)
*Action: Click 'Single triage' in navigation. Select 'Quick-load sample scenario' $\to$ 'Damaged Parcel'. Click 'Triage Exception'.*

> **Spoken:**  
> "I built ShipTriage to turn that unstructured note into instant, structured decision support.
> 
> Within milliseconds, ShipTriage predicts the issue category, assigns an urgency priority, surfaces the exact text signals behind the prediction, and provides a conservative standard operating procedure prompt. 
> 
> Crucially, look at this badge: it tells the associate whether the prediction came from a high-precision keyword rule or our statistical ML model."

---

### Segment 3: Uncertainty Management & Dynamic Threshold (0:45 – 1:10)
*Action: Point to the 'Triage Status' card (showing 'Above Threshold'). Move the 'Manual-review threshold' slider in the sidebar from 60% to 85%. Watch the status pill instantly flip to 'Review Required'. Check one box on the Human Verification Checklist.*

> **Spoken:**  
> "As a PM, my core principle is that software in physical operations must never be an overconfident black box.
> 
> In the sidebar, I can tune our operational review threshold. When I raise it to 85%, the system immediately recalculates against the active threshold and routes the ticket to the Human Review Queue. 
> 
> We never take autonomous shipment actions: our interactive checklist ensures an associate verifies the physical barcode and package seal before proceeding."

---

### Segment 4: Learning From Failure & The Hybrid Pivot (1:10 – 1:40)
*Action: Navigate to 'Model insights'. Scroll to the 'Why Did Keyword Rules Outperform ML?' panel and the comparison table.*

> **Spoken:**  
> "My most valuable product learning came from a failure. When I evaluated our model using a template-group holdout to prevent data leakage, a simple keyword baseline beat our machine learning model—100% to 78.5%.
> 
> ML had developed an acute blind spot, misclassifying every delayed shipment as 'missing' due to shared tracking vocabulary.
> 
> Instead of forcing a complex neural net, I designed a Hybrid Architecture: domain rules act as a first line of defense, while ML serves as a fallback for colloquial phrasing. That hybrid model delivered 100% holdout accuracy and 90% on unseen phrasing."

---

### Segment 5: Shift-Level Batch Triage & North Star Vision (1:40 – 2:00)
*Action: Navigate to 'Batch triage'. Upload the sample CSV. Click 'Review required queue' filter.*

> **Spoken:**  
> "For shift supervisors, our Batch Triage in-memory workflow processes 1,000 tickets in under two seconds, letting them filter the review queue first and export enriched manifests.
> 
> Our proposed North Star Metric is **Median Time to Initial Triage Decision**, aiming to cut triage from 120 seconds to under 35 seconds while keeping high-priority recall at 99%. 
> 
> ShipTriage proves how I approach product: start with the worker on the floor, respect data over hype, and build AI that humans can genuinely trust."

---

## Pro-Tips for Delivering this Demo in an Interview
1. **Pacing:** Speak at an energetic, conversational pace (approx. 140 words per minute).
2. **Cursor Control:** Move your cursor deliberately to highlight the exact visual cards you are discussing.
3. **Emphasize the Failure:** Interviewers love Segment 4 (the ML blindspot). Highlight it as proof of your analytical rigor, intellectual humility, and bias toward the simplest working solution.
