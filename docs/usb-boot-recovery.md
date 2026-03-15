# USB Boot Recovery Guide

Boot from a USB drive to access recovery tools, repair Windows, run diagnostics, or reinstall — all without touching your internal drive.

---

## What You Need

| Item | Details |
|---|---|
| USB flash drive | At least **8 GB** (16 GB+ recommended). **All data on it will be erased.** |
| A working PC | To create the bootable USB on |
| Internet connection | To download the tools |

---

## Part 1 — Create a Bootable USB

You have two options depending on what you want on the USB:

### Option A — Official Windows Recovery Drive (easiest, built into Windows)

Creates a Microsoft-signed recovery environment: Startup Repair, Command Prompt, System Restore, and factory reset.

1. On a working Windows PC, plug in the USB drive.
2. Press **Win + S**, type **Recovery Drive**, and open it.
3. Check **"Back up system files to the recovery drive"** if you want a full reinstall option, or leave it unchecked for a lighter rescue-only drive.
4. Select your USB drive → **Next** → **Create**.
5. Wait (this can take 20–40 minutes).

> **Official guide**: [Create a recovery drive — Microsoft Support](https://support.microsoft.com/en-us/windows/create-a-recovery-drive-abb4b612-b42e-4bf8-9aeb-b2fec98b6e4d)

---

### Option B — Windows Installation Media via Microsoft Media Creation Tool (recommended for reinstall)

Downloads the latest official Windows ISO and writes it to USB. Lets you do a clean install, upgrade, or repair install.

#### Windows 11
1. Go to [microsoft.com/software-download/windows11](https://www.microsoft.com/software-download/windows11)
2. Under **"Create Windows 11 Installation Media"**, click **Download Now**.
3. Run `MediaCreationTool_Win11.exe` as Administrator.
4. Accept the license → **Create installation media for another PC** → **Next**.
5. Choose language, edition, and architecture (64-bit is standard) → **Next**.
6. Select **USB flash drive** → **Next** → pick your USB drive → **Next**.
7. The tool downloads Windows and writes it to the USB automatically. Wait for "Your USB flash drive is ready."

#### Windows 10
1. Go to [microsoft.com/software-download/windows10](https://www.microsoft.com/software-download/windows10)
2. Click **Download tool now** → run `MediaCreationTool.exe`.
3. Follow the same steps as above.

---

### Option C — Ventoy (advanced: multi-ISO USB)

[Ventoy](https://www.ventoy.net) lets you copy multiple ISO files onto one USB and pick which one to boot — ideal if you want one USB with Windows 11, Windows 10, and diagnostic tools.

1. Download the latest release from [ventoy.net/en/download.html](https://www.ventoy.net/en/download.html).
2. Extract the zip, run **Ventoy2Disk.exe**, select your USB drive, and click **Install**.
3. After installation, the USB shows as a normal drive. Simply **copy any ISO files** onto it.
4. When you boot from it, Ventoy presents a menu to choose which ISO to run.

**Recommended ISOs to put on a Ventoy USB:**
- Windows 11 ISO (from Microsoft — see below)
- Windows 10 ISO (from Microsoft — see below)
- [Hiren's BootCD PE](https://www.hirensbootcd.org/) — all-in-one diagnostic/repair toolkit
- [MemTest86](https://www.memtest86.com/) — RAM testing

#### Downloading official Windows ISOs directly
If you need raw ISO files (for Ventoy or Rufus):
- **Windows 11**: [microsoft.com/software-download/windows11](https://www.microsoft.com/software-download/windows11) → scroll to "Download Windows 11 Disk Image (ISO)"
- **Windows 10**: [microsoft.com/software-download/windows10ISO](https://www.microsoft.com/software-download/windows10ISO)

> **Note**: The direct ISO download links appear when visiting from a non-Windows browser. On Windows, use the Media Creation Tool instead or use the Ventoy/Rufus workflow.

---

### Option D — Rufus (fast, flexible USB writer)

[Rufus](https://rufus.ie) is a free, open-source tool that writes ISO files to USB drives very quickly.

1. Download Rufus from [rufus.ie](https://rufus.ie) (portable version, no install needed).
2. Plug in USB drive and open Rufus.
3. Under **Device**, select your USB drive.
4. Under **Boot selection**, click **SELECT** and choose your ISO file.
5. Rufus auto-detects the partition scheme. For modern PCs: **GPT** + **UEFI (non CSM)**. For older PCs: **MBR** + **BIOS or UEFI-CSM**.
6. Click **START** → confirm the wipe warning → wait for completion.

---

## Part 2 — Boot from the USB in BIOS

### Step 1 — Enter BIOS/UEFI

Restart the PC and press the BIOS key immediately after the manufacturer logo appears:

| Brand | Key |
|---|---|
| ASUS | Del or F2 |
| MSI | Del |
| Gigabyte | Del or F2 |
| ASRock | F2 |
| Dell | F2 (BIOS) or F12 (boot menu) |
| HP | Esc or F10 |
| Lenovo | F1, F2, or Fn+F2 |
| Acer | Del or F2 |
| Surface | Hold Volume Down while pressing Power |

> **Tip**: Most systems also have a **one-time boot menu** (F11, F12, or Esc) that lets you pick USB without changing BIOS settings permanently.

### Step 2 — Set USB as First Boot Device

In BIOS, go to the **Boot** tab and move your USB drive to position **#1** in the boot order. Save & exit (usually **F10 + Enter**).

### Step 3 — Handle Secure Boot (if USB won't boot)

If the PC refuses to boot from USB:
1. In BIOS → **Security** or **Boot** tab → **Secure Boot** → **Disabled**.
2. Save & exit, then try booting from USB again.
3. After you're done with recovery, re-enable Secure Boot if desired.

> **Why this matters**: Windows signed media (from Microsoft's tool) works with Secure Boot on. Third-party tools like Hiren's BootCD may require Secure Boot to be temporarily disabled.

### Step 4 — Boot into the Recovery Environment

After booting from USB you'll land in one of these environments depending on what you created:

| USB Type | What you see |
|---|---|
| Windows Recovery Drive | "Choose your keyboard layout" → blue recovery screen |
| Windows Installation Media | "Install Windows" setup screen — choose "Repair your computer" at the bottom left |
| Ventoy | Ventoy boot menu — select the ISO to run |
| Hiren's BootCD PE | Hiren's desktop with tools pre-loaded |

---

## Part 3 — What to Do Once Booted from USB

### From the Windows Recovery Environment (blue screen with options)

Navigate: **Troubleshoot → Advanced Options**

| Tool | What it does |
|---|---|
| **Startup Repair** | Automatically detects and fixes common boot problems |
| **System Restore** | Rolls Windows back to a saved restore point |
| **System Image Recovery** | Restores from a full backup image |
| **Command Prompt** | Manual repairs — see commands below |
| **Uninstall Updates** | Removes a recent Windows Update that broke things |
| **UEFI Firmware Settings** | Reboots into BIOS |

### Useful Command Prompt Commands (run from recovery CMD)

```cmd
# Check and fix the file system on the Windows drive (usually C:)
chkdsk C: /f /r

# Repair the boot sector
bootrec /fixmbr
bootrec /fixboot
bootrec /rebuildbcd

# Find the correct Windows drive letter (if C: isn't Windows)
diskpart
  list volume
  exit

# Repair Windows system files
sfc /scannow

# Repair the Windows image
DISM /Online /Cleanup-Image /RestoreHealth
```

---

## Next Steps

- Need to diagnose what went wrong? → See [Diagnostic Tools Guide](diagnostic-tools.md)
- Need to create Windows installation media or download ISOs? → See [Windows Media Creation Guide](windows-media-creation.md)
- Need help with Windows licensing and activation? → See [Windows Activation Guide](windows-activation.md)
