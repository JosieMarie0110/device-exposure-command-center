SCENARIOS = {
    "Corporate Campus": """hostname=ws-finance-22, ip=10.10.20.14, mac=00:1B:44:11:3A:B7, os=Windows 10, ports=443|3389, traffic=tls|rdp, owner=finance, managed=yes, location=hq
hostname=mac-marketing-07, ip=10.10.20.31, mac=3C:22:FB:91:22:10, os=macOS, ports=443|5223, traffic=tls|apple-push, owner=marketing, managed=yes, location=hq
hostname=printer-3f-west, ip=10.10.30.45, mac=AC:5F:3E:12:AA:09, os=embedded, ports=80|9100, traffic=http|jetdirect, owner=unknown, managed=no, location=west-office
hostname=cam-lobby-01, ip=10.10.90.33, mac=88:53:2E:44:AA:91, os=embedded, ports=80|554, traffic=http|rtsp, owner=facilities, managed=no, location=lobby
hostname=iphone-guest-01, ip=10.10.70.10, mac=40:9C:28:11:8A:55, os=iOS, ports=443, traffic=tls, owner=guest, managed=no, location=guest-wifi
hostname=win-hr-12, ip=10.10.21.11, mac=F0:18:98:55:44:11, os=Windows 11, ports=443|135|445, traffic=tls|smb|rpc, owner=hr, managed=yes, location=hq
hostname=unknown-asset-01, ip=10.10.99.99, mac=10:2A:B3:FF:88:77, os=unknown, ports=23|8080, traffic=telnet|http, owner=unknown, managed=no, location=server-room
hostname=voip-phone-22, ip=10.10.40.12, mac=64:16:7F:22:19:18, os=embedded, ports=5060|443, traffic=sip|tls, owner=it, managed=yes, location=hq""",

    "Hospital / IoMT": """hostname=infusion-pump-07, ip=10.20.80.22, mac=88:53:2E:44:AA:91, os=unknown, ports=161|502, traffic=snmp|modbus, owner=biomed, managed=no, location=icu
hostname=ct-scanner-02, ip=10.20.81.14, mac=00:25:96:FF:12:33, os=Windows 7, ports=104|443, traffic=dicom|tls, owner=radiology, managed=no, location=imaging
hostname=nurse-station-11, ip=10.20.20.45, mac=00:1B:44:11:3A:B8, os=Windows 10, ports=443|3389, traffic=tls|rdp, owner=nursing, managed=yes, location=clinical
hostname=patient-monitor-03, ip=10.20.82.31, mac=3C:5A:B4:22:90:11, os=embedded, ports=80|161, traffic=http|snmp, owner=unknown, managed=no, location=icu
hostname=lab-analyzer-01, ip=10.20.83.20, mac=50:3E:AA:10:11:99, os=embedded, ports=21|443, traffic=ftp|tls, owner=lab, managed=no, location=lab
hostname=doctor-macbook-04, ip=10.20.21.18, mac=24:A2:E1:19:88:77, os=macOS, ports=443|5223, traffic=tls|apple-push, owner=physician, managed=yes, location=clinical
hostname=visitor-phone-01, ip=10.20.90.18, mac=7C:D1:C3:11:12:13, os=Android, ports=443, traffic=tls, owner=guest, managed=no, location=guest-wifi
hostname=unknown-bedside-asset, ip=10.20.84.55, mac=9C:AD:EF:56:77:88, os=unknown, ports=23|80, traffic=telnet|http, owner=unknown, managed=no, location=nicu""",

    "Manufacturing / OT": """hostname=plc-line1-01, ip=10.30.50.10, mac=00:30:64:AA:10:01, os=embedded, ports=502|44818, traffic=modbus|ethernet-ip, owner=operations, managed=no, location=plant-floor
hostname=hmi-station-02, ip=10.30.50.21, mac=00:30:64:AA:10:02, os=Windows 10, ports=3389|445, traffic=rdp|smb, owner=engineering, managed=yes, location=control-room
hostname=scada-server-01, ip=10.30.10.15, mac=00:30:64:AA:10:03, os=Windows Server 2012, ports=443|135|445, traffic=tls|rpc|smb, owner=operations, managed=yes, location=datacenter
hostname=sensor-temp-14, ip=10.30.60.44, mac=00:30:64:AA:10:04, os=embedded, ports=1883, traffic=mqtt, owner=unknown, managed=no, location=plant-floor
hostname=eng-laptop-07, ip=10.30.20.17, mac=BC:EE:7B:10:22:44, os=Windows 11, ports=443|3389, traffic=tls|rdp, owner=engineering, managed=yes, location=engineering
hostname=camera-dock-01, ip=10.30.70.25, mac=3C:5A:B4:22:90:33, os=embedded, ports=80|554, traffic=http|rtsp, owner=security, managed=no, location=loading-dock
hostname=unknown-switchport-device, ip=10.30.99.91, mac=10:2A:B3:FF:88:70, os=unknown, ports=23|8080, traffic=telnet|http, owner=unknown, managed=no, location=plant-floor
hostname=bacnet-controller-01, ip=10.30.61.12, mac=18:65:90:AA:BB:CC, os=embedded, ports=47808, traffic=bacnet, owner=facilities, managed=no, location=hvac-room""",

    "Branch Office / BYOD": """hostname=branch-laptop-01, ip=10.40.20.10, mac=00:1B:44:11:3A:C1, os=Windows 11, ports=443|3389, traffic=tls|rdp, owner=sales, managed=yes, location=branch
hostname=branch-printer-01, ip=10.40.30.18, mac=AC:5F:3E:12:AA:19, os=embedded, ports=80|9100, traffic=http|jetdirect, owner=office-admin, managed=no, location=branch
hostname=guest-phone-22, ip=10.40.70.55, mac=40:9C:28:11:8A:99, os=Android, ports=443, traffic=tls, owner=guest, managed=no, location=guest-wifi
hostname=ipad-pos-01, ip=10.40.25.40, mac=24:A2:E1:19:88:99, os=iPadOS, ports=443, traffic=tls, owner=retail, managed=yes, location=branch
hostname=ap-branch-01, ip=10.40.10.2, mac=64:16:7F:22:19:99, os=embedded, ports=443|8080, traffic=tls|http, owner=it, managed=yes, location=network-closet
hostname=voip-phone-07, ip=10.40.40.14, mac=64:16:7F:22:19:77, os=embedded, ports=5060|443, traffic=sip|tls, owner=it, managed=yes, location=branch
hostname=unknown-device-branch, ip=10.40.99.77, mac=10:2A:B3:FF:88:12, os=unknown, ports=23|161, traffic=telnet|snmp, owner=unknown, managed=no, location=network-closet
hostname=mac-manager-01, ip=10.40.21.11, mac=3C:22:FB:91:22:88, os=macOS, ports=443|5223, traffic=tls|apple-push, owner=manager, managed=yes, location=branch"""
}


DISCOVERY_SOURCES = [
    "SPAN / Mirrored Traffic",
    "TAP Feed",
    "Switch Context",
    "DHCP / IPAM Context",
    "RADIUS / NAC Context",
    "EDR / MDM Enrichment",
    "Manual Inventory Import",
]


ENVIRONMENT_PROFILES = [
    "Standard Enterprise",
    "Regulated",
    "Healthcare",
    "Manufacturing",
]


def get_scenario_names():
    return list(SCENARIOS.keys())


def get_scenario_data(name: str) -> str:
    return SCENARIOS.get(name, "")


def get_default_scenario() -> str:
    return get_scenario_data("Corporate Campus")
