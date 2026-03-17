from __future__ import annotations

from typing import Dict, List


def parse_device_line(line: str) -> Dict[str, str]:
    """
    Parse a single device line like:
    hostname=ws-finance-22, ip=10.10.20.14, os=Windows 10, ports=443|3389
    """
    device: Dict[str, str] = {}

    for part in line.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        device[key.strip().lower()] = value.strip()

    device.setdefault("hostname", "unknown")
    device.setdefault("ip", "unknown")
    device.setdefault("mac", "unknown")
    device.setdefault("os", "unknown")
    device.setdefault("ports", "")
    device.setdefault("traffic", "")
    device.setdefault("owner", "unknown")
    device.setdefault("managed", "no")
    device.setdefault("location", "unknown")

    return device


def split_pipe_values(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip().lower() for item in value.split("|") if item.strip()]


def classify_device(device: Dict[str, str]) -> Dict[str, str]:
    hostname = device.get("hostname", "").lower()
    os_name = device.get("os", "").lower()
    owner = device.get("owner", "").lower()
    managed = device.get("managed", "").lower()
    location = device.get("location", "").lower()
    ports = split_pipe_values(device.get("ports", ""))
    traffic = split_pipe_values(device.get("traffic", ""))

    asset_type = "Unknown Asset"
    confidence = 45
    reasoning: List[str] = []

    # IoMT / medical devices
    if any(word in hostname for word in ["pump", "scanner", "monitor", "bedside", "ct", "mri", "lab-analyzer"]):
        asset_type = "IoMT Device"
        confidence = 90
        reasoning.append("Hostname pattern suggests a medical or clinical device.")

    if any(proto in traffic for proto in ["dicom"]):
        asset_type = "IoMT Device"
        confidence = max(confidence, 95)
        reasoning.append("Medical protocol detected (DICOM).")

    # OT / industrial devices
    if any(word in hostname for word in ["plc", "hmi", "scada", "controller", "sensor"]):
        asset_type = "OT / Industrial Asset"
        confidence = max(confidence, 88)
        reasoning.append("Hostname pattern aligns with industrial or control-system assets.")

    if any(proto in traffic for proto in ["modbus", "bacnet", "ethernet-ip"]):
        asset_type = "OT / Industrial Asset"
        confidence = max(confidence, 96)
        reasoning.append("Industrial protocol detected in traffic.")

    # Cameras / surveillance
    if "camera" in hostname or hostname.startswith("cam-") or "rtsp" in traffic:
        asset_type = "IoT Camera"
        confidence = max(confidence, 92)
        reasoning.append("Camera indicators found in hostname or RTSP traffic.")

    # Printers
    if "printer" in hostname or "jetdirect" in traffic or "9100" in ports:
        asset_type = "Network Printer"
        confidence = max(confidence, 90)
        reasoning.append("Printer indicators found in hostname, port 9100, or JetDirect traffic.")

    # VoIP
    if "voip" in hostname or "phone" in hostname or "sip" in traffic or "5060" in ports:
        if asset_type == "Unknown Asset":
            asset_type = "VoIP / Unified Communications Device"
            confidence = 88
            reasoning.append("SIP/VoIP patterns detected.")
        elif "VoIP" not in asset_type and "phone" in hostname:
            reasoning.append("Phone-like naming detected alongside other signals.")

    # Wireless / infrastructure
    if hostname.startswith("ap-") or "switchport" in hostname:
        if hostname.startswith("ap-"):
            asset_type = "Network Infrastructure Device"
            confidence = max(confidence, 90)
            reasoning.append("Access point naming pattern detected.")
        else:
            reasoning.append("Connected via an unidentified switchport context.")

    # Corporate managed endpoints
    if (
        any(os_hint in os_name for os_hint in ["windows", "macos", "ios", "ipados", "android"])
        and managed == "yes"
        and any(proto in traffic for proto in ["tls", "rdp", "apple-push"])
    ):
        if "server" in os_name:
            asset_type = "Server"
            confidence = max(confidence, 90)
            reasoning.append("Server OS detected with enterprise-style services.")
        elif "windows" in os_name or "macos" in os_name:
            asset_type = "Corporate Endpoint"
            confidence = max(confidence, 89)
            reasoning.append("Managed user endpoint signals detected.")
        elif os_name in ["ios", "ipados", "android"]:
            asset_type = "Managed Mobile Device"
            confidence = max(confidence, 85)
            reasoning.append("Managed mobile platform detected.")

    # Guest / BYOD
    if owner == "guest" or "guest" in location or "guest" in hostname:
        if managed == "no":
            asset_type = "Guest / BYOD Device"
            confidence = max(confidence, 84)
            reasoning.append("Guest ownership or guest network context detected.")

    # Embedded devices
    if os_name == "embedded" and asset_type == "Unknown Asset":
        asset_type = "Embedded Network Device"
        confidence = 72
        reasoning.append("Embedded OS suggests a specialized network-connected device.")

    # Unknown / unmanaged default boost
    if os_name == "unknown":
        reasoning.append("Operating system is unknown.")
    if managed == "no":
        reasoning.append("Device is not managed.")
    if owner == "unknown":
        reasoning.append("Device ownership is unknown.")

    if not reasoning:
        reasoning.append("Limited telemetry available; classification based on general patterns.")

    return {
        "asset_type": asset_type,
        "confidence": str(confidence),
        "reasoning": " ".join(reasoning),
    }


def analyze_device(device: Dict[str, str]) -> Dict[str, str]:
    classification = classify_device(device)

    result = {
        "hostname": device.get("hostname", "unknown"),
        "ip": device.get("ip", "unknown"),
        "mac": device.get("mac", "unknown"),
        "os": device.get("os", "unknown"),
        "owner": device.get("owner", "unknown"),
        "managed": device.get("managed", "no"),
        "location": device.get("location", "unknown"),
        "ports": device.get("ports", ""),
        "traffic": device.get("traffic", ""),
        "asset_type": classification["asset_type"],
        "confidence": classification["confidence"],
        "reasoning": classification["reasoning"],
    }

    return result


def analyze_text_input(raw_text: str) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        device = parse_device_line(line)
        analyzed = analyze_device(device)
        results.append(analyzed)

    return results
