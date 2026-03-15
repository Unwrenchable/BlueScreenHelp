"""
troubleshooter.py – Interactive decision-tree troubleshooter.

Works entirely offline – no API key required.
The tree mirrors the steps documented in the BlueScreenHelp docs/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Decision-tree data model
# ---------------------------------------------------------------------------

@dataclass
class Node:
    id: str
    prompt: str
    choices: dict[str, str] = field(default_factory=dict)   # label -> next node id
    advice: list[str] = field(default_factory=list)          # shown when terminal
    links: list[str] = field(default_factory=list)           # doc references


# ---------------------------------------------------------------------------
# Tree definition  (mirrors BlueScreenHelp docs)
# ---------------------------------------------------------------------------

NODES: dict[str, Node] = {

    # ── Entry point ──────────────────────────────────────────────────────────
    "start": Node(
        id="start",
        prompt="What best describes your situation?",
        choices={
            "1": "bsod",
            "2": "wont_boot",
            "3": "slow_unstable",
            "4": "no_display",
            "5": "activation",
        },
    ),

    # ── BSOD branch ─────────────────────────────────────────────────────────
    "bsod": Node(
        id="bsod",
        prompt="Do you see a specific stop-code (e.g. MEMORY_MANAGEMENT, IRQL_NOT_LESS_OR_EQUAL)?",
        choices={
            "1": "bsod_known_code",
            "2": "bsod_no_code",
        },
    ),

    "bsod_known_code": Node(
        id="bsod_known_code",
        prompt="Which category does the stop-code fall into?",
        choices={
            "1": "bsod_memory",
            "2": "bsod_driver",
            "3": "bsod_disk",
            "4": "bsod_other",
        },
    ),

    "bsod_memory": Node(
        id="bsod_memory",
        prompt="RAM-related BSOD (MEMORY_MANAGEMENT, PAGE_FAULT_IN_NONPAGED_AREA, etc.)",
        advice=[
            "1. Run Windows Memory Diagnostic: Win+R → mdsched.exe → Restart now and check for problems",
            "2. Run MemTest86 for a deeper test (boot from USB, let it run 2+ passes)",
            "3. Try reseating your RAM sticks (power off, unplug, remove & re-insert firmly)",
            "4. If multiple sticks, test ONE stick at a time in Slot 1 to isolate a faulty module",
            "5. Check RAM frequency/XMP in BIOS – disable XMP as a test",
        ],
        links=["docs/diagnostic-tools.md"],
    ),

    "bsod_driver": Node(
        id="bsod_driver",
        prompt="Driver-related BSOD (IRQL_NOT_LESS_OR_EQUAL, SYSTEM_SERVICE_EXCEPTION, etc.)",
        advice=[
            "1. Boot into Safe Mode (Shift+Restart → Troubleshoot → Advanced → Startup Settings → F4)",
            "2. In Safe Mode, open Device Manager and look for yellow ⚠ devices",
            "3. Roll back recently updated drivers (right-click → Properties → Driver → Roll Back)",
            "4. Uninstall the problematic driver and reinstall the latest from the manufacturer's site",
            "5. Run: sfc /scannow    in an elevated Command Prompt",
            "6. If the BSOD names a specific .sys file, search for that file name online to identify the driver",
        ],
        links=["docs/diagnostic-tools.md"],
    ),

    "bsod_disk": Node(
        id="bsod_disk",
        prompt="Disk-related BSOD (NTFS_FILE_SYSTEM, FAT_FILE_SYSTEM, INACCESSIBLE_BOOT_DEVICE, etc.)",
        advice=[
            "1. Check disk health: run 'bsh diagnose --checks disk' or Get-PhysicalDisk in PowerShell",
            "2. Run: chkdsk C: /f /r /x   from Recovery Console (may need USB boot)",
            "3. Check SATA/NVMe cable connections – reseat the drive",
            "4. Look at CrystalDiskInfo SMART attributes for Reallocated Sectors or Pending Sectors",
            "5. If INACCESSIBLE_BOOT_DEVICE: try 'bootrec /fixmbr' and 'bootrec /fixboot' from WinRE",
        ],
        links=["docs/usb-boot-recovery.md", "docs/diagnostic-tools.md"],
    ),

    "bsod_other": Node(
        id="bsod_other",
        prompt="Generic BSOD advice",
        advice=[
            "1. Note the exact stop code and search it on https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/bug-check-code-reference2",
            "2. Check Event Viewer → Windows Logs → System for Critical events near the crash time",
            "3. Run: bsh diagnose   to collect a full diagnostic report",
            "4. Update Windows (Settings → Windows Update → Check for updates)",
            "5. Check for malware: run Windows Defender full scan or Malwarebytes",
        ],
        links=["docs/diagnostic-tools.md"],
    ),

    "bsod_no_code": Node(
        id="bsod_no_code",
        prompt="No visible stop code – likely a hardware or firmware issue.",
        advice=[
            "1. Enable automatic memory dumps: System Properties → Advanced → Startup & Recovery → Small memory dump",
            "2. Check hardware temps with HWiNFO64 while under load",
            "3. Ensure all power connectors (CPU 8-pin, GPU 6+2 pin) are firmly seated",
            "4. Test with the minimum hardware (1 RAM stick, no GPU if CPU has iGPU)",
            "5. Update BIOS/UEFI firmware from your motherboard manufacturer's site",
        ],
        links=["docs/diagnostic-tools.md"],
    ),

    # ── Won't boot branch ────────────────────────────────────────────────────
    "wont_boot": Node(
        id="wont_boot",
        prompt="How far does the system get?",
        choices={
            "1": "no_post",
            "2": "bios_only",
            "3": "boot_loop",
            "4": "winre",
        },
    ),

    "no_post": Node(
        id="no_post",
        prompt="No POST (no beeps, no display, fans may spin) – likely hardware.",
        advice=[
            "1. Unplug ALL external peripherals (USB drives, monitors except one, etc.)",
            "2. Clear CMOS: remove the coin-cell battery for 30 s, or use the CLEAR_CMOS jumper/button",
            "3. Reseat RAM (try one stick at a time in Slot 1/A2)",
            "4. Reseat GPU – try with iGPU only if possible",
            "5. Listen for POST beep codes – look them up for your BIOS vendor",
            "6. Check that all power cables (ATX 24-pin, CPU 8-pin) are fully inserted",
        ],
        links=["README.md"],
    ),

    "bios_only": Node(
        id="bios_only",
        prompt="Gets to BIOS/UEFI but won't boot Windows.",
        advice=[
            "1. Check Boot Order in BIOS – your Windows drive should be first",
            "2. Make sure Secure Boot is set correctly (On for GPT/UEFI Windows, Off for legacy)",
            "3. If using NVMe, ensure the drive is visible in BIOS under 'NVMe Configuration'",
            "4. Boot from a Windows USB recovery drive → Startup Repair",
            "5. In WinRE Command Prompt, run: bootrec /fixmbr  bootrec /fixboot  bootrec /rebuildbcd",
        ],
        links=["docs/usb-boot-recovery.md", "README.md"],
    ),

    "boot_loop": Node(
        id="boot_loop",
        prompt="Stuck in a restart loop (crashes before reaching the desktop).",
        advice=[
            "1. Interrupt 3 boots in a row to trigger Automatic Repair / WinRE",
            "2. In WinRE: Troubleshoot → Advanced Options → System Restore (pick a good restore point)",
            "3. If no restore point: Advanced Options → Startup Repair",
            "4. Boot from USB and run: sfc /scannow  and  DISM /Online /Cleanup-Image /RestoreHealth",
            "5. Last resort: Windows Reset (keeps files option) from WinRE → Troubleshoot → Reset this PC",
        ],
        links=["docs/usb-boot-recovery.md"],
    ),

    "winre": Node(
        id="winre",
        prompt="Already in Windows Recovery Environment (WinRE).",
        advice=[
            "Option A – Startup Repair: Troubleshoot → Advanced Options → Startup Repair",
            "Option B – System Restore: Troubleshoot → Advanced Options → System Restore",
            "Option C – Command Prompt:",
            "   sfc /scannow",
            "   DISM /Online /Cleanup-Image /RestoreHealth",
            "   bootrec /fixmbr && bootrec /fixboot && bootrec /rebuildbcd",
            "   chkdsk C: /f /r /x",
            "Option D – Reset this PC (keeps files): Troubleshoot → Reset this PC → Keep my files",
        ],
        links=["docs/usb-boot-recovery.md"],
    ),

    # ── Slow / unstable branch ───────────────────────────────────────────────
    "slow_unstable": Node(
        id="slow_unstable",
        prompt="What kind of instability are you experiencing?",
        choices={
            "1": "slow_general",
            "2": "high_temp",
            "3": "random_freeze",
        },
    ),

    "slow_general": Node(
        id="slow_general",
        prompt="Generally slow system",
        advice=[
            "1. Open Task Manager (Ctrl+Shift+Esc) → Processes – check for high CPU/RAM/Disk usage",
            "2. Run: bsh diagnose   for a full snapshot",
            "3. Disable startup programs: Task Manager → Startup tab",
            "4. Run Windows Defender full scan (or Malwarebytes) for malware",
            "5. Check disk health – a failing HDD will severely slow the system (use CrystalDiskInfo)",
            "6. Consider adding RAM or upgrading to an SSD",
        ],
        links=["docs/diagnostic-tools.md"],
    ),

    "high_temp": Node(
        id="high_temp",
        prompt="Overheating (CPU/GPU throttling or shutdown)",
        advice=[
            "1. Install HWiNFO64 and monitor CPU/GPU temps under load (safe limits: CPU <85°C, GPU <90°C)",
            "2. Clean dust from heatsinks, fans, and vents with compressed air",
            "3. Replace thermal paste on CPU (and GPU if it's old)",
            "4. Ensure all case fans are working and airflow is correct (front/bottom = intake, rear/top = exhaust)",
            "5. For laptops: use a cooling pad, ensure vents are not blocked",
        ],
        links=["docs/diagnostic-tools.md"],
    ),

    "random_freeze": Node(
        id="random_freeze",
        prompt="Random freezes / hangs (requires hard reboot)",
        advice=[
            "1. Check Event Viewer immediately after a freeze for Critical/Error events",
            "2. Test RAM with MemTest86 (run overnight for best results)",
            "3. Check disk health (CrystalDiskInfo) – reallocated sectors = imminent failure",
            "4. Update or roll back GPU drivers",
            "5. Run: bsh diagnose   and inspect the output for warnings",
        ],
        links=["docs/diagnostic-tools.md"],
    ),

    # ── No display branch ────────────────────────────────────────────────────
    "no_display": Node(
        id="no_display",
        prompt="No display / black screen",
        advice=[
            "1. Try a different monitor cable (HDMI → DisplayPort, or vice versa)",
            "2. If discrete GPU: connect monitor to motherboard video output to test iGPU",
            "3. Reseat the GPU in the PCIe slot; check GPU power connectors",
            "4. Try a different monitor or TV",
            "5. If system POSTs (beeps): GPU may be dead – test in another system",
            "6. After Windows login (blind): try Win+Ctrl+Shift+B to reset GPU driver",
        ],
        links=["README.md"],
    ),

    # ── Activation branch ────────────────────────────────────────────────────
    "activation": Node(
        id="activation",
        prompt="Windows activation issues",
        advice=[
            "1. Check status: Settings → System → Activation",
            "2. Run: slmgr.vbs /dli  in Command Prompt to see license details",
            "3. If you have a product key: Settings → Activation → Change product key",
            "4. Digital license (linked to Microsoft account): Sign in to the same MSA after reinstall",
            "5. For error codes see: docs/windows-activation.md",
            "6. Phone activation: slui 4  (reads back an Installation ID, get Confirmation ID from MS)",
        ],
        links=["docs/windows-activation.md"],
    ),
}

# Map user-facing labels to node ids at the start node
START_MENU = {
    "1": ("🖥  Blue Screen of Death (BSOD)", "bsod"),
    "2": ("🚫 Windows won't boot", "wont_boot"),
    "3": ("🐌 System is slow or unstable", "slow_unstable"),
    "4": ("⬛ No display / black screen", "no_display"),
    "5": ("🔑 Windows activation problem", "activation"),
}


# ---------------------------------------------------------------------------
# Runner (used by cli.py)
# ---------------------------------------------------------------------------

def run_tree(ask_fn, print_fn) -> None:
    """
    Drive the decision tree.

    ask_fn(prompt, choices) -> str   : asks the user a question
    print_fn(lines)                  : displays advice lines
    """
    current_id = "start"

    while True:
        node = NODES.get(current_id)
        if node is None:
            print_fn(["[Error] Unknown node – restarting.", ""])
            current_id = "start"
            continue

        # Terminal node (has advice, no more choices)
        if node.advice:
            print_fn(["", f"📋  {node.prompt}", ""])
            for line in node.advice:
                print_fn([f"   {line}"])
            if node.links:
                print_fn(["", "📚  Related docs:"])
                for link in node.links:
                    print_fn([f"   • {link}"])
            print_fn([""])
            answer = ask_fn(
                "What would you like to do next?",
                {"r": "Restart troubleshooter", "q": "Quit"},
            )
            if answer == "r":
                current_id = "start"
            else:
                break
            continue

        # Decision node
        answer = ask_fn(node.prompt, node.choices)
        if answer == "q":
            break
        next_id = node.choices.get(answer)
        if next_id:
            current_id = next_id
        else:
            print_fn(["Invalid choice, please try again."])
