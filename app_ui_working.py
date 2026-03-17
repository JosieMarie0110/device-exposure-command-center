import html
import gradio as gr
import pandas as pd

from analyzer import analyze_text_input
from scoring import (
    score_devices,
    generate_executive_summary,
    generate_talking_points,
)
from sample_data import (
    get_scenario_names,
    get_scenario_data,
    DISCOVERY_SOURCES,
)

# =========================================================
# APP BRANDING
# Change these to whatever name you actually want
# =========================================================
APP_TITLE = "EXPOSURE COMMAND CENTER"
APP_SUBTITLE = "Simulate device visibility, unmanaged asset exposure, and risk-driven security posture analysis."

SCENARIO_PLACEHOLDER = "Select a network scenario"
DISCOVERY_PLACEHOLDER = "Select a discovery context"


def scenario_choices():
    return [SCENARIO_PLACEHOLDER] + get_scenario_names()


def discovery_choices():
    return [DISCOVERY_PLACEHOLDER] + DISCOVERY_SOURCES


def safe_text(value, fallback="Not available"):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def normalize_result_to_df(result):
    if isinstance(result, pd.DataFrame):
        return result

    if isinstance(result, list):
        if len(result) == 0:
            return pd.DataFrame()
        return pd.DataFrame(result)

    if isinstance(result, dict):
        if "devices" in result and isinstance(result["devices"], list):
            return pd.DataFrame(result["devices"])
        if "data" in result and isinstance(result["data"], list):
            return pd.DataFrame(result["data"])
        return pd.DataFrame([result])

    return pd.DataFrame()


def build_context_text(scenario: str, discovery: str) -> str:
    return """
**Network Scenario**

Select a sample environment to simulate the types of assets, locations, and management patterns present on the network. Examples may include corporate IT, healthcare / IoMT, manufacturing / OT, or branch office environments.

**Discovery Context**

Select the telemetry source used to simulate how assets are discovered and enriched during analysis. This may include passive network visibility, mirrored traffic, infrastructure data, or endpoint enrichment sources. The selected context helps explain how the platform is identifying devices and building exposure insights.
""".strip()    

    if scenario and scenario != SCENARIO_PLACEHOLDER:
        try:
            data = get_scenario_data(scenario)
            if isinstance(data, dict):
                description = data.get("description", "")
                network_notes = data.get("network_notes", "")
                device_notes = data.get("device_notes", "")

                if description:
                    base.extend(["", f"**Environment Overview:** {description}"])
                if network_notes:
                    base.extend(["", f"**Network Notes:** {network_notes}"])
                if device_notes:
                    base.extend(["", f"**Asset Notes:** {device_notes}"])
        except Exception:
            pass

    return "\n".join(base)


