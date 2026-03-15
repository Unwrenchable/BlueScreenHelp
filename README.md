# BlueScreenHelp

A comprehensive, community-maintained guide **and real plug-and-play tool** to help you recover your PC from blue screen errors and boot failures — **without losing your data**.

---

## ⚡ Quick Start — The Tool

BlueScreenHelp ships as an actual working diagnostic and recovery agent, not just docs.

### 1-Click Windows Install (PowerShell)

```powershell
# Open PowerShell (no admin needed), then:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # one-time
irm https://raw.githubusercontent.com/Unwrenchable/BlueScreenHelp/main/install.ps1 | iex
```

Or clone the repo and run locally:

```powershell
git clone https://github.com/Unwrenchable/BlueScreenHelp.git
cd BlueScreenHelp
.\install.ps1
```

Open a **new terminal**, then you're ready:

```
bsh                          # interactive menu
bsh diagnose                 # full system diagnostic (disk, RAM, BSOD events, drivers…)
bsh troubleshoot             # guided step-by-step troubleshooter
bsh report --save            # save an HTML + TXT diagnostic report to disk
bsh diagnose --ai            # optional AI-powered analysis (needs OPENAI_API_KEY)
```

### Python install (cross-platform)

```bash
pip install bluescreenhelp        # from PyPI (when published)
# or directly from source:
pip install "git+https://github.com/Unwrenchable/BlueScreenHelp.git"
```

---

## 🛠️ What the Tool Does

| Command | Description |
|---|---|
| `bsh diagnose` | Runs 10 health checks: disk SMART, RAM, BSOD event logs, DISM integrity, boot config, drivers, activation, CPU temp, network |
| `bsh diagnose --checks disk,memory` | Run only specific checks |
| `bsh diagnose --save` | Save results as HTML + TXT report |
| `bsh diagnose --ai` | Get AI-powered analysis of results |
| `bsh troubleshoot` | Interactive decision-tree covering BSOD, boot failures, slow system, no display, activation |
| `bsh info` | Quick system info snapshot |
| `bsh report` | Full diagnostic + save report |

### PowerShell scripts (no Python required)

```powershell
# Full diagnostic report (saves HTML to Desktop with -SaveReport)
.\scripts\Invoke-WindowsDiagnostic.ps1 -SaveReport

# Automated repair: SFC → DISM → chkdsk → bootrec
.\scripts\Repair-Windows.ps1

# BSOD info: event log + minidump files + stop-code reference
.\scripts\Get-BSODInfo.ps1
```

---

## 🗂️ Guide Index

