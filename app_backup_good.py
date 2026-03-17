import gradio as gr
import pandas as pd

from analyzer import analyze_text_input
from scoring import score_devices, generate_executive_summary
from sample_data import (
    get_scenario_names,
    get_scenario_data,
    get_default_scenario,
    DISCOVERY_SOURCES,
    ENVIRONMENT_PROFILES,
)


def load_scenario(name):
    return get_scenario_data(name)


def build_metrics_html(scored_devices):

    total_assets = len(scored_devices)

    unmanaged_assets = sum(
        1 for d in scored_devices if d.get("managed", "").lower() == "no"
    )

    unknown_assets = sum(
        1
        for d in scored_devices
        if d.get("asset_type", "").lower() == "unknown asset"
        or d.get("owner", "").lower() == "unknown"
    )

    high_risk_assets = sum(
        1 for d in scored_devices if d.get("risk_level", "") in ["High", "Critical"]
    )

    card = """
        background:white;
        border-radius:12px;
        padding:16px;
        border:1px solid #d8e6f3;
        text-align:center;
        box-shadow:0 2px 8px rgba(0,0,0,0.04);
    """

    html = f"""
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:12px;">
        <div style="{card}">
            <div style="font-size:28px;font-weight:700;color:#174f84">{total_assets}</div>
            <div>Total Assets</div>
        </div>
        <div style="{card}">
            <div style="font-size:28px;font-weight:700;color:#174f84">{unmanaged_assets}</div>
            <div>Unmanaged</div>
        </div>
        <div style="{card}">
            <div style="font-size:28px;font-weight:700;color:#174f84">{unknown_assets}</div>
            <div>Unknown Ownership</div>
        </div>
        <div style="{card}">
            <div style="font-size:28px;font-weight:700;color:#174f84">{high_risk_assets}</div>
            <div>High / Critical Risk</div>
        </div>
    </div>
    """

    return html


def run_analysis(telemetry, discovery_source, environment):

    analyzed = analyze_text_input(telemetry)

    scored = score_devices(analyzed, environment)

    df = pd.DataFrame(scored)

    if not df.empty:

        display_columns = [
            "hostname",
            "ip",
            "asset_type",
            "confidence",
            "managed",
            "owner",
            "location",
            "risk_score",
            "risk_level",
            "recommended_action",
        ]

        df = df[display_columns]

        df = df.sort_values(
            by=["risk_score", "confidence"], ascending=[False, False]
        ).reset_index(drop=True)

    summary = generate_executive_summary(scored)

    metrics_html = build_metrics_html(scored)

    return df, summary, metrics_html


title_html = """
# Exposure Command Center
### Forescout-Inspired Asset Discovery & Risk Simulator
"""


with gr.Blocks(theme=gr.themes.Soft()) as demo:

    gr.Markdown(title_html)

    # TOP SECTION
    with gr.Row():

        with gr.Column(scale=1):

            scenario_dropdown = gr.Dropdown(
                choices=get_scenario_names(),
                label="Example Environment",
                value=get_scenario_names()[0],
            )

            load_button = gr.Button("Load Scenario")

            discovery_source = gr.Dropdown(
                choices=DISCOVERY_SOURCES,
                label="Discovery Source",
                value=DISCOVERY_SOURCES[0],
            )

            environment_dropdown = gr.Dropdown(
                choices=ENVIRONMENT_PROFILES,
                label="Environment Profile",
                value=ENVIRONMENT_PROFILES[0],
            )

            analyze_button = gr.Button("Analyze Exposure")

        with gr.Column(scale=2):

            telemetry_input = gr.Textbox(
                label="Network Telemetry Input",
                value=get_default_scenario(),
                lines=12,
            )

    metrics_html = gr.HTML()

    executive_summary = gr.Textbox(
        label="Executive Summary",
        lines=6,
    )

    # BOTTOM SECTION (FULL WIDTH)
    gr.Markdown("## Device Exposure Analysis")

    results_table = gr.Dataframe(
        headers=[
            "hostname",
            "ip",
            "asset_type",
            "confidence",
            "managed",
            "owner",
            "location",
            "risk_score",
            "risk_level",
            "recommended_action",
        ],
        wrap=True,
        interactive=False,
    )

    load_button.click(
        fn=load_scenario,
        inputs=scenario_dropdown,
        outputs=telemetry_input,
    )

    analyze_button.click(
        fn=run_analysis,
        inputs=[telemetry_input, discovery_source, environment_dropdown],
        outputs=[results_table, executive_summary, metrics_html],
    )


if __name__ == "__main__":
    demo.launch()
