# ShipTriage — Resume & Portfolio Descriptions

**Purpose:** Ready-to-use resume bullets, portfolio summaries, and LinkedIn project entries highlighting product management, technical leadership, and supply chain domain expertise.

---

## 1. Resume Bullet Points (Tailored for Google APM & Tech PM Roles)

### Option A: Standard Google APM Bullet Style (XYZ Format: "Accomplished [X], as measured by [Y], by doing [Z]")
- **Product Architecture & Strategy:** Spearheaded product discovery and architecture for **ShipTriage**, a human-in-the-loop ML decision platform targeting a 70% reduction in warehouse exception triage latency (120s $\to$ <35s) across 5 core failure modes.
- **Data-Driven Pivot & Machine Learning:** Diagnosed a 0.0% recall failure mode on delayed shipments where pure TF-IDF + Logistic Regression was outperformed by domain rules; engineered a **Hybrid Rules + ML Fallback Engine** that boosted challenge accuracy from 60% to 90% and holdout accuracy to 100%.
- **Safety & Guardrail Design:** Established an operational uncertainty framework with a dynamic review threshold (0.40–0.90) and human verification checklist, ensuring zero autonomous shipment modifications and a projected $\ge 99.0\%$ high-priority recall guardrail.
- **Product Delivery & Testing:** Delivered an end-to-end Python/Streamlit prototype featuring sub-5ms local inference, in-memory shift batch CSV ingestion (<2s for 1,000 rows), and an automated 17-test CI verification suite with zero cloud deployment dependencies.

### Option B: Concise 2-Line Resume Version (Space-Constrained)
- **ShipTriage — AI-Assisted Exception Triage Platform | Founder & Product Lead** *(Python, scikit-learn, Streamlit)*
  - Conceptualized and built an augmented triage platform for fulfillment hubs, defining a North Star Metric to cut median triage time from 120s to <35s while maintaining $\ge 99\%$ high-priority recall.
  - Architected a Hybrid Rules + ML engine that resolved an acute delayed-shipment blindspot, increasing generalization accuracy from 60% to 90% with dynamic threshold-gated human oversight.

---

## 2. LinkedIn Project Section

**Project Name:** ShipTriage — AI-Assisted Shipment Exception Intelligence  
**Role:** Product Manager & Technical Architect  
**Project URL:** [https://shiptriage-dtvzbqvymfb9mfzetgx3nq.streamlit.app/](https://shiptriage-dtvzbqvymfb9mfzetgx3nq.streamlit.app/)  
**Skills:** Product Requirements Document (PRD), Human-in-the-Loop AI, Supply Chain Operations, Machine Learning Evaluation, Metrics Frameworks, Rapid Prototyping (Python/Streamlit).  

**Description:**  
In high-velocity fulfillment logistics, warehouse associates spend up to two minutes per package deciphering unstructured, non-standardized exception notes (damaged cartons, unmapped AWBs, transit delays), risking SLA breaches and costly misroutes. 

Drawing from my MBA in Operations & Supply Chain Management and ML engineering background at IIT Mandi, I built ShipTriage:
- **Decision Support, Not Black-Box Automation:** Built an augmented triage workflow that predicts failure categories and urgency levels while enforcing physical verification checklists and zero autonomous shipment actions.
- **The Empirical Turnaround:** When template-group holdout evaluation revealed that keyword rules beat our pure ML model (100% vs 78.5%) due to delayed/missing vocabulary overlap, I designed a Hybrid Rules + ML Fallback engine that delivered 100% holdout accuracy and 90% challenge accuracy.
- **Dynamic Uncertainty Routing:** Engineered a real-time threshold gate that automatically diverts low-scoring or ambiguous tickets to human review queues.
- **Portfolio Deliverables:** Accompanied by a complete Google APM portfolio suite including PRD, Technical Architecture, Model Evaluation Report, User Research Toolkit (5–8 interview protocol), and Experimentation Plan.

---

## 3. Executive Elevator Summary (For Cover Letters & Networking)

> *"ShipTriage is a product portfolio project that showcases how I approach product management at the intersection of supply chain operations and machine learning. Inspired by actual warehouse floor realities, it structures free-text exception notes into actionable categories, urgency signals, and conservative SOP prompts. Rather than chasing AI complexity for its own sake, I used rigorous empirical testing to build a hybrid rules + ML architecture that prioritizes transparency, worker trust, and operational safety."*