| Guide | What it covers |
|---|---|
| 📖 **[This page](#troubleshooting-overview)** | Quick BIOS checks, CMOS reset, drive detection, common culprits |
| 💾 **[USB Boot Recovery Guide](docs/usb-boot-recovery.md)** | Create a bootable USB (Windows, Hiren's, Ventoy), boot from BIOS, run recovery tools |
| 🔬 **[Diagnostic Tools Guide](docs/diagnostic-tools.md)** | Built-in Windows tools + free third-party tools to identify hardware & software issues |
| 📀 **[Windows Media Creation Guide](docs/windows-media-creation.md)** | Download official Windows 10/11 ISOs, create installation USB, repair vs. clean install |
| 🔑 **[Windows Activation Guide](docs/windows-activation.md)** | Find, recover, and apply your legitimate Windows product key |

---

## Troubleshooting Overview

### Problem: PC Freezes, Then Only Boots into BIOS

Your computer freezing/locking up and then only booting into the BIOS (setup screen) instead of loading Windows is a common issue. It usually means the system can't find or properly access a bootable drive (your SSD/HDD with Windows on it), or there's a related configuration/hardware glitch triggered by whatever caused the original freeze.

Below are the most likely causes and step-by-step troubleshooting fixes, starting with the easiest/safest ones.

---

## Step 1 — Quick Checks First (No Tools Needed)

- **Unplug all non-essentials**: Disconnect external USB devices (drives, printers, extra keyboards/mice, etc.), then restart. Sometimes a faulty peripheral confuses the boot process.
- **In BIOS**:
  - Look for the **Boot** or **Boot Priority/Order** tab.
  - See if your main drive (SSD/HDD with Windows) is listed and set as first in boot order.
    - If it's **missing or not detected** → go to Step 3.
    - If **listed but still loops to BIOS** → try selecting **Load Optimized Defaults** / **Load Setup Defaults** (or similar wording), save & exit (usually F10, then Enter).
  - Check if **Secure Boot** is enabled/disabled — try toggling it and saving/exiting.
  - Look for **CSM** (Compatibility Support Module / Legacy Boot) — enable it if disabled (or vice versa), save & exit, and test.

---

## Step 2 — Reset BIOS to Defaults (Very Common Fix)

This often resolves post-freeze boot weirdness, especially if settings got corrupted.

### Option A — Reset from within BIOS (easiest)
1. Enter BIOS (usually **Del**, **F2**, or **F10** during startup).
2. Find **"Load Optimized Defaults"** or **"Reset to Default"**.
3. Select it, save & exit (**F10**, then **Enter**).

### Option B — CMOS Clear (hardware reset — recommended if Option A doesn't work)
1. Power off the PC completely and unplug the power cord.
2. Open the case.
3. Find the small round coin-cell battery on the motherboard (**CR2032**).
4. Remove it for **5–10 minutes** (or longer).
5. While it's out, press and hold the power button for **20–30 seconds** to drain residual power.
6. Put the battery back in.
7. Plug in and power on — BIOS should reset to defaults.

> **Alternative on some motherboards**: Look for a **"CLR_CMOS"** jumper or button — short the pins with a screwdriver for a few seconds (check your motherboard manual for the exact location).

After resetting, re-enter BIOS, set boot order if needed, then save & exit.

---

## Step 3 — Check Storage Drive Detection & Connections

Many cases after a freeze/lockup point to the boot drive not being seen properly.

1. In BIOS, navigate to **Storage / SATA / M.2** section.
2. Does your Windows drive appear (with correct size/model)?

### Drive IS detected, but not in boot order
- Manually set it as **#1** in the boot order.
- Disable Secure Boot if it's causing issues.
- Save & exit.

### Drive is NOT detected
Likely a hardware or connection issue:

1. Power off and unplug the power cord.
2. Open the case.
3. **For SATA drives**: Unplug and replug both the SATA data cable and the power cable. Try a different SATA port on the motherboard if possible.
4. **For M.2/NVMe SSDs**: Carefully reseat it — unscrew, lift out, push back in firmly, and resecure the screw.
5. If you have multiple drives, temporarily disconnect extras and test with only the Windows drive connected.
6. Restart and check BIOS again.

---

## Step 4 — Other Common Culprits & Next Steps

| Symptom / Situation | What to Try |
|---|---|
| Reset helped temporarily but issue returns | **Dead CMOS battery** — replace the CR2032 coin-cell battery (~$2–5 at any store) |
| Drive is detected but Windows won't load | **Corrupted Windows boot** — use a bootable USB to run Startup Repair (see USB guide) |
| Drive is not detected even after reseating | **Failing drive** — test in another PC or with a USB enclosure |
| Random freezes + boot issues | **RAM or PSU problem** — try reseating RAM sticks or testing with one stick at a time |

### How to Run Windows Startup Repair
1. Create a bootable Windows USB — see the **[USB Boot Recovery Guide](docs/usb-boot-recovery.md)**.
2. Plug it into the affected PC.
3. In BIOS, set the USB drive as the **first boot device**.
4. Boot from the USB → **Troubleshoot** → **Advanced Options** → **Startup Repair**.
5. Follow the on-screen prompts.

---

## Quick Reference: Common BIOS Entry Keys

| Brand | Key(s) |
|---|---|
| ASUS | Del, F2 |
| MSI | Del |
| Gigabyte | Del, F2 |
| ASRock | F2 |
| Dell | F2, F12 |
| HP | Esc, F10 |
| Lenovo | F1, F2, Fn+F2 |
| Acer | Del, F2 |
| Surface | Vol Down + Power |

---

## When to Seek Further Help

If none of the above steps resolve the issue, describe your setup when asking for help:
- Desktop or laptop?
- Windows version?
- SSD or HDD? (NVMe M.2 or SATA?)
- Motherboard brand/model?
- Any error messages shown?

---

## Contributing

Found a fix that worked for you? Open a pull request or issue to help others in the community!

### Developing the agent

```bash
git clone https://github.com/Unwrenchable/BlueScreenHelp.git
cd BlueScreenHelp
pip install -e ".[dev]"
pytest tests/ -v         # run all tests
bsh --help               # try the CLI
```

### Project structure

```
BlueScreenHelp/
├── agent/                   # Python CLI tool (bsh command)
│   ├── cli.py               # Click entry-point
│   ├── diagnostics.py       # Windows health checks
│   ├── troubleshooter.py    # Decision-tree troubleshooter
│   ├── reporter.py          # HTML / TXT / JSON report generator
│   └── ai_helper.py         # Optional AI-powered analysis
├── scripts/                 # PowerShell scripts (no Python needed)
│   ├── Invoke-WindowsDiagnostic.ps1
│   ├── Repair-Windows.ps1
│   └── Get-BSODInfo.ps1
├── docs/                    # Detailed written guides
│   ├── usb-boot-recovery.md
│   ├── diagnostic-tools.md
│   ├── windows-media-creation.md
│   └── windows-activation.md
├── tests/                   # pytest test suite
├── install.ps1              # 1-click Windows installer
└── pyproject.toml           # Python package config
```

