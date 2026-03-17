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

DISCOVERY_DETAILS = {
    "SPAN / Mirrored Traffic": {
        "overview": "Passive network telemetry collected from mirrored switch traffic to observe device communication patterns.",
        "strengths": "Strong for identifying unmanaged devices, protocol usage, and network behavior without requiring agents.",
        "limitations": "Limited visibility for idle devices, encrypted traffic context, and segments not included in SPAN configuration.",
        "analysis_value": "uncovering unmanaged assets and communication-based exposure across the environment",
    },
    "TAP Feed": {
        "overview": "Packet-level telemetry captured from network TAP infrastructure for continuous passive monitoring.",
        "strengths": "Provides high-fidelity traffic visibility with minimal packet loss compared to SPAN.",
        "limitations": "Coverage depends on TAP placement and may not reflect the full network if not fully instrumented.",
        "analysis_value": "validating network behavior, device communications, and improving confidence in passive discovery",
    },
    "Switch Context": {
        "overview": "Network infrastructure metadata sourced from switches, including MAC tables, VLANs, and port mappings.",
        "strengths": "Provides strong location awareness and Layer 2 visibility for connected devices.",
        "limitations": "Limited behavioral or application-level context and may not identify device risk or activity patterns on its own.",
        "analysis_value": "mapping device location, segmentation, and understanding physical network placement",
    },
    "DHCP / IPAM Context": {
        "overview": "IP address assignment and lease data sourced from DHCP and IPAM systems.",
        "strengths": "Helps correlate devices to IP history, naming conventions, and basic ownership patterns.",
        "limitations": "Data may be stale or incomplete and does not provide real-time behavior or security posture.",
        "analysis_value": "improving ownership attribution and tracking device identity over time",
    },
    "RADIUS / NAC Context": {
        "overview": "Authentication and access-control data from RADIUS or NAC systems.",
        "strengths": "Provides user-to-device correlation and access control context.",
        "limitations": "Only reflects authenticated sessions, so unmanaged or unauthenticated devices may be missed.",
        "analysis_value": "understanding access patterns, identity correlation, and enforcement opportunities",
    },
    "EDR / MDM Enrichment": {
        "overview": "Endpoint telemetry from EDR or MDM platforms providing device posture and security context.",
        "strengths": "Deep visibility into managed endpoints, including OS, software, and security posture.",
        "limitations": "Limited to managed devices with agents installed and does not cover unmanaged or unsupported assets well.",
        "analysis_value": "validating endpoint security posture and enriching device context",
    },
    "Manual Inventory Import": {
        "overview": "Static asset data imported from spreadsheets or external inventory sources.",
        "strengths": "Provides baseline asset records and organizational context.",
        "limitations": "Often outdated or incomplete and lacks real-time validation or behavioral insight.",
        "analysis_value": "baseline comparison and identifying gaps between known and observed assets",
    },
}


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

                base.extend(["", f"**Selected Scenario:** {scenario}"])

                if description:
                    base.extend(["", f"**Environment Overview:** {description}"])
                if network_notes:
                    base.extend(["", f"**Network Context:** {network_notes}"])
                if device_notes:
                    base.extend(["", f"**Asset Profile:** {device_notes}"])
        except Exception:
            base.extend(["", f"**Selected Scenario:** {scenario}"])

    if discovery and discovery != DISCOVERY_PLACEHOLDER:
        base.extend(["", f"**Selected Discovery Source:** {discovery}"])

        details = DISCOVERY_DETAILS.get(discovery)
        if details:
            base.extend([
                "",
                f"**How It Works:** {details['overview']}",
                "",
                f"**Strengths:** {details['strengths']}",
                "",
                f"**Visibility Gaps:** {details['limitations']}",
                "",
                f"**Why It Matters Here:** This source is especially useful for {details['analysis_value']}.",
            ])

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

    series = df[owner_col].fillna("").astype(str).str.strip().str.lower()
    unknown_mask = series.isin(["", "unknown", "none", "na", "n/a"])
    return int(unknown_mask.sum())


