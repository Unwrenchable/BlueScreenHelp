# Diagnostic Tools Guide

Use these tools to identify what caused your blue screen, freeze, or boot failure. Start with the built-in Windows tools, then use free third-party tools for deeper hardware testing.

---

## Built-in Windows Tools

These run directly from within Windows or from the Windows Recovery Environment (USB boot).

### 1. Windows Memory Diagnostic

Tests your RAM for errors. RAM faults are a common cause of blue screens and random freezes.

**From within Windows:**
1. Press **Win + R**, type `mdsched.exe`, press **Enter**.
2. Choose **"Restart now and check for problems"**.
3. The PC reboots and runs tests automatically. Results appear after Windows loads back up.

**From Recovery USB (Command Prompt):**
```cmd
mdsched.exe
```

---

### 2. Check Disk (chkdsk)

Scans and repairs file system errors and bad sectors on your storage drive. Essential after a freeze or sudden power-off.

**Scan only (no fixes, safe to run while Windows is running):**
```cmd
chkdsk C:
```

**Scan and fix (requires a reboot if drive is in use):**
```cmd
chkdsk C: /f /r
```

- `/f` — fixes file system errors
- `/r` — locates bad sectors and recovers readable data (takes longer)

> Results are shown on screen and logged in Event Viewer under **Windows Logs → Application** (source: `Chkdsk`).

---

### 3. System File Checker (sfc)

Scans all protected Windows system files and replaces corrupted or missing ones. Fixes many blue screen and instability issues.

**Run in an elevated Command Prompt (or Recovery CMD):**
```cmd
sfc /scannow
```

If it reports "Windows Resource Protection found corrupt files but was unable to fix some of them," follow up with DISM.

---

### 4. DISM (Deployment Image Servicing and Management)

Repairs the Windows component store that sfc uses as its source of clean files. Run this after sfc if sfc can't fix things.

**Elevated Command Prompt:**
```cmd
DISM /Online /Cleanup-Image /CheckHealth
DISM /Online /Cleanup-Image /ScanHealth
DISM /Online /Cleanup-Image /RestoreHealth
```

Run the three commands in order. `RestoreHealth` downloads clean files from Windows Update and may take 15–30 minutes.

---

### 5. Event Viewer — Blue Screen Error Details

Windows logs every crash with an error code. Check Event Viewer to find exactly what caused the blue screen.

1. Press **Win + X** → **Event Viewer**.
2. Expand **Windows Logs** → **System**.
3. Look for events with a red **Error** level near the time of the crash.
4. Alternatively: **Windows Logs → Application** → filter by source **BugCheck** or **WER**.

Key things to note:
- **Stop code** (e.g., `CRITICAL_PROCESS_DIED`, `MEMORY_MANAGEMENT`)
- **Faulting module** (e.g., a specific driver `.sys` file)