def pick_risk_column(df: pd.DataFrame):
    candidates = [
        "risk",
        "risk_level",
        "severity",
        "exposure",
        "priority",
    ]
    lower_map = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def build_visualization_html(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return """
        <div style="padding:18px; color:#183b67; font-size:16px;">
            No exposure visualization available yet. Run a simulation to populate results.
        </div>
        """

    risk_col = pick_risk_column(df)

    if risk_col is None:
        return f"""
        <div style="padding:18px; color:#183b67; font-size:16px;">
            Devices analyzed: <strong>{len(df)}</strong><br><br>
            Risk distribution was not available in the returned data.
        </div>
        """

    counts = (
        df[risk_col]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .to_dict()
    )

    ordered = ["Low", "Medium", "High", "Critical", "Unknown"]
    total = max(sum(counts.values()), 1)

    rows = []
    for level in ordered:
        value = counts.get(level, 0)
        pct = int((value / total) * 100) if total else 0

        rows.append(f"""
        <div style="margin-bottom:14px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#17365f; font-weight:600;">
                <span>{html.escape(level)}</span>
                <span>{value}</span>
            </div>
            <div style="width:100%; height:14px; background:#e7eef8; border-radius:999px; overflow:hidden;">
                <div style="height:14px; width:{pct}%; background:linear-gradient(90deg,#6e7df7,#8d66ff); border-radius:999px;"></div>
            </div>
        </div>
        """)

    return f"""
    <div style="padding:18px;">
        <div style="font-size:16px; font-weight:700; color:#17365f; margin-bottom:16px;">
            Exposure by Risk Level
        </div>
        {''.join(rows)}
    </div>
    """


def build_exposure_details(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "No exposure details available."

    preview = df.copy()

    if len(preview.columns) > 6:
        preview = preview.iloc[:, :6]

    try:
        table_md = preview.to_markdown(index=False)
    except Exception:
        table_md = preview.to_string(index=False)

    return f"""### Exposure Details

**Devices analyzed:** {len(df)}

{table_md}
"""

def run_exposure_analysis(scenario: str, discovery: str):
    context_text = build_context_text(scenario, discovery)

    if not scenario or scenario == SCENARIO_PLACEHOLDER:
        msg = "Please select a network scenario."
        return msg, msg, build_visualization_html(pd.DataFrame()), "No exposure details available.", context_text

    if not discovery or discovery == DISCOVERY_PLACEHOLDER:
        msg = "Please select a discovery context."
        return msg, msg, build_visualization_html(pd.DataFrame()), "No exposure details available.", context_text

    try:
        scenario_data = get_scenario_data(scenario)

        raw_text = ""

        if isinstance(scenario_data, str):
            raw_text = scenario_data

        elif isinstance(scenario_data, dict):
            raw_text = (
                scenario_data.get("raw_text")
                or scenario_data.get("device_text")
                or scenario_data.get("sample_data")
                or scenario_data.get("devices_text")
                or ""
            )

        if not raw_text:
            error_text = f"No device data found for scenario: {scenario}"
            return error_text, error_text, build_visualization_html(pd.DataFrame()), "No exposure details available.", context_text

        raw_result = analyze_text_input(raw_text)
        device_df = normalize_result_to_df(raw_result)

        try:
            scored_df = score_devices(device_df) if not device_df.empty else device_df
        except Exception:
            scored_df = device_df

        try:
            executive_summary = generate_executive_summary(scored_df)
        except Exception:
            executive_summary = (
                f"Simulation completed for **{scenario}** using **{discovery}**. "
                f"The environment should be reviewed for unmanaged assets, device posture gaps, and high-risk exposure areas."
            )

        try:
            actions = generate_talking_points(scored_df)
        except Exception:
            actions = "\n".join([
                "- Validate unmanaged and unknown device visibility",
                "- Prioritize high-risk device investigation",
                "- Confirm segmentation and access-control coverage",
                "- Review remediation ownership across security and infrastructure teams",
            ])

        viz_html = build_visualization_html(scored_df)
        details = build_exposure_details(scored_df)

        return executive_summary, actions, viz_html, details, context_text

    except Exception as e:
        error_text = f"Analysis error: {str(e)}"
        return error_text, error_text, build_visualization_html(pd.DataFrame()), "No exposure details available.", context_text


CUSTOM_CSS = """
body, .gradio-container {
    background: linear-gradient(90deg, #031326 0%, #041a34 50%, #031326 100%) !important;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
}

.gradio-container {
    max-width: 100% !important;
    padding: 18px !important;
}

/* Dropdown borders */
.gradio-container .gr-dropdown .wrap {
    border: 2px solid #3b6df6 !important;
    border-radius: 10px !important;
}

/* Dropdown hover */
.gradio-container .gr-dropdown .wrap:hover {
    border-color: #274ecf !important;
}

/* Button borders */
.gradio-container button {
    border: 2px solid #3b6df6 !important;
    border-radius: 10px !important;
}

/* Button hover */
.gradio-container button:hover {
    border-color: #274ecf !important;
}

/* Prevent blue overlay on focus */
.gradio-container .gr-dropdown:focus-within {
    background: transparent !important;
}


.gradio-container {
    max-width: 100% !important;
    padding: 18px !important;
}

#hero-title {
    text-align: center;
    color: #ffffff;
    margin-bottom: 4px;
    font-size: 46px;
    font-weight: 800;
}

#hero-subtitle {
    text-align: center;
    color: #d3e2ff;
    margin-bottom: 18px;
    font-size: 18px;
}

.panel,
.result-card,
.context-card,
.details-card {
    background: #f7f9fc !important;
    border: 1px solid #d9e7fb !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12) !important;
}

.panel,
.result-card,
.context-card,
.details-card {
    padding: 14px !important;
}

.section-title-dark {
    color: #17365f;
    font-weight: 800;
    font-size: 18px;
    margin-bottom: 8px;
}

.section-title-light {
    color: #ffffff;
    font-weight: 800;
    font-size: 18px;
    margin-bottom: 8px;
}

.gr-button {
    background: linear-gradient(90deg, #5b6df6, #6f5cff) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 18px !important;
    min-height: 52px !important;
}

.gr-button:hover {
    filter: brightness(1.05);
}

footer {
    display: none !important;
}
"""


with gr.Blocks(css=CUSTOM_CSS, theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        f"""
        <h1 id="hero-title">{APP_TITLE}</h1>
        <div id="hero-subtitle">{APP_SUBTITLE}</div>
        """
    )

    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            with gr.Column(elem_classes=["context-card"]):
                gr.Markdown('<div class="section-title-dark">Simulation Configuration</div>')

                scenario_dropdown = gr.Dropdown(
                    choices=scenario_choices(),
                    value=SCENARIO_PLACEHOLDER,
                    label=None,
                    interactive=True,
                    container=False,
                )

                discovery_dropdown = gr.Dropdown(
                    choices=discovery_choices(),
                    value=DISCOVERY_PLACEHOLDER,
                    label=None,
                    interactive=True,
                    container=False,
                )

                run_button = gr.Button("Launch Simulation")

        with gr.Column(scale=2, elem_classes=["context-card"]):
            gr.Markdown('<div class="section-title-dark">Network Configuration Context</div>')

            context_box = gr.Markdown(
                value=build_context_text(SCENARIO_PLACEHOLDER, DISCOVERY_PLACEHOLDER)
            )

    with gr.Row(equal_height=True):
        with gr.Column(scale=1, elem_classes=["result-card"]):
            gr.Markdown('<div class="section-title-dark">Executive Summary</div>')
            summary_box = gr.Markdown()

        with gr.Column(scale=1, elem_classes=["result-card"]):
            gr.Markdown('<div class="section-title-dark">Recommended Actions</div>')
            actions_box = gr.Markdown()

     with gr.Row():
         with gr.Column(elem_classes=["details-card"]):
         gr.Markdown('<div class="section-title-dark">Exposure Visualization</div>')
         exposure_chart = gr.Plot()

     with gr.Row():
         with gr.Column(elem_classes=["details-card"]):
         gr.Markdown('<div class="section-title-dark">Exposure Details</div>')
         exposure_table = gr.Dataframe(
             headers=[],
             datatype="str",
             row_count=(0, "dynamic"),
             col_count=(0, "dynamic"),
             interactive=False,
        ) 
            


    scenario_dropdown.change(
        fn=lambda scenario, discovery: build_context_text(scenario, discovery),
        inputs=[scenario_dropdown, discovery_dropdown],
        outputs=context_box,
    )

    discovery_dropdown.change(
        fn=lambda scenario, discovery: build_context_text(scenario, discovery),
        inputs=[scenario_dropdown, discovery_dropdown],
        outputs=context_box,
    )

    run_button.click(
        fn=run_exposure_analysis,
        inputs=[scenario_dropdown, discovery_dropdown],
        outputs=[
            summary_box,
            actions_box,
            visualization_box,
            exposure_details,
            context_box,
        ],
    )

if __name__ == "__main__":
    demo.launch()
