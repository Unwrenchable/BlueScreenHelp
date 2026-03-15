# Windows Media Creation Guide

Download official Windows installation media from Microsoft and write it to USB. Use this to repair, reinstall, or upgrade Windows — fully legitimate and free to download.

---

## Overview

Microsoft provides free download tools for:
- **Windows 11** (Home, Pro, Education, Enterprise)
- **Windows 10** (Home, Pro, Education, Enterprise)

You do **not** need to pay to download Windows — you only need a valid license key to activate it after installation. See the [Windows Activation Guide](windows-activation.md) if you need help with licensing.

---

## Windows 11

### Method 1 — Media Creation Tool (recommended for most users)

1. Go to **[microsoft.com/software-download/windows11](https://www.microsoft.com/software-download/windows11)**
2. Under **"Create Windows 11 Installation Media"**, click **Download Now**.
3. Run `MediaCreationToolW11.exe`.
4. Accept the license agreement.
5. On "What do you want to do?" select **"Create installation media (USB flash drive, DVD, or ISO file) for another PC"** → **Next**.
6. Select **Language**, **Edition** (Windows 11), **Architecture** (64-bit) → **Next**.
7. Select **USB flash drive** → **Next** → choose your drive → **Next**.
8. The tool downloads Windows 11 and writes it to the USB. This takes 20–60 minutes depending on your internet speed.
9. When you see **"Your USB flash drive is ready"** — done.

> **System Requirements for Windows 11:** 64-bit CPU, 4 GB RAM, 64 GB storage, TPM 2.0, Secure Boot capable, DirectX 12 GPU. If your PC doesn't meet these, use Windows 10 instead.

### Method 2 — Download ISO directly (for Rufus/Ventoy)

1. Go to **[microsoft.com/software-download/windows11](https://www.microsoft.com/software-download/windows11)**
2. Scroll to **"Download Windows 11 Disk Image (ISO) for x64 devices"**.
3. Select **Windows 11 (multi-edition ISO for x64 devices)** → **Download Now**.
4. Choose your language → **Confirm** → download the ISO (approximately 6.5 GB).
5. Use [Rufus](https://rufus.ie) or [Ventoy](https://www.ventoy.net) to write the ISO to USB.

---

## Windows 10

### Method 1 — Media Creation Tool

1. Go to **[microsoft.com/software-download/windows10](https://www.microsoft.com/software-download/windows10)**
2. Click **Download tool now**.
3. Run `MediaCreationTool.exe`.
4. Accept the license → select **"Create installation media for another PC"** → **Next**.
5. Choose language, edition, and architecture → **Next**.
6. Select **USB flash drive** → choose your drive → **Next**.
7. Wait for download and writing to complete.

### Method 2 — Download ISO directly

1. Go to **[microsoft.com/software-download/windows10ISO](https://www.microsoft.com/software-download/windows10ISO)**
   - *If visiting from a Windows PC, you'll be redirected to the Media Creation Tool page. Open the link from a non-Windows device or use the User-Agent trick in your browser developer tools to see the direct ISO download.*
2. Select the **Windows 10 (multi-edition ISO)** → choose language → download (approximately 5.8 GB).

---

## Windows Editions Explained

| Edition | Who it's for | Upgrade to it from |
|---|---|---|
| **Home** | Personal/home use | Any Windows 10/11 Home key |
| **Pro** | Power users, small businesses (BitLocker, Hyper-V, domain join) | Any Windows 10/11 Pro key or Home key + upgrade |
| **Education** | Schools and students | Education keys via school program |
| **Enterprise** | Large organizations | Volume licensing |

The Windows installation ISO downloaded via the Media Creation Tool is a **multi-edition ISO** — it contains both Home and Pro. The edition installed depends on the license key you enter.

---

## Writing the ISO to USB

### Using Rufus (recommended for ISOs)

1. Download Rufus from [rufus.ie](https://rufus.ie) (portable version, no installation required).
2. Plug in your USB drive (8 GB+ for Windows 10, 16 GB+ for Windows 11).
3. Open Rufus.
4. **Device**: select your USB drive.
5. **Boot selection**: click **SELECT** and choose the Windows ISO file.
6. **Partition scheme**:
   - Modern UEFI PC: **GPT**
   - Older PC with Legacy BIOS: **MBR**
7. **File system**: NTFS (for Windows ISOs).
8. Click **START**.
9. If prompted, Rufus may offer to download extra files (like UEFI:NTFS) — accept.
10. Confirm the wipe warning → wait for "READY" status.

### Using Ventoy (multi-ISO, pick at boot)

See the [USB Boot Recovery Guide](usb-boot-recovery.md#option-c--ventoy-advanced-multi-iso-usb) for full Ventoy setup instructions. Once Ventoy is installed on the USB, just copy Windows ISO files onto it.

---

## Which Windows Version Should I Install?

| Situation | Recommendation |
|---|---|
| PC meets Windows 11 requirements | Install Windows 11 (free upgrade from 10) |
| PC is older / doesn't meet Win 11 requirements | Install Windows 10 (supported until Oct 2025) |
| Doing a repair install (keep files/apps) | Use the same version and edition already installed |
| Clean install (start fresh) | Download whichever version you're licensed for |

> **Checking what you're licensed for**: Open **Settings → System → About** on a working Windows PC and note the **Windows specification** section (Edition and version).

---

## Repair Install vs. Clean Install

### Repair Install (keeps your files and apps)

Use when Windows is having problems but you want to keep your data:

1. Boot into your current Windows installation (if you can) or boot from USB.
2. If booting from USB: select **"Install now"** → **"I don't have a product key"** (your digital license handles it) → select your current edition → accept terms.
3. On "Which type of installation?" select **"Upgrade: Install Windows and keep files, settings, and applications"**.
4. Follow prompts. Windows reinstalls over itself, fixing system files while preserving your data.

### Clean Install (erases the drive)

Use when Windows is beyond repair, or you're setting up a new drive:

1. Boot from the Windows USB.
2. Select language → **Install now** → enter key (or skip for now) → accept terms.
3. On "Which type of installation?" select **"Custom: Install Windows only (advanced)"**.
4. Select the drive/partition → **Next**. Windows will be installed fresh.
5. **Warning**: This erases all data on the selected partition/drive.

---

## After Installation

- **Connect to the internet** — Windows will pull drivers, updates, and verify your digital license automatically.
- **Check for updates**: Settings → Windows Update → Check for updates.
- **Install drivers**: Windows usually installs drivers automatically. For specialized hardware (GPU, network adapter), visit the manufacturer's website.
- **Activate Windows**: See [Windows Activation Guide](windows-activation.md).

---

## Troubleshooting Installation Issues

| Problem | Fix |
|---|---|
| "This PC can't run Windows 11" | PC doesn't meet requirements. Use Windows 10, or enable TPM 2.0 in BIOS if your CPU supports it. |
| Setup won't detect the drive | Try a different USB port (use USB 2.0 port if USB 3.0 fails during setup). Check BIOS for SATA/NVMe mode. |
| Setup freezes or crashes | RAM issue — run MemTest86 first. Also try a different USB drive. |
| "No signed device drivers were found" | Missing storage controller driver. Add the driver to the USB and load it during setup. |
| Stuck on "Getting updates" | Disconnect from internet during install, then reconnect after. |

---

## Links Summary

| Resource | URL |
|---|---|
| Windows 11 download | [microsoft.com/software-download/windows11](https://www.microsoft.com/software-download/windows11) |
| Windows 10 download | [microsoft.com/software-download/windows10](https://www.microsoft.com/software-download/windows10) |
| Rufus | [rufus.ie](https://rufus.ie) |
| Ventoy | [ventoy.net](https://www.ventoy.net) |
| Windows 11 system requirements | [microsoft.com/windows/windows-11-specifications](https://www.microsoft.com/windows/windows-11-specifications) |
