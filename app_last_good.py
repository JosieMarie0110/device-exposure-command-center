import html
import gradio as gr
import pandas as pd
import plotly.express as px

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
        border-radius:16px;
        padding:18px;
        border:1px solid #d8e6f3;
        text-align:center;
        box-shadow:0 2px 8px rgba(0,0,0,0.05);
    """

    html_output = f"""
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:14px;">
        <div style="{card}">
            <div style="font-size:30px;font-weight:800;color:#174f84;">{total_assets}</div>
            <div style="font-size:13px;color:#55708d;">Total Assets</div>
        </div>
        <div style="{card}">
            <div style="font-size:30px;font-weight:800;color:#174f84;">{unmanaged_assets}</div>
            <div style="font-size:13px;color:#55708d;">Unmanaged</div>
        </div>
        <div style="{card}">
            <div style="font-size:30px;font-weight:800;color:#174f84;">{unknown_assets}</div>
            <div style="font-size:13px;color:#55708d;">Unknown / Unattributed</div>
        </div>
        <div style="{card}">
            <div style="font-size:30px;font-weight:800;color:#174f84;">{high_risk_assets}</div>
            <div style="font-size:13px;color:#55708d;">High / Critical Risk</div>
        </div>
    </div>
    """
    return html_output


def risk_badge(level):
    level = (level or "").strip().lower()

    styles = {
        "critical": "background:#fde8e8; color:#b42318; border:1px solid #f5c2c7;",
        "high": "background:#fff1e6; color:#c2410c; border:1px solid #fed7aa;",
        "moderate": "background:#fff7db; color:#a16207; border:1px solid #fde68a;",
        "low": "background:#eafaf1; color:#166534; border:1px solid #bbf7d0;",
    }

    style = styles.get(
        level,
        "background:#eef2f7; color:#334155; border:1px solid #d7dde5;",
    )

    return f"""
    <span style="
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        font-size:12px;
        font-weight:700;
        {style}
    ">
        {html.escape(level.title() if level else 'Unknown')}
    </span>
    """


def managed_badge(value):
    value = (value or "").strip().lower()

    if value == "yes":
        style = "background:#eafaf1; color:#166534; border:1px solid #bbf7d0;"
        label = "Managed"
    else:
        style = "background:#fde8e8; color:#b42318; border:1px solid #f5c2c7;"
        label = "Unmanaged"

    return f"""
    <span style="
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        font-size:12px;
        font-weight:700;
        {style}
    ">
        {label}
    </span>
    """


def build_findings_html(scored_devices):
    if not scored_devices:
        return """
        <div style="
            background:white;
            border:1px solid #d8e6f3;
            border-radius:16px;
            padding:24px;
            color:#5b7086;
            box-shadow:0 2px 8px rgba(0,0,0,0.04);
        ">
            Run an analysis to see device findings.
        </div>
        """

    sorted_devices = sorted(
        scored_devices,
        key=lambda d: (d.get("risk_score", 0), d.get("confidence", 0)),
        reverse=True,
    )

    rows = []

    for d in sorted_devices:
        risk_level = d.get("risk_level", "")
        risk_score = d.get("risk_score", "")
        confidence = d.get("confidence", "")
        row_bg = "#fff5f5" if risk_level == "Critical" else "#ffffff"

        rows.append(
            f"""
            <tr style="background:{row_bg};">
                <td>{html.escape(str(d.get("hostname", "")))}</td>
                <td>{html.escape(str(d.get("ip", "")))}</td>
                <td>{html.escape(str(d.get("asset_type", "")))}</td>
                <td style="text-align:center;">{html.escape(str(confidence))}</td>
                <td style="text-align:center;">{managed_badge(d.get("managed", ""))}</td>
                <td>{html.escape(str(d.get("owner", "")))}</td>
                <td>{html.escape(str(d.get("location", "")))}</td>
                <td style="text-align:center; font-weight:700; color:#123b63;">{html.escape(str(risk_score))}</td>
                <td style="text-align:center;">{risk_badge(risk_level)}</td>
                <td>{html.escape(str(d.get("recommended_action", "")))}</td>
            </tr>
            """
        )

    table_html = f"""
    <div style="
        background:white;
        border:1px solid #d8e6f3;
        border-radius:18px;
        box-shadow:0 2px 10px rgba(0,0,0,0.04);
        overflow:hidden;
    ">
        <div style="
            padding:16px 18px;
            border-bottom:1px solid #e5edf5;
            background:linear-gradient(180deg, #f8fbfe 0%, #f2f7fc 100%);
        ">
            <div style="font-size:18px; font-weight:800; color:#123b63;">Device Exposure Analysis</div>
            <div style="font-size:13px; color:#5b7086; margin-top:4px;">
                Assets sorted by highest exposure score and classification confidence.
            </div>
        </div>

        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead>
                    <tr style="background:#f8fbfe; color:#123b63;">
                        <th style="text-align:left; padding:14px; border-bottom:1px solid #e5edf5;">Hostname</th>
                        <th style="text-align:left; padding:14px; border-bottom:1px solid #e5edf5;">IP</th>
                        <th style="text-align:left; padding:14px; border-bottom:1px solid #e5edf5;">Asset Type</th>
                        <th style="text-align:center; padding:14px; border-bottom:1px solid #e5edf5;">Confidence</th>
                        <th style="text-align:center; padding:14px; border-bottom:1px solid #e5edf5;">Status</th>
                        <th style="text-align:left; padding:14px; border-bottom:1px solid #e5edf5;">Owner</th>
                        <th style="text-align:left; padding:14px; border-bottom:1px solid #e5edf5;">Location</th>
                        <th style="text-align:center; padding:14px; border-bottom:1px solid #e5edf5;">Score</th>
                        <th style="text-align:center; padding:14px; border-bottom:1px solid #e5edf5;">Risk</th>
                        <th style="text-align:left; padding:14px; border-bottom:1px solid #e5edf5;">Recommended Action</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    </div>
    """
    return table_html


def build_top_risks_html(scored_devices):
    if not scored_devices:
        return """
        <div style="
            background:white;
            border:1px solid #d8e6f3;
            border-radius:16px;
            padding:18px;
            color:#5b7086;
            box-shadow:0 2px 8px rgba(0,0,0,0.04);
        ">
            Top risks will appear here after analysis.
        </div>
        """

    sorted_devices = sorted(
        scored_devices,
        key=lambda d: d.get("risk_score", 0),
        reverse=True,
    )[:3]

    cards = []
    for d in sorted_devices:
        cards.append(
            f"""
            <div style="
                background:white;
                border:1px solid #d8e6f3;
                border-radius:14px;
                padding:14px;
                box-shadow:0 2px 8px rgba(0,0,0,0.04);
            ">
                <div style="display:flex; justify-content:space-between; gap:10px; align-items:center;">
                    <div style="font-weight:800; color:#123b63;">{html.escape(str(d.get("hostname", "")))}</div>
                    <div>{risk_badge(d.get("risk_level", ""))}</div>
                </div>
                <div style="font-size:13px; color:#5b7086; margin-top:6px;">
                    {html.escape(str(d.get("asset_type", "")))} • Score {html.escape(str(d.get("risk_score", "")))}
                </div>
                <div style="font-size:13px; color:#334155; margin-top:10px; line-height:1.5;">
                    {html.escape(str(d.get("recommended_action", "")))}
                </div>
            </div>
            """
        )

    return f"""
    <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px;">
        {''.join(cards)}
    </div>
    """


def build_asset_chart(scored_devices):
    if not scored_devices:
        return None

    df = pd.DataFrame(scored_devices)

    if df.empty or "asset_type" not in df.columns:
        return None

    counts = df["asset_type"].value_counts().reset_index()
    counts.columns = ["Asset Type", "Count"]

    fig = px.pie(
        counts,
        names="Asset Type",
        values="Count",
        title="Discovered Asset Distribution",
        hole=0.45,
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        legend_title_text="Asset Type",
        paper_bgcolor="white",
    )

    return fig


def run_analysis(telemetry, discovery_source, environment):
    analyzed = analyze_text_input(telemetry)
    scored = score_devices(analyzed, environment)

    for d in scored:
        try:
            d["confidence"] = int(d.get("confidence", 0))
        except Exception:
            d["confidence"] = 0

    summary = generate_executive_summary(scored)
    metrics_html = build_metrics_html(scored)
    findings_html = build_findings_html(scored)
    top_risks_html = build_top_risks_html(scored)
    asset_chart = build_asset_chart(scored)

    df = pd.DataFrame(scored)

    return summary, metrics_html, top_risks_html, asset_chart, findings_html, df


custom_css = """
.gradio-container {
    max-width: 1450px !important;
    margin: 0 auto;
    background: linear-gradient(180deg, #f4f9fe 0%, #eef6fd 100%);
}

.hero-box {
    background: linear-gradient(135deg, #e9f4ff 0%, #f8fbff 100%);
    border: 1px solid #d6e7f8;
    border-radius: 22px;
    padding: 24px;
    margin-bottom: 14px;
    box-shadow: 0 6px 20px rgba(18, 59, 99, 0.08);
}

textarea, .wrap textarea {
    border-radius: 14px !important;
}

button.primary-btn {
    background: #174f84 !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
}

button.secondary-btn {
    background: #dcecfb !important;
    color: #123b63 !important;
    border: 1px solid #c9def2 !important;
    border-radius: 12px !important;
}
"""


title_html = """
<div class="hero-box">
    <div style="font-size:34px; font-weight:800; color:#123b63; margin-bottom:6px;">
        Exposure Command Center
    </div>
    <div style="font-size:17px; font-weight:600; color:#355a7a; margin-bottom:8px;">
        Forescout-Inspired Asset Discovery & Risk Simulator
    </div>
    <div style="font-size:14px; color:#4b6783; line-height:1.6;">
        Built as an interview study project to better understand agentless visibility, device classification,
        exposure prioritization, and policy-driven response across enterprise environments.
    </div>
</div>
"""


with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.HTML(title_html)

    with gr.Row():
        with gr.Column(scale=1, min_width=360):
            gr.Markdown("### Configure Scenario")

            scenario_dropdown = gr.Dropdown(
                choices=get_scenario_names(),
                label="Example Environment",
                value=get_scenario_names()[0],
            )

            load_button = gr.Button("Load Scenario", elem_classes="secondary-btn")

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

            analyze_button = gr.Button("Analyze Exposure", elem_classes="primary-btn")

        with gr.Column(scale=2, min_width=720):
            telemetry_input = gr.Textbox(
                label="Network Telemetry Input",
                value=get_default_scenario(),
                lines=12,
                placeholder="Paste one device per line using key=value pairs...",
            )

    metrics_html = gr.HTML(value=build_metrics_html([]))

    gr.Markdown("### Priority Findings")
    top_risks_html = gr.HTML(value=build_top_risks_html([]))

    executive_summary = gr.Textbox(
        label="Executive Summary",
        lines=7,
    )

    gr.Markdown("### Asset Visibility Overview")
    asset_chart = gr.Plot()

    findings_html = gr.HTML(value=build_findings_html([]))

    raw_data = gr.Dataframe(
        label="Raw Analysis Data",
        visible=False,
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
        outputs=[
            executive_summary,
            metrics_html,
            top_risks_html,
            asset_chart,
            findings_html,
            raw_data,
        ],
    )


if __name__ == "__main__":
    demo.launch()