def count_high_risk(df: pd.DataFrame):
    if df is None or df.empty:
        return 0

    risk_col = pick_risk_column(df)
    if not risk_col:
        return 0

    series = df[risk_col].fillna("").astype(str).str.strip().str.lower()
    return int(series.isin(["high", "critical"]).sum())


def get_primary_exposure_theme(unmanaged_count: int, unknown_owner_count: int, high_risk_count: int) -> str:
    values = {
        "unmanaged": unmanaged_count,
        "ownership": unknown_owner_count,
        "high_risk": high_risk_count,
    }

    if max(values.values()) == 0:
        return "baseline"

    return max(values, key=values.get)


def build_dynamic_executive_summary(
    scenario: str,
    discovery: str,
    df: pd.DataFrame,
) -> str:
    if df is None or df.empty:
        return (
            f"Analysis completed for **{scenario}** using **{discovery}**. "
            "No device records were available to score, so additional telemetry or sample data may be needed "
            "to evaluate unmanaged exposure, ownership gaps, and risk patterns."
        )

    total_assets = len(df)
    unmanaged_count = count_unmanaged(df)
    unknown_owner_count = count_unknown_owner(df)
    high_risk_count = count_high_risk(df)
    primary_theme = get_primary_exposure_theme(unmanaged_count, unknown_owner_count, high_risk_count)

    lead_map = {
        "unmanaged": "The strongest exposure signal is unmanaged asset presence.",
        "ownership": "The strongest exposure signal is incomplete ownership attribution.",
        "high_risk": "The strongest exposure signal is elevated device risk.",
        "baseline": "The current dataset shows a relatively balanced exposure profile.",
    }

    observations = [f"**{total_assets}** assets were analyzed"]

    if unmanaged_count > 0:
        observations.append(f"**{unmanaged_count}** appear unmanaged")
    if unknown_owner_count > 0:
        observations.append(f"**{unknown_owner_count}** have unclear ownership")
    if high_risk_count > 0:
        observations.append(f"**{high_risk_count}** are marked high-risk or critical")

    observation_text = ", ".join(observations)

    discovery_note = ""
    details = DISCOVERY_DETAILS.get(discovery)
    if details:
        discovery_note = (
            f" Because this analysis relies on **{discovery}**, visibility is strongest for "
            f"{details['analysis_value']}."
        )

    return (
        f"Analysis completed for **{scenario}** using **{discovery}**. "
        f"{lead_map[primary_theme]} "
        f"The current results indicate {observation_text}, creating opportunities to improve visibility, "
        f"ownership tracking, investigation prioritization, and enforcement decisions."
        f"{discovery_note}"
    )


