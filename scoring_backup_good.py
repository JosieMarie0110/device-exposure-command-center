from typing import Dict, Tuple, List


def calculate_risk_score(device: Dict[str, str], environment: str = "Standard Enterprise") -> Tuple[int, str, List[str]]:
    score = 0
    reasons = []

    os_name = device.get("os", "").lower()
    owner = device.get("owner", "").lower()
    managed = device.get("managed", "").lower()
    location = device.get("location", "").lower()
    asset_type = device.get("asset_type", "").lower()
    ports = device.get("ports", "").lower()
    traffic = device.get("traffic", "").lower()

    if os_name == "unknown":
        score += 20
        reasons.append("Unknown operating system reduces asset confidence.")

    if managed == "no":
        score += 20
        reasons.append("Unmanaged device increases operational risk.")

    if owner == "unknown":
        score += 10
        reasons.append("Ownership is not established.")

    if "telnet" in traffic or "23" in ports:
        score += 15
        reasons.append("Legacy remote access service detected (Telnet).")

    if "ftp" in traffic or "21" in ports:
        score += 10
        reasons.append("Insecure or legacy file transfer exposure detected.")

    if "rdp" in traffic or "3389" in ports:
        score += 8
        reasons.append("Remote access protocol detected.")

    if any(x in asset_type for x in ["iot", "industrial", "ot", "iomt"]):
        score += 10
        reasons.append("Specialized connected asset may require tighter governance.")

    if any(x in asset_type for x in ["iot", "industrial", "ot", "iomt"]) and managed == "no":
        score += 15
        reasons.append("Specialized unmanaged asset increases exposure.")

    sensitive_locations = {
        "server-room",
        "icu",
        "nicu",
        "control-room",
        "plant-floor",
        "imaging",
        "datacenter",
        "network-closet",
        "lab",
    }

    if location in sensitive_locations:
        score += 15
        reasons.append(f"Asset is in a sensitive location: {location}.")

    if "windows 7" in os_name or "windows server 2012" in os_name:
        score += 15
        reasons.append("Legacy Windows platform may indicate elevated support and security risk.")

    if managed == "yes" and "corporate endpoint" in asset_type:
        score -= 10
        reasons.append("Managed corporate endpoint lowers relative risk.")

    if managed == "yes" and owner != "unknown":
        score -= 5
        reasons.append("Known ownership and management improve accountability.")

    if environment == "Healthcare":
        if "iomt" in asset_type or location in {"icu", "nicu", "imaging", "lab", "clinical"}:
            score += 10
            reasons.append("Healthcare context raises sensitivity for clinical assets.")

    if environment == "Manufacturing":
        if "industrial" in asset_type or "ot" in asset_type or location in {"plant-floor", "control-room"}:
            score += 10
            reasons.append("Manufacturing context raises sensitivity for operational assets.")

    if environment == "Regulated":
        if owner == "unknown":
            score += 5
            reasons.append("Unknown ownership is more concerning in regulated environments.")

    score = max(0, min(score, 100))

    if score >= 75:
        level = "Critical"
    elif score >= 50:
        level = "High"
    elif score >= 25:
        level = "Moderate"
    else:
        level = "Low"

    return score, level, reasons


def recommend_action(device: Dict[str, str], risk_level: str) -> str:
    asset_type = device.get("asset_type", "").lower()
    managed = device.get("managed", "").lower()
    owner = device.get("owner", "").lower()
    location = device.get("location", "").lower()

    if risk_level == "Critical":
        if managed == "no":
            return "Restrict access, segment immediately, and escalate for urgent investigation."
        return "Escalate to security operations and validate exposure immediately."

    if risk_level == "High":
        if owner == "unknown":
            return "Validate ownership, segment if needed, and investigate behavior."
        if any(x in asset_type for x in ["iot", "industrial", "ot", "iomt"]):
            return "Apply tighter segmentation and review specialized asset controls."
        return "Investigate posture and confirm policy alignment."

    if risk_level == "Moderate":
        if managed == "no":
            return "Monitor closely and validate whether the asset should be managed."
        if location in {"network-closet", "server-room"}:
            return "Review placement and confirm intended use."
        return "Continue monitoring and confirm baseline behavior."

    return "Allow normal access and continue routine monitoring."


def generate_business_impact(device: Dict[str, str]) -> str:
    asset_type = device.get("asset_type", "")
    risk_level = device.get("risk_level", "")
    managed = device.get("managed", "").lower()
    owner = device.get("owner", "").lower()

    if risk_level in {"Critical", "High"} and managed == "no":
        return "Unmanaged high-risk asset may create a visibility and control gap."
    if owner == "unknown":
        return "Lack of ownership can slow remediation and accountability."
    if "IoMT" in asset_type or "OT" in asset_type:
        return "Specialized asset may require context-aware governance and segmentation."
    if risk_level == "Low":
        return "Asset appears lower risk and more operationally understood."
    return "Asset should be reviewed in the context of broader exposure priorities."


def score_devices(devices, environment="Standard Enterprise"):
    results = []

    for device in devices:
        score, level, reasons = calculate_risk_score(device, environment)
        action = recommend_action(device, level)
        impact = generate_business_impact({
            **device,
            "risk_level": level,
        })

        device_result = device.copy()
        device_result["risk_score"] = score
        device_result["risk_level"] = level
        device_result["recommended_action"] = action
        device_result["risk_drivers"] = " | ".join(reasons) if reasons else "No major risk drivers detected."
        device_result["business_impact"] = impact

        results.append(device_result)

    return results


def generate_executive_summary(devices):
    total = len(devices)
    unmanaged = sum(1 for d in devices if d.get("managed", "").lower() == "no")
    unknown_owner = sum(1 for d in devices if d.get("owner", "").lower() == "unknown")
    high_risk = sum(1 for d in devices if d.get("risk_level") in ["High", "Critical"])
    critical = sum(1 for d in devices if d.get("risk_level") == "Critical")

    iot = sum(1 for d in devices if "iot" in d.get("asset_type", "").lower())
    iomt = sum(1 for d in devices if "iomt" in d.get("asset_type", "").lower())
    ot = sum(
        1
        for d in devices
        if "industrial" in d.get("asset_type", "").lower()
        or "ot" in d.get("asset_type", "").lower()
    )

    if critical > 0:
        primary_concern = "Critical-risk assets were identified and should be prioritized for containment or segmentation."
    elif high_risk > 0:
        primary_concern = "High-risk assets were identified, driven primarily by unmanaged posture, unclear ownership, or sensitive placement."
    elif unmanaged > 0:
        primary_concern = "The main concern is unmanaged asset visibility and governance."
    else:
        primary_concern = "The environment appears relatively stable, with lower immediate exposure indicators."

    summary = f"""
Assets Discovered: {total}

Unmanaged Devices: {unmanaged}
Unknown Ownership: {unknown_owner}

High Risk Assets: {high_risk}
Critical Assets: {critical}

IoT Devices: {iot}
IoMT Devices: {iomt}
OT / Industrial Assets: {ot}

Primary Exposure Insight:
{primary_concern}

Recommended Next Step:
Prioritize ownership validation, segmentation review, and posture assessment for unmanaged or high-risk assets before expanding governance to the broader environment.
"""

    return summary.strip()