Search the stop code on [Microsoft's BSOD reference](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/bug-check-code-reference2) for specific guidance.

---

### 6. Reliability Monitor

Gives a visual timeline of crashes, errors, and important events in plain English.

1. Press **Win + S**, type **Reliability Monitor**, open it.
2. Scroll back to when the problems started.
3. Click any red **X** (critical event) or yellow **!** (warning) to see details.

---

### 7. Device Manager — Driver Problems

A faulty or outdated driver is one of the most common BSOD causes.

1. Press **Win + X** → **Device Manager**.
2. Look for any items with a yellow **!** or red **X**.
3. Right-click a flagged device → **Update driver** or **Roll back driver**.
4. After a driver update caused the crash: **Roll back driver** restores the previous version.

---

## Free Third-Party Diagnostic Tools

These are free, trusted tools used by technicians worldwide. Download them on a working PC and run from USB.

### Hardware — RAM

| Tool | Download | Notes |
|---|---|---|
| **MemTest86** | [memtest86.com](https://www.memtest86.com/) | Gold standard for RAM testing. Bootable ISO — runs outside Windows. Run for at least 2 full passes (hours). |
| **HCI MemTest** | [hcidesign.com](https://hcidesign.com/memtest/) | Runs inside Windows. Good for quick tests while the system is still booting. |

**When to suspect RAM**: random BSODs with different stop codes each time, crashes during memory-intensive tasks, or PC won't POST.

---

### Hardware — Storage Drive

| Tool | Download | Notes |
|---|---|---|
| **CrystalDiskInfo** | [crystalmark.info](https://crystalmark.info/en/software/crystaldiskinfo/) | Reads S.M.A.R.T. health data from HDDs and SSDs. Look for "Caution" or "Bad" status. |
| **CrystalDiskMark** | [crystalmark.info](https://crystalmark.info/en/software/crystaldiskmark/) | Benchmarks read/write speeds — a sudden drop signals a failing drive. |
| **HDDScan** | [hddscan.com](https://hddscan.com/) | Deep surface scan for bad sectors on HDD/SSD. |
| **Samsung Magician** | [samsung.com](https://semiconductor.samsung.com/us/consumer-storage/magician/) | For Samsung SSDs specifically — health check, firmware updates. |
| **SeaTools** | [seagate.com](https://www.seagate.com/support/downloads/seatools/) | For Seagate and most other HDDs. Runs inside Windows or from bootable USB. |

**S.M.A.R.T. attributes to watch** in CrystalDiskInfo:
- **Reallocated Sectors Count** — drive remapping bad sectors (early warning)
- **Uncorrectable Sector Count** — data loss risk, replace soon
- **Pending Sectors** — sectors waiting to be remapped

---

### Hardware — GPU / Temperatures

| Tool | Download | Notes |
|---|---|---|
| **GPU-Z** | [techpowerup.com](https://www.techpowerup.com/gpuz/) | GPU health, temps, VRAM details |
| **HWiNFO64** | [hwinfo.com](https://www.hwinfo.com/) | Comprehensive real-time sensor monitoring (CPU, GPU, drives, fans, voltages) |
| **MSI Afterburner** | [msi.com](https://www.msi.com/Landing/afterburner) | GPU monitoring overlay; useful for spotting thermal throttling |

**Danger thresholds:**
- CPU: above 90°C under load → thermal paste or cooling issue
- GPU: above 95°C under load → thermal paste or fan issue
- SSD (NVMe): above 70°C → check airflow or add heatsink

---

### Software — Malware & System Integrity

| Tool | Download | Notes |
|---|---|---|
| **Malwarebytes Free** | [malwarebytes.com](https://www.malwarebytes.com/) | Scans for malware that can cause BSODs |
| **Microsoft Safety Scanner** | [microsoft.com](https://docs.microsoft.com/en-us/windows/security/threat-protection/intelligence/safety-scanner-download) | Official Microsoft on-demand malware scanner |

---

### All-in-One Bootable Toolkit

| Tool | Download | Notes |
|---|---|---|
| **Hiren's BootCD PE** | [hirensbootcd.org](https://www.hirensbootcd.org/) | Boots a full Windows PE environment with dozens of diagnostic and repair tools pre-installed, including disk tools, antivirus, registry editors, and password recovery. Runs entirely from USB without touching the internal drive. |

Hiren's BootCD PE includes:
- Macrium Reflect (disk imaging/backup)
- MiniTool Partition Wizard
- CrystalDiskInfo
- AIDA64 (hardware info)
- Autoruns, Process Hacker
- NirSoft utilities (password recovery, system info)
- And many more

---

## Interpreting Results — Common Scenarios

| Test Result | Likely Cause | What to Do |
|---|---|---|
| MemTest86 shows errors | Faulty RAM | Reseat RAM; test sticks one at a time; replace bad stick |
| CrystalDiskInfo shows "Caution" or bad S.M.A.R.T. | Failing drive | Back up data immediately; replace drive |
| sfc or DISM reports unfixable corruption | Corrupted Windows | Run Startup Repair from USB or do a Repair Install |
| HWiNFO shows CPU/GPU over temp thresholds | Thermal issue | Clean dust; replace thermal paste; improve airflow |
| Event Viewer shows driver name in crash | Bad driver | Roll back or update that specific driver |
| Multiple different BSOD stop codes | RAM or motherboard | Test RAM with MemTest86; check CPU socket pins |

---

## Next Steps

- Need to boot a diagnostic tool from USB? → See [USB Boot Recovery Guide](usb-boot-recovery.md)
- Need to reinstall Windows? → See [Windows Media Creation Guide](windows-media-creation.md)
- Need help with Windows licensing after reinstall? → See [Windows Activation Guide](windows-activation.md)
