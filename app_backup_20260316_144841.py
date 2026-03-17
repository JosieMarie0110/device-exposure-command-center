import html
from io import BytesIO

import matplotlib.pyplot as plt
import gradio as gr
import pandas as pd
from PIL import Image

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

APP_TITLE = "DEVICE EXPOSURE COMMAND CENTER"
APP_SUBTITLE = "Simulate unmanaged asset visibility, device classification, and exposure-driven response workflows."

SCENARIO_PLACEHOLDER = "Select an environment"
DISCOVERY_PLACEHOLDER = "Select a discovery source"


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
        "**Environment Scenario**",
        "Choose a sample environment to simulate the types of assets, management patterns, and visibility gaps present on the network.",
        "",
        "**Discovery Source**",
        "Choose the telemetry source used to simulate how devices are discovered, classified, and enriched during analysis.",
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
                    base.extend(["", f"**Network Context:** {network_notes}"])
                if device_notes:
                    base.extend(["", f"**Asset Profile:** {device_notes}"])
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


def count_unmanaged(df: pd.DataFrame):
    if df is None or df.empty:
        return 0

    lower_map = {c.lower(): c for c in df.columns}
    managed_col = lower_map.get("managed")

    if not managed_col:
        return 0

    series = df[managed_col].astype(str).str.strip().str.lower()
    unmanaged_mask = series.isin(["no", "false", "0", "unmanaged", "unknown"])
    return int(unmanaged_mask.sum())


def count_unknown_owner(df: pd.DataFrame):
    if df is None or df.empty:
        return 0

    lower_map = {c.lower(): c for c in df.columns}
    owner_col = lower_map.get("owner")

    if not owner_col:
        return 0

    series = df[owner_col].astype(str).str.strip().str.lower()
    unknown_mask = series.isin(["", "unknown", "none", "na", "n/a"])
    return int(unknown_mask.sum())


