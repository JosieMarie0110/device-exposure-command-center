### Project Status
Actively under development

# Device Exposure Command Center 

A lightweight simulation that demonstrates how asset visibility platforms identify devices on a network, classify them, and surface potential exposure risks.

This project was created as part of my technical portfolio to explore how network telemetry and infrastructure signals can be translated into meaningful security insights and executive-level summaries.

---

## Overview

Modern organizations often struggle with a fundamental security question:

**What devices actually exist on the network?**

Asset visibility and exposure management platforms help answer that question by collecting telemetry from network infrastructure, analyzing traffic patterns, and enriching device information with contextual signals.

The **Forescout Exposure Simulator** models a simplified version of that workflow.

The application allows a user to:

- Select a **network scenario**
- Choose a **discovery context**
- Simulate device discovery and classification
- Generate an **exposure summary**
- Produce **recommended remediation actions**
- Visualize device exposure and risk distribution

The goal of this project is not to replicate a full security platform, but to demonstrate how asset visibility and exposure insights can be communicated clearly and effectively.

---

## Why I Built This

In many organizations, security teams struggle with visibility into unmanaged or unknown devices. These devices can include:

- IoT devices
- medical equipment (IoMT)
- OT / manufacturing systems
- unmanaged laptops or shadow IT assets

Without visibility, these assets can introduce risk that security teams cannot easily detect or prioritize.

I built this project to simulate the workflow that exposure management platforms provide — taking raw signals from infrastructure and translating them into meaningful insights and actionable guidance.

---

<img width="943" height="1235" alt="image" src="https://github.com/user-attachments/assets/57573166-6e05-42ee-a554-8215d3876140" />

## Key Features

**Scenario-Based Simulation**

The application includes multiple network environments to simulate different operational contexts.

Examples include:

- Corporate IT environments  
- Healthcare / IoMT networks  
- Manufacturing / OT environments  
- Distributed branch office networks  

---

**Discovery Context Selection**

Different telemetry sources may be used to discover assets on a network.

Examples include:

- Passive network monitoring
- Mirrored traffic (SPAN / TAP)
- Infrastructure telemetry
- Endpoint enrichment sources

The simulator allows the user to select the discovery source to illustrate how asset intelligence platforms gather device information.

---

**Executive Summary**

After the simulation runs, the application generates a concise summary of the environment and potential exposure risks.

This models how security teams often need to translate technical findings into leadership-ready communication.

---

**Recommended Actions**

The application also generates recommended next steps to address potential exposure risks, such as:

- investigating unmanaged devices
- reviewing segmentation policies
- validating asset ownership
- confirming monitoring coverage

---

**Exposure Visualization**

The simulation provides a basic visualization of discovered assets and their associated risk levels.

---

**Exposure Details Table**

A table view provides device-level context that could support deeper analysis by security or operations teams.

---

## Technology Stack

This project was built using:

- **Python**
- **Gradio** for the user interface
- **Pandas** for data handling
- **Plotly** for simple visualization

The goal was to keep the implementation lightweight while still providing an interactive demonstration of exposure analysis concepts.

---

## Project Structure


```
forescout-exposure-simulator
│
├── app.py
├── analyzer.py
├── scoring.py
├── sample_data.py
├── requirements.txt
└── README.md
```

