"""
diagnostics.py – Run real Windows diagnostic commands and collect system info.

On non-Windows systems each check gracefully returns a "not available" result
so the tool can still be explored/tested on Linux/macOS (e.g., in CI).
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


IS_WINDOWS = sys.platform == "win32"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    status: str          # "ok" | "warning" | "error" | "info" | "skipped"
    summary: str
    details: list[str] = field(default_factory=list)
    raw_output: str = ""


@dataclass
class DiagnosticReport:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    hostname: str = ""
    os_info: str = ""
    checks: list[CheckResult] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as exc:  # pragma: no cover
        return -1, "", str(exc)


def _ps(script: str, timeout: int = 60) -> tuple[int, str, str]:
    """Execute a PowerShell one-liner."""
    return _run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        timeout=timeout,
    )


def _not_windows(name: str) -> CheckResult:
    return CheckResult(
        name=name,
        status="skipped",
        summary="This check requires Windows.",
    )


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_os_info() -> CheckResult:
    info = platform.platform()
    node = platform.node()
    return CheckResult(
        name="OS Info",
        status="info",
        summary=info,
        details=[f"Hostname: {node}", f"Python: {sys.version.split()[0]}"],
    )


def check_disk_health() -> CheckResult:
    """Query S.M.A.R.T. / disk health via PowerShell."""
    name = "Disk Health (SMART)"
    if not IS_WINDOWS:
        return _not_windows(name)

    rc, out, err = _ps(
        "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus,OperationalStatus,"
        "Size | ConvertTo-Json -Depth 2"
    )
    if rc != 0 or not out:
        return CheckResult(name=name, status="warning",
                           summary="Could not query disk health (run as Administrator for full data).",
                           raw_output=err)

    try:
        disks = json.loads(out)
        if isinstance(disks, dict):
            disks = [disks]
        details = []
        overall = "ok"
        for d in disks:
            health = d.get("HealthStatus", "Unknown")
            size_gb = round(int(d.get("Size", 0)) / 1e9, 1)
            line = (f"{d.get('FriendlyName','?')} | {d.get('MediaType','?')} | "
                    f"{size_gb} GB | Health: {health} | Op: {d.get('OperationalStatus','?')}")
            details.append(line)
            if health.lower() not in ("healthy", "ok"):
                overall = "warning"
        return CheckResult(name=name, status=overall,
                           summary=f"{len(disks)} disk(s) found.",
                           details=details, raw_output=out)
    except json.JSONDecodeError:
        return CheckResult(name=name, status="info",
                           summary="Disk info retrieved (non-JSON output).",
                           raw_output=out)


def check_memory() -> CheckResult:
    """Check physical RAM via PowerShell."""
    name = "RAM"
    if not IS_WINDOWS:
        return _not_windows(name)

    rc, out, err = _ps(
        "Get-CimInstance Win32_PhysicalMemory | "
        "Select-Object Manufacturer,Capacity,Speed,MemoryType | ConvertTo-Json -Depth 2"
    )
    if rc != 0 or not out:
        return CheckResult(name=name, status="warning",
                           summary="Could not query RAM info.", raw_output=err)

    try:
        modules = json.loads(out)
        if isinstance(modules, dict):
            modules = [modules]
        total_gb = sum(int(m.get("Capacity", 0)) for m in modules) / 1e9
        details = []
        for m in modules:
            gb = round(int(m.get("Capacity", 0)) / 1e9, 1)
            details.append(f"{m.get('Manufacturer','?')} {gb} GB @ {m.get('Speed','?')} MHz")
        return CheckResult(name=name, status="ok",
                           summary=f"Total RAM: {round(total_gb, 1)} GB ({len(modules)} module(s))",
                           details=details, raw_output=out)
    except json.JSONDecodeError:
        return CheckResult(name=name, status="info",
                           summary="RAM info retrieved.", raw_output=out)


def check_event_log_bsod() -> CheckResult:
    """Look for recent BSOD/crash events in the System event log."""
    name = "BSOD / Crash Events"
    if not IS_WINDOWS:
        return _not_windows(name)

    rc, out, err = _ps(
        "Get-WinEvent -FilterHashtable @{LogName='System'; Id=41,1001,6008} "
        "-MaxEvents 10 -ErrorAction SilentlyContinue | "
        "Select-Object TimeCreated,Id,Message | ConvertTo-Json -Depth 2"
    )
    if rc != 0 and not out:
        return CheckResult(name=name, status="ok",
                           summary="No recent crash events found (or insufficient permissions).",
                           raw_output=err)

    try:
        events = json.loads(out)
        if isinstance(events, dict):
            events = [events]
        if not events:
            return CheckResult(name=name, status="ok",
                               summary="No recent BSOD / unexpected-shutdown events found.")
        details = []
        for e in events[:10]:
            msg = (e.get("Message") or "")[:120].replace("\n", " ")
            details.append(f"[{e.get('TimeCreated','')}] ID {e.get('Id','')} – {msg}")
        return CheckResult(name=name, status="warning",
                           summary=f"{len(events)} recent crash/shutdown event(s) detected.",
                           details=details, raw_output=out)
    except json.JSONDecodeError:
        return CheckResult(name=name, status="info",
                           summary="Crash events retrieved (non-JSON output).",
                           raw_output=out[:500])


def check_windows_integrity() -> CheckResult:
    """Quick DISM health check (fast – does not repair)."""
    name = "Windows Image Integrity (DISM)"
    if not IS_WINDOWS:
        return _not_windows(name)

    rc, out, err = _run(
        ["dism", "/Online", "/Cleanup-Image", "/CheckHealth"],
        timeout=120,
    )
    raw = (out + "\n" + err).strip()
    if "No component store corruption detected" in raw or rc == 0:
        return CheckResult(name=name, status="ok",
                           summary="Windows component store is healthy.",
                           raw_output=raw)
    return CheckResult(name=name, status="warning",
                       summary="DISM detected possible component store issues. Run Repair-Windows.ps1.",
                       raw_output=raw)


def check_activation() -> CheckResult:
    """Check Windows activation status."""
    name = "Windows Activation"
    if not IS_WINDOWS:
        return _not_windows(name)

    rc, out, err = _run(["cscript", "//NoLogo", r"C:\Windows\System32\slmgr.vbs", "/dli"],
                        timeout=30)
    raw = (out + "\n" + err).strip()
    if "Licensed" in raw:
        return CheckResult(name=name, status="ok",
                           summary="Windows is activated.", raw_output=raw)
    if "Notification" in raw or "Grace" in raw:
        return CheckResult(name=name, status="warning",
                           summary="Windows is NOT activated or is in a grace period.",
                           raw_output=raw)
    return CheckResult(name=name, status="info",
                       summary="Could not determine activation status.",
                       raw_output=raw)


def check_boot_config() -> CheckResult:
    """Verify BCD / boot configuration."""
    name = "Boot Configuration (BCD)"
    if not IS_WINDOWS:
        return _not_windows(name)

    rc, out, err = _run(["bcdedit", "/enum", "all"], timeout=30)
    raw = (out + "\n" + err).strip()
    if rc == 0:
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        return CheckResult(name=name, status="ok",
                           summary="BCD read successfully.",
                           details=lines[:20],
                           raw_output=raw)
    return CheckResult(name=name, status="warning",
                       summary="Could not read BCD (run as Administrator).",
                       raw_output=raw)


def check_cpu_temp() -> CheckResult:
    """Get CPU temperature via PowerShell WMI (requires ACPI provider)."""
    name = "CPU Temperature"
    if not IS_WINDOWS:
        return _not_windows(name)

    rc, out, err = _ps(
        "Get-CimInstance -Namespace root/WMI -ClassName MSAcpi_ThermalZoneTemperature "
        "-ErrorAction SilentlyContinue | "
        "Select-Object InstanceName,CurrentTemperature | ConvertTo-Json -Depth 2"
    )
    if rc != 0 or not out:
        return CheckResult(name=name, status="info",
                           summary="CPU temperature not available via WMI (use HWiNFO64 for accurate readings).",
                           raw_output=err)
    try:
        zones = json.loads(out)
        if isinstance(zones, dict):
            zones = [zones]
        details = []
        overall = "ok"
        for z in zones:
            raw_temp = z.get("CurrentTemperature", 0)
            celsius = round((raw_temp / 10.0) - 273.15, 1)
            label = z.get("InstanceName", "Zone")
            details.append(f"{label}: {celsius}°C")
            if celsius > 90:
                overall = "warning"
        return CheckResult(name=name, status=overall,
                           summary="CPU thermal zones read.",
                           details=details, raw_output=out)
    except json.JSONDecodeError:
        return CheckResult(name=name, status="info",
                           summary="Temperature data retrieved.", raw_output=out[:300])


def check_network() -> CheckResult:
    """Ping Google DNS to verify internet connectivity."""
    name = "Network Connectivity"
    target = "8.8.8.8"
    ping_cmd = (["ping", "-n", "3", target] if IS_WINDOWS
                else ["ping", "-c", "3", "-W", "3", target])
    rc, out, err = _run(ping_cmd, timeout=15)
    raw = (out + "\n" + err).strip()
    if rc == 0:
        return CheckResult(name=name, status="ok",
                           summary=f"Internet reachable (pinged {target}).",
                           raw_output=raw)
    return CheckResult(name=name, status="warning",
                       summary=f"Cannot reach {target} – check your network connection.",
                       raw_output=raw)


def check_drivers() -> CheckResult:
    """List devices with driver problems."""
    name = "Driver Issues"
    if not IS_WINDOWS:
        return _not_windows(name)

    rc, out, err = _ps(
        "Get-PnpDevice | Where-Object {$_.Status -ne 'OK'} | "
        "Select-Object Status,Class,FriendlyName,InstanceId | ConvertTo-Json -Depth 2"
    )
    if rc != 0 or not out or out.strip() in ("null", ""):
        return CheckResult(name=name, status="ok",
                           summary="No driver problems detected.")

    try:
        devices = json.loads(out)
        if isinstance(devices, dict):
            devices = [devices]
        if not devices:
            return CheckResult(name=name, status="ok",
                               summary="No driver problems detected.")
        details = [
            f"{d.get('Status','?')} | {d.get('Class','?')} | {d.get('FriendlyName','?')}"
            for d in devices
        ]
        return CheckResult(name=name, status="warning",
                           summary=f"{len(devices)} device(s) with driver issues.",
                           details=details, raw_output=out)
    except json.JSONDecodeError:
        return CheckResult(name=name, status="info",
                           summary="Driver info retrieved.", raw_output=out[:500])


# ---------------------------------------------------------------------------
# Full diagnostic runner
# ---------------------------------------------------------------------------

ALL_CHECKS = [
    check_os_info,
    check_disk_health,
    check_memory,
    check_event_log_bsod,
    check_windows_integrity,
    check_activation,
    check_boot_config,
    check_cpu_temp,
    check_network,
    check_drivers,
]


def run_all(checks=None, progress_callback=None) -> DiagnosticReport:
    """Run all (or a subset of) checks and return a DiagnosticReport."""
    report = DiagnosticReport(
        hostname=platform.node(),
        os_info=platform.platform(),
    )
    checks = checks or ALL_CHECKS
    for fn in checks:
        if progress_callback:
            progress_callback(fn.__name__)
        result = fn()
        report.checks.append(result)
    return report