def build_business_outcome_mapping(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return (
            "**Business Outcome Mapping**\n\n"
            "- Improve device visibility across the environment  \n"
            "- Reduce exposure caused by unmanaged assets  \n"
            "- Improve ownership clarity and follow-up workflows"
        )

    unmanaged_count = count_unmanaged(df)
    unknown_owner_count = count_unknown_owner(df)
    risk_col = pick_risk_column(df)

    high_risk_count = 0
    if risk_col:
        series = df[risk_col].fillna("").astype(str).str.strip().str.lower()
        high_risk_count = int(series.isin(["high", "critical"]).sum())

    outcomes = [
        "- Improve asset visibility and classification confidence",
        "- Reduce investigation time by enriching device context",
        "- Support better segmentation and enforcement decisions",
    ]

    if unmanaged_count > 0:
        outcomes.append(f"- Reduce unmanaged device exposure across **{unmanaged_count}** identified assets")

    if unknown_owner_count > 0:
        outcomes.append(f"- Improve ownership attribution for **{unknown_owner_count}** devices")

    if high_risk_count > 0:
        outcomes.append(f"- Prioritize remediation for **{high_risk_count}** high-risk or critical assets")

    outcomes.append("- Strengthen governance, remediation ownership, and downstream security workflows")

    return "**Business Outcome Mapping**\n\n" + "  \n".join(outcomes)


def build_signal_tiles_html(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return """
        <div style="padding:14px; color:#f1e2a6; font-size:13px;">
            No device exposure signals available yet. Run an analysis to populate results.
        </div>
        """

    risk_col = pick_risk_column(df)
    unmanaged_count = count_unmanaged(df)
    unknown_owner_count = count_unknown_owner(df)
    risk_source = html.escape(risk_col) if risk_col else "Management / ownership context"

    return f"""
    <div style="
        display:grid;
        grid-template-columns:repeat(4, minmax(0, 1fr));
        gap:10px;
        margin-bottom:8px;
    ">
        <div style="background:linear-gradient(180deg,#2a2100,#211900); border:1px solid #8a6b00; border-radius:10px; padding:10px 12px;">
            <div style="font-size:11px; color:#cda63a; font-weight:700; text-transform:uppercase; margin-bottom:4px;">Assets Observed</div>
            <div style="font-size:22px; color:#fdf4d2; font-weight:800;">{len(df)}</div>
        </div>

        <div style="background:linear-gradient(180deg,#2a2100,#211900); border:1px solid #8a6b00; border-radius:10px; padding:10px 12px;">
            <div style="font-size:11px; color:#cda63a; font-weight:700; text-transform:uppercase; margin-bottom:4px;">Unmanaged</div>
            <div style="font-size:22px; color:#fdf4d2; font-weight:800;">{unmanaged_count}</div>
        </div>

        <div style="background:linear-gradient(180deg,#2a2100,#211900); border:1px solid #8a6b00; border-radius:10px; padding:10px 12px;">
            <div style="font-size:11px; color:#cda63a; font-weight:700; text-transform:uppercase; margin-bottom:4px;">Unknown Owner</div>
            <div style="font-size:22px; color:#fdf4d2; font-weight:800;">{unknown_owner_count}</div>
        </div>

        <div style="background:linear-gradient(180deg,#2a2100,#211900); border:1px solid #8a6b00; border-radius:10px; padding:10px 12px;">
            <div style="font-size:11px; color:#cda63a; font-weight:700; text-transform:uppercase; margin-bottom:4px;">Signal Source</div>
            <div style="font-size:16px; color:#fdf4d2; font-weight:800;">{risk_source}</div>
        </div>
    </div>
    """


def fig_to_pil(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    image = Image.open(buf).convert("RGBA")
    plt.close(fig)
    return image


def build_exposure_chart(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8.8, 3.8))
    fig.patch.set_facecolor("#171100")
    ax.set_facecolor("#231b00")

    if df is None or df.empty:
        ax.text(
            0.5,
            0.5,
            "No exposure data available",
            ha="center",
            va="center",
            fontsize=12,
            color="#fdf4d2",
        )
        ax.axis("off")
        return fig_to_pil(fig)

    risk_col = pick_risk_column(df)

    if risk_col is not None:
        ordered = ["Low", "Medium", "High", "Critical", "Unknown"]
        counts = df[risk_col].fillna("Unknown").astype(str).str.title().value_counts().to_dict()
        values = [counts.get(level, 0) for level in ordered]
        colors = ["#4f7cf7", "#6f89ff", "#d9a441", "#c75c5c", "#94a3b8"]

        ax.barh(ordered, values, color=colors, edgecolor="none")
        ax.invert_yaxis()
        ax.set_title("Risk Signal Distribution", fontsize=13, fontweight="bold", color="#d7aa12")
        ax.set_xlabel("Device Count", color="#fdf4d2")
        ax.tick_params(axis="x", colors="#fdf4d2")
        ax.tick_params(axis="y", colors="#fdf4d2")

        for i, v in enumerate(values):
            ax.text(v + 0.05, i, str(v), va="center", fontsize=10, color="#fdf4d2")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#8a6b00")
        ax.spines["bottom"].set_color("#8a6b00")
        ax.grid(axis="x", alpha=0.18, color="#8a6b00")
        fig.tight_layout()
        return fig_to_pil(fig)

    unmanaged = count_unmanaged(df)
    unknown_owner = count_unknown_owner(df)
    managed = max(len(df) - unmanaged, 0)

    categories = ["Managed", "Unmanaged", "Unknown Owner"]
    values = [managed, unmanaged, unknown_owner]
    colors = ["#2f80ed", "#8b63ff", "#94a3b8"]

    ax.bar(categories, values, color=colors, edgecolor="none")
    ax.set_title("Device Management Signals", fontsize=13, fontweight="bold", color="#d7aa12")
    ax.set_ylabel("Device Count", color="#fdf4d2")
    ax.tick_params(axis="x", colors="#fdf4d2")
    ax.tick_params(axis="y", colors="#fdf4d2")

    for i, v in enumerate(values):
        ax.text(i, v + 0.05, str(v), ha="center", va="bottom", fontsize=10, color="#fdf4d2")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#8a6b00")
    ax.spines["bottom"].set_color("#8a6b00")
    ax.grid(axis="y", alpha=0.18, color="#8a6b00")
    fig.tight_layout()
    return fig_to_pil(fig)


def build_asset_table(df: pd.DataFrame):
    if df is None or df.empty:
        return pd.DataFrame(columns=["No asset data available"])

    preview = df.copy()

    preferred_columns = [
        "hostname",
        "ip",
        "os",
        "owner",
        "managed",
        "location",
        "risk",
        "risk_level",
        "severity",
    ]

    selected = []
    lower_map = {c.lower(): c for c in preview.columns}
    for col in preferred_columns:
        if col in lower_map:
            selected.append(lower_map[col])

    if selected:
        preview = preview[selected]

    preview.columns = [c.replace("_", " ").title() for c in preview.columns]
    return preview


def build_asset_table_summary(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "**Assets observed:** 0  \n**Unmanaged assets identified:** 0"

    unmanaged_count = count_unmanaged(df)
    unknown_owner_count = count_unknown_owner(df)

    return f"""**Assets observed:** {len(df)}  
**Unmanaged assets identified:** {unmanaged_count}  
**Unknown owner attribution:** {unknown_owner_count}"""


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


def normalize_talking_points(points):
    if isinstance(points, str):
        return points

    if isinstance(points, list):
        return "\n".join(f"- {item}" for item in points)

    return "\n".join([
        "- Validate unmanaged and unknown device visibility",
        "- Prioritize high-risk device investigation",
        "- Confirm segmentation and access-control coverage",
        "- Review remediation ownership across security and infrastructure teams",
    ])


def run_exposure_analysis(scenario: str, discovery: str):
    context_text = build_context_text(scenario, discovery)

    if not scenario or scenario == SCENARIO_PLACEHOLDER:
        msg = "Please select an environment."
        empty_df = pd.DataFrame()
        return (
            msg,
            msg,
            build_signal_tiles_html(empty_df),
            build_exposure_chart(empty_df),
            build_asset_table_summary(empty_df),
            build_asset_table(empty_df),
            build_business_outcome_mapping(empty_df),
            context_text,
        )

    if not discovery or discovery == DISCOVERY_PLACEHOLDER:
        msg = "Please select a discovery source."
        empty_df = pd.DataFrame()
        return (
            msg,
            msg,
            build_signal_tiles_html(empty_df),
            build_exposure_chart(empty_df),
            build_asset_table_summary(empty_df),
            build_asset_table(empty_df),
            build_business_outcome_mapping(empty_df),
            context_text,
        )

    try:
        analyzer_input = extract_analyzer_input(scenario)
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
                f"Analysis completed for **{scenario}** using **{discovery}**. "
                f"The environment shows device exposure areas that should be reviewed for unmanaged assets, "
                f"ownership gaps, and risk-driven enforcement opportunities."
            )

        try:
            actions = normalize_talking_points(generate_talking_points(scored_df))
        except Exception:
            actions = "\n".join([
                "- Validate unmanaged and unknown device visibility",
                "- Prioritize high-risk device investigation",
                "- Confirm segmentation and access-control coverage",
                "- Review remediation ownership across security and infrastructure teams",
            ])

        tiles_html = build_signal_tiles_html(scored_df)
        chart_image = build_exposure_chart(scored_df)
        table_summary = build_asset_table_summary(scored_df)
        table_df = build_asset_table(scored_df)
        business_outcomes = build_business_outcome_mapping(scored_df)

        return (
            executive_summary,
            actions,
            tiles_html,
            chart_image,
            table_summary,
            table_df,
            business_outcomes,
            context_text,
        )

    except Exception as e:
        error_text = f"Analysis error: {str(e)}"
        empty_df = pd.DataFrame()
        return (
            error_text,
            error_text,
            build_signal_tiles_html(empty_df),
            build_exposure_chart(empty_df),
            build_asset_table_summary(empty_df),
            build_asset_table(empty_df),
            build_business_outcome_mapping(empty_df),
            context_text,
        )


CUSTOM_CSS = """
body, .gradio-container {
    background: linear-gradient(180deg, #120d00 0%, #1b1400 100%) !important;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    color: #fdf4d2 !important;
}

.gradio-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
    padding: 12px !important;
}

#hero-shell {
    background: linear-gradient(135deg, #241b00 0%, #171100 100%);
    border: 1px solid #8a6b00;
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
}

#hero-title {
    color: #d7aa12;
    margin: 0 0 4px 0;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 0.2px;
}

#hero-subtitle {
    color: #f1e2a6;
    margin: 0;
    font-size: 12px;
    line-height: 1.35;
}

.panel,
.result-card,
.context-card,
.details-card {
    background: linear-gradient(180deg, #231b00 0%, #171100 100%) !important;
    border: 1px solid #8a6b00 !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.14) !important;
    padding: 10px !important;
}

.section-title-dark {
    color: #d7aa12;
    font-weight: 800;
    font-size: 14px;
    margin-bottom: 8px;
}

.gradio-container .gr-dropdown .wrap,
.gradio-container .gr-textbox,
.gradio-container .gr-textbox textarea,
.gradio-container input,
.gradio-container select,
.gradio-container textarea {
    background: #2a2100 !important;
    color: #fdf4d2 !important;
    border: 1.5px solid #8a6b00 !important;
    border-radius: 10px !important;
    min-height: 40px !important;
    box-shadow: none !important;
    font-size: 13px !important;
}

.gradio-container .gr-dropdown .wrap:hover {
    border-color: #cda63a !important;
}

.gr-button {
    background: linear-gradient(90deg, #a67d00, #7a5c00) !important;
    color: #fff7dd !important;
    border: 1px solid #6e5300 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    min-height: 40px !important;
    padding: 8px 12px !important;
    box-shadow: none !important;
}

.gr-button:hover {
    filter: brightness(1.05);
}

.compact-markdown p,
.compact-markdown li {
    font-size: 12px !important;
    line-height: 1.45 !important;
    margin-bottom: 4px !important;
    color: #fdf4d2 !important;
}

.compact-markdown h1,
.compact-markdown h2,
.compact-markdown h3,
.compact-markdown h4 {
    font-size: 14px !important;
    margin-bottom: 6px !important;
    color: #d7aa12 !important;
}

.gradio-container .markdown,
.gradio-container .markdown p,
.gradio-container .markdown li,
.gradio-container .markdown strong {
    color: #fdf4d2 !important;
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
                gr.Markdown('<div class="section-title-dark">Scenario Controls</div>')

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

                run_button = gr.Button("Analyze Device Exposure")

        with gr.Column(scale=2):
            with gr.Column(elem_classes=["context-card", "compact-markdown"]):
                gr.Markdown('<div class="section-title-dark">Discovery & Visibility Context</div>')
                context_box = gr.Markdown(
                    value=build_context_text(SCENARIO_PLACEHOLDER, DISCOVERY_PLACEHOLDER)
                )

    with gr.Row(equal_height=True):
        with gr.Column(scale=1, elem_classes=["result-card", "compact-markdown"]):
            gr.Markdown('<div class="section-title-dark">Exposure Overview</div>')
            summary_box = gr.Markdown()

        with gr.Column(scale=1, elem_classes=["result-card", "compact-markdown"]):
            gr.Markdown('<div class="section-title-dark">Priority Actions</div>')
            actions_box = gr.Markdown()

    with gr.Row():
        with gr.Column(elem_classes=["details-card"]):
            gr.Markdown('<div class="section-title-dark">Device Exposure Signals</div>')
            signal_tiles_box = gr.HTML(
                value=build_signal_tiles_html(pd.DataFrame())
            )
            exposure_chart = gr.Image(
                value=build_exposure_chart(pd.DataFrame()),
                show_label=False,
                container=False,
                interactive=False,
            )

    with gr.Row():
        with gr.Column(scale=2, elem_classes=["details-card", "compact-markdown"]):
            gr.Markdown('<div class="section-title-dark">Asset Intelligence Table</div>')
            asset_table_summary = gr.Markdown(value="**Assets observed:** 0  \n**Unmanaged assets identified:** 0")
            exposure_table = gr.Dataframe(
                value=pd.DataFrame(),
                interactive=False,
                wrap=True,
            )

        with gr.Column(scale=1, elem_classes=["details-card", "compact-markdown"]):
            gr.Markdown('<div class="section-title-dark">Business Outcome Mapping</div>')
            business_outcome_box = gr.Markdown(
                value=build_business_outcome_mapping(pd.DataFrame())
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
            signal_tiles_box,
            exposure_chart,
            asset_table_summary,
            exposure_table,
            business_outcome_box,
            context_box,
        ],
    )

if __name__ == "__main__":
    demo.launch()
