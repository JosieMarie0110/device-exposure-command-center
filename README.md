### Project Status
Actively under development

# Device Exposure Command Center

**Device Exposure Command Center** is an interactive simulation platform designed to model how modern security teams identify, analyze, and respond to device exposure across complex environments.

Inspired by platforms like Forescout and Armis, this project focuses on **asset visibility, classification, and risk-driven decision making**, translating raw telemetry into actionable security insights.

---

## What It Does

The application simulates how different discovery methods surface device data and exposes key risk indicators across an environment.

It enables users to:

- Analyze device visibility across simulated environments  
- Identify unmanaged assets and ownership gaps  
- Evaluate risk signals and exposure patterns  
- Generate executive-level summaries and priority actions  
- Map findings to business outcomes and operational impact  

---

## Key Concepts Modeled

- **Unmanaged Asset Discovery** – Identifying devices outside traditional control planes  
- **Ownership Attribution Gaps** – Highlighting devices without clear accountability  
- **Risk Signal Analysis** – Prioritizing high-risk and critical assets  
- **Discovery Method Context** – Understanding how visibility changes based on telemetry source  
- **Exposure-Driven Workflows** – Connecting technical findings to remediation and governance actions  

---

## How It Works

1. Select a **scenario** representing a simulated environment  
2. Choose a **discovery source** (e.g., SPAN, DHCP, EDR)  
3. Run analysis to simulate device ingestion and scoring  
4. Review:
   - Exposure Overview  
   - Priority Actions  
   - Device Exposure Signals  
   - Asset Intelligence Table  
   - Business Outcome Mapping  

---

## Discovery-Aware Analysis

A key feature of this project is its ability to contextualize findings based on the selected discovery method.

Each discovery source includes:

- How the data is collected  
- Strengths in visibility and coverage  
- Known blind spots or limitations  
- Impact on exposure analysis  

This mirrors how real-world platforms evaluate **visibility gaps and telemetry bias**.

---

## Example Outputs

- **Exposure Overview**  
  Dynamic summary based on asset counts, unmanaged devices, ownership gaps, and risk levels  

- **Priority Actions**  
  Data-driven recommendations based on current exposure signals  

- **Device Exposure Signals**  
  Visual breakdown of asset distribution and risk indicators  

- **Business Outcome Mapping**  
  Translation of technical findings into measurable business impact  

---

## Why This Project

Security teams often struggle to connect **technical telemetry** with **business impact and decision-making**.

This project was built to explore how:

- Raw device data can be transformed into **structured insights**  
- Visibility gaps can be clearly communicated  
- Security findings can be aligned to **business outcomes and stakeholder priorities**  

---

## Design Philosophy

- **Signal → Insight → Action → Outcome**
- Separate **data logic** from **presentation layers**
- Emphasize **context over raw data**
- Simulate real-world **security + customer success workflows**

---

## Tech Stack

- Python  
- Pandas (data processing)  
- Gradio (interactive UI)  
- Matplotlib (visualization)  

---

## Status

Active development — continuously improving:

- Dynamic analysis logic  
- UI/UX and visualization  
- Scenario realism and data modeling  
- AI-assisted insights and recommendations  

 Strategic decision-making  

---

## Related Projects

- **CS Brain** – AI-powered Customer Success strategy assistant  
- **Business Outcomes Mapper** – Value alignment and stakeholder mapping tool  

---

## Future Enhancements

- Discovery-specific action recommendations  
- Risk scoring improvements  
- Scenario customization  
- AI-driven insights and pattern detection  
- Expanded integrations and data sources  

---
