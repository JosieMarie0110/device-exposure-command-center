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

APP_TITLE = "EXPOSURE COMMAND CENTER"
APP_SUBTITLE = "Simulate device visibility, unmanaged asset exposure, and risk-driven security posture analysis."

SCENARIO_PLACEHOLDER = "Select a network scenario"
DISCOVERY_PLACEHOLDER = "Select a discovery context"


def scenario_choices():
    return [SCENARIO_PLACEHOLDER] + get_scenario_names()


def discovery_choices():
    return [DISCOVERY_PLACEHOLDER] + DISCOVERY_SOURCES


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
    base = [
        "**Network Scenario**",
        "Select a sample environment to simulate the types of assets, locations, and management patterns present on the network.",
        "",
        "**Discovery Context**",
        "Select the telemetry source used to simulate how assets are discovered and enriched during analysis.",
    ]

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

    if discovery and discovery != DISCOVERY_PLACEHOLDER:
        base.extend(["", f"**Selected Discovery Source:** {discovery}"])

    return "\n".join(base)


def pick_risk_column(df: pd.DataFrame):
    candidates = ["risk", "risk_level", "severity", "exposure", "priority"]
    lower_map = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def build_visualization_html(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return """
        <div style="padding:12px; color:#183b67; font-size:13px;">
            No exposure visualization available yet. Run a simulation to populate results.
        </div>
        """

    risk_col = pick_risk_column(df)

    if risk_col is None:
        return f"""
        <div style="padding:12px; color:#183b67; font-size:13px;">
            Devices analyzed: <strong>{len(df)}</strong><br><br>
            Risk distribution was not available in the returned data.
        </div>
        """

    counts = df[risk_col].fillna("Unknown").astype(str).value_counts().to_dict()
    ordered = ["Low", "Medium", "High", "Critical", "Unknown"]
    total = max(sum(counts.values()), 1)

    rows = []
    for level in ordered:
        value = counts.get(level, 0)
        pct = int((value / total) * 100) if total else 0

        rows.append(f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#17365f; font-weight:600; font-size:12px;">
                <span>{html.escape(level)}</span>
                <span>{value}</span>
            </div>
            <div style="width:100%; height:10px; background:#e7eef8; border-radius:999px; overflow:hidden;">
                <div style="height:10px; width:{pct}%; background:linear-gradient(90deg,#6e7df7,#8d66ff); border-radius:999px;"></div>
            </div>
        </div>
        """)

    return f"""
    <div style="padding:10px;">
        <div style="font-size:14px; font-weight:700; color:#17365f; margin-bottom:10px;">
            Exposure by Risk Level
        </div>
        {''.join(rows)}
    </div>
    """


def build_exposure_details(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "No exposure details available."

    preview = df.copy()

    if len(preview.columns) > 8:
        preview = preview.iloc[:, :8]

    try:
        table_md = preview.to_markdown(index=False)
    except Exception:
        table_md = preview.to_string(index=False)

    return f"""### Exposure Details

**Devices analyzed:** {len(df)}

{table_md}
"""


def extract_analyzer_input(scenario_name: str):
    scenario_data = get_scenario_data(scenario_name)

    if scenario_data is None:
        return ""

    if isinstance(scenario_data, str):
        return scenario_data

    if isinstance(scenario_data, list):
        return scenario_data

    if isinstance(scenario_data, dict):
        for key in [
            "telemetry",
            "telemetry_input",
            "raw_text",
            "network_data",
            "sample_input",
            "input_text",
            "device_data",
            "devices",
            "records",
            "assets",
            "data",
        ]:
            value = scenario_data.get(key)
            if value:
                return value

    return scenario_name


def run_exposure_analysis(scenario: str, discovery: str):
    context_text = build_context_text(scenario, discovery)

    if not scenario or scenario == SCENARIO_PLACEHOLDER:
        msg = "Please select a network scenario."
        return msg, msg, build_visualization_html(pd.DataFrame()), "No exposure details available.", context_text

    if not discovery or discovery == DISCOVERY_PLACEHOLDER:
        msg = "Please select a discovery context."
        return msg, msg, build_visualization_html(pd.DataFrame()), "No exposure details available.", context_text

    try:
        analyzer_input = extract_analyzer_input(scenario)

        # analyzer.py only accepts ONE argument
        raw_result = analyze_text_input(analyzer_input)

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
    max-width: 1280px !important;
    margin: 0 auto !important;
    padding: 12px !important;
}

#hero-shell {
    background: #f3f7fc;
    border: 1px solid #d8e4f5;
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

#hero-title {
    color: #17365f;
    margin: 0 0 4px 0;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 0.2px;
}

#hero-subtitle {
    color: #506b8c;
    margin: 0;
    font-size: 12px;
    line-height: 1.35;
}

.panel,
.result-card,
.context-card,
.details-card {
    background: #f7f9fc !important;
    border: 1px solid #d9e7fb !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08) !important;
    padding: 10px !important;
}

.section-title-dark {
    color: #17365f;
    font-weight: 800;
    font-size: 14px;
    margin-bottom: 8px;
}

.gradio-container .gr-dropdown .wrap,
.gradio-container .gr-textbox,
.gradio-container .gr-textbox textarea {
    border: 1.5px solid #c8d8ee !important;
    border-radius: 10px !important;
    min-height: 40px !important;
    box-shadow: none !important;
    font-size: 13px !important;
}

.gradio-container .gr-dropdown .wrap:hover {
    border-color: #7a9be8 !important;
}

.gr-button {
    background: linear-gradient(90deg, #1e64c8, #0c56bb) !important;
    color: white !important;
    border: 1px solid #0f4ea5 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    min-height: 40px !important;
    padding: 8px 12px !important;
    box-shadow: none !important;
}

.gr-button:hover {
    filter: brightness(1.04);
}

.compact-markdown p,
.compact-markdown li {
    font-size: 12px !important;
    line-height: 1.4 !important;
    margin-bottom: 4px !important;
}

.compact-markdown h1,
.compact-markdown h2,
.compact-markdown h3,
.compact-markdown h4 {
    font-size: 14px !important;
    margin-bottom: 6px !important;
}

.details-card table {
    font-size: 12px !important;
}

.details-card th,
.details-card td {
    padding: 6px 8px !important;
}

footer {
    display: none !important;
}
"""


with gr.Blocks(css=CUSTOM_CSS, theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        f"""
        <div id="hero-shell">
            <h1 id="hero-title">{APP_TITLE}</h1>
            <div id="hero-subtitle">{APP_SUBTITLE}</div>
        </div>
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

                run_button = gr.Button("Analyze Exposure")

        with gr.Column(scale=2):
            with gr.Column(elem_classes=["context-card", "compact-markdown"]):
                gr.Markdown('<div class="section-title-dark">Network Configuration Context</div>')
                context_box = gr.Markdown(
                    value=build_context_text(SCENARIO_PLACEHOLDER, DISCOVERY_PLACEHOLDER)
                )

    with gr.Row(equal_height=True):
        with gr.Column(scale=1, elem_classes=["result-card", "compact-markdown"]):
            gr.Markdown('<div class="section-title-dark">Executive Summary</div>')
            summary_box = gr.Markdown()

        with gr.Column(scale=1, elem_classes=["result-card", "compact-markdown"]):
            gr.Markdown('<div class="section-title-dark">Recommended Actions</div>')
            actions_box = gr.Markdown()

    with gr.Row():
        with gr.Column(elem_classes=["details-card"]):
            gr.Markdown('<div class="section-title-dark">Exposure Visualization</div>')
            visualization_box = gr.HTML(
                value=build_visualization_html(pd.DataFrame())
            )

    with gr.Row():
        with gr.Column(elem_classes=["details-card", "compact-markdown"]):
            gr.Markdown('<div class="section-title-dark">Exposure Details</div>')
            exposure_details = gr.Markdown(value="No exposure details available.")

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
