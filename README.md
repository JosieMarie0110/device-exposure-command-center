### Project Status
Actively under development

## Device Exposure Command Center

An interactive simulation platform for modeling how security teams identify, classify, and respond to device exposure.

Inspired by platforms like Forescout and Armis, it focuses on agentless visibility, multi-source discovery, and risk-based prioritization.

---

## Overview

Simulates how device data is discovered, analyzed, and translated into actionable insights.

Helps answer:
- What devices exist?  
- Which are unmanaged or risky?  
- Where are ownership gaps?  
- What actions should be prioritized?  

---

## What It Does

- Analyze device visibility across environments  
- Identify unmanaged assets and ownership gaps  
- Evaluate risk signals and exposure patterns  
- Generate priority actions and summaries  
- Map findings to business impact  

---

## Key Concepts

- **Unmanaged Discovery** — devices outside control  
- **Ownership Gaps** — no clear accountability  
- **Risk Signals** — prioritizing critical assets  
- **Discovery Context** — visibility varies by source  
- **Exposure Workflows** — from finding → action  

---

## How It Works

1. Select a scenario  
2. Choose a discovery source (SPAN, DHCP, EDR)  
3. Run analysis  

Outputs:
- Exposure overview  
- Priority actions  
- Device exposure signals  
- Asset intelligence  
- Business impact mapping  

---

## Discovery-Aware Analysis

Each discovery method includes:
- Data collection method  
- Visibility strengths  
- Known blind spots  
- Impact on analysis  

Reflects real-world telemetry limitations and bias.

---

## Why It Matters

Security teams struggle to connect telemetry to decisions.

This project focuses on:
- Turning device data into actionable insight  
- Highlighting visibility gaps  
- Aligning technical findings to business outcomes  

---

## Design Philosophy

- Signal → Insight → Action → Outcome  
- Context over raw data  
- Separate data and presentation layers  
- Model real-world security + CS workflows  

---

## Tech Stack

- Python  
- Pandas  
- Gradio  
- Matplotlib  

---

## Status

Active development:
- Improved analysis logic  
- UI/UX enhancements  
- More realistic scenarios  
- AI-assisted insights  

---

## Future Enhancements

- Discovery-based recommendations  
- Improved risk scoring  
- Scenario customization  
- Expanded data sources  