def build_priority_actions(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "\n".join([
            "- Validate device visibility across the selected environment",
            "- Review unmanaged and unknown ownership patterns",
            "- Confirm segmentation and access-control policy coverage",
            "- Align remediation ownership across security and infrastructure teams",
        ])

    unmanaged_count = count_unmanaged(df)
    unknown_owner_count = count_unknown_owner(df)
    high_risk_count = count_high_risk(df)

    actions = []

    if unmanaged_count > 0:
        actions.append(f"- Investigate and classify **{unmanaged_count} unmanaged assets**")
    if unknown_owner_count > 0:
        actions.append(f"- Resolve ownership gaps for **{unknown_owner_count} devices**")
    if high_risk_count > 0:
        actions.append(f"- Prioritize review of **{high_risk_count} high-risk or critical devices**")

    actions.append("- Validate segmentation and access-control policy coverage")
    actions.append("- Confirm remediation ownership across security and infrastructure teams")

    return "\n".join(actions)


def build_business_outcome_mapping(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return (
            "- Improve device visibility across the environment  \n"
            "- Reduce exposure caused by unmanaged assets  \n"
            "- Improve ownership clarity and follow-up workflows"
        )

    unmanaged_count = count_unmanaged(df)
    unknown_owner_count = count_unknown_owner(df)
    high_risk_count = count_high_risk(df)

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

    return "  \n".join(outcomes)


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
    high_risk_count = count_high_risk(df)
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
            <div style="font-size:11px; color:#cda63a; font-weight:700; text-transform:uppercase; margin-bottom:4px;">High Risk</div>
            <div style="font-size:22px; color:#fdf4d2; font-weight:800;">{high_risk_count}</div>
        </div>
    </div>
    <div style="
        margin-top:6px;
        background:linear-gradient(180deg,#241c00,#1a1400);
        border:1px solid #8a6b00;
        border-radius:10px;
        padding:10px 12px;
        color:#fdf4d2;
        font-size:13px;
    ">
        <span style="color:#cda63a; font-weight:700;">Signal Source:</span> {risk_source}
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
    high_risk_count = count_high_risk(df)

    return f"""**Assets observed:** {len(df)}  
**Unmanaged assets identified:** {unmanaged_count}  
**Unknown owner attribution:** {unknown_owner_count}  
**High-risk / critical assets:** {high_risk_count}"""


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
            model_summary = generate_executive_summary(scored_df)
            if isinstance(model_summary, str) and len(model_summary.strip()) > 40:
                executive_summary = build_dynamic_executive_summary(scenario, discovery, scored_df)
            else:
                executive_summary = build_dynamic_executive_summary(scenario, discovery, scored_df)
        except Exception:
            executive_summary = build_dynamic_executive_summary(scenario, discovery, scored_df)

        try:
            _ = generate_talking_points(scored_df)
            actions = build_priority_actions(scored_df)
        except Exception:
            actions = build_priority_actions(scored_df)

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
    padding: 12px !important;
}

.section-title-dark {
    color: #e3b722 !important;
    font-weight: 700;
    font-size: 15px;
    margin-bottom: 8px;
}

/* readable markdown text */
.gradio-container .markdown p,
.gradio-container .markdown li,
.gradio-container .markdown span,
.gradio-container .prose p,
.gradio-container .prose li {
    color: #fdf4d2 !important;
}

.gradio-container .markdown strong,
.gradio-container .prose strong {
    color: #e6c34a !important;
}

/* safer input styling: do not override dropdown internals too aggressively */
.gradio-container input:not([type="checkbox"]),
.gradio-container textarea {
    background: #2a2100 !important;
    color: #fdf4d2 !important;
    border: 1.5px solid #8a6b00 !important;
    border-radius: 10px !important;
}

/* button darker for better contrast */
.gr-button {
    background: linear-gradient(180deg, #4a3500, #2a1e00) !important;
    color: #ffd95a !important;
    border: 1px solid #8a6b00 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}

.gr-button:hover {
    background: linear-gradient(180deg, #5a4200, #332500) !important;
}

/* dataframe text */
table, th, td {
    color: #000000 !important;
}

/* footer */
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
            with gr.Column(elem_classes=["context-card"]):
                gr.Markdown('<div class="section-title-dark">Discovery & Visibility Context</div>')

                context_box = gr.Markdown(
                    value=build_context_text(
                        SCENARIO_PLACEHOLDER,
                        DISCOVERY_PLACEHOLDER
                    )
                )

    with gr.Row(equal_height=True):
        with gr.Column(scale=1, elem_classes=["result-card"]):
            gr.Markdown('<div class="section-title-dark">Exposure Overview</div>')
            summary_box = gr.Markdown()

        with gr.Column(scale=1, elem_classes=["result-card"]):
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
        with gr.Column(scale=2, elem_classes=["details-card"]):
            gr.Markdown('<div class="section-title-dark">Asset Intelligence Table</div>')

            asset_table_summary = gr.Markdown(
                value="**Assets observed:** 0  \n**Unmanaged assets identified:** 0"
            )

            exposure_table = gr.Dataframe(
                value=pd.DataFrame(),
                interactive=False,
                wrap=True,
            )

        with gr.Column(scale=1, elem_classes=["details-card"]):
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
