# Data Recovery Guide

This guide explains how to use BlueScreenHelp's built-in data recovery tools to rescue your personal files from failing, corrupted, or unbootable drives.

---

## Overview

BlueScreenHelp includes real data recovery capabilities that can:

- ✅ Recover files from drives that won't boot or mount
- ✅ Extract data even when the file system is corrupted
- ✅ Handle bad sectors gracefully during recovery
- ✅ Support 30+ file types including photos, documents, videos, and archives
- ✅ Create disk images for later recovery attempts
- ✅ Work with NTFS, FAT32, FAT16, and exFAT file systems

---

## When to Use Data Recovery

Use these tools when:

- Your drive won't boot Windows
- You see "Operating System Not Found" or similar errors
- Drive shows as RAW or unformatted in Disk Management
- Windows reports "Drive needs to be formatted"
- Drive makes clicking noises (failing hardware)
- You accidentally deleted files and need them back
- File system is corrupted after a crash or power failure

---

## Quick Start

### Step 1: List Available Drives

First, see what drives are available:

```bash
bsh scan-drive -d list
```

This shows all physical drives and volumes with their model, size, and device path.

### Step 2: Scan a Specific Drive

Before recovering, assess the drive's condition:

```bash
bsh scan-drive -d "\\.\PhysicalDrive0"
```

Or for a specific volume:

```bash
bsh scan-drive -d "\\.\C:"
```

This tells you:
- Whether the drive is accessible
- What file system it uses
- Recommended recovery methods
- Estimated chances of success

### Step 3: Recover Files

Basic recovery (all file types):

```bash
bsh recover -d "\\.\C:" -o D:\Recovery
```

Recover only photos and documents:

```bash
bsh recover -d "\\.\PhysicalDrive1" -o D:\Recovery --types jpg,png,pdf,docx
```

Scan without recovering (dry run):

```bash
bsh recover -d "\\.\PhysicalDrive0" -o D:\Recovery --scan-only
```

---

## Recovery Methods

BlueScreenHelp supports two recovery methods:

### 1. File Carving (Default)

**Best for:** Corrupted file systems, formatted drives, drives that won't mount

File carving scans the raw disk data looking for file signatures (magic bytes) that identify file types. It can find files even when the file system is completely destroyed.

```bash
bsh recover -d "\\.\PhysicalDrive0" -o D:\Recovery --method carving
```

**Pros:**
- Works when file system is corrupted
- Can recover from formatted drives
- Doesn't need file system metadata

**Cons:**
- Original filenames are lost (files named as `recovered_001_<offset>.jpg`)
- Slower than filesystem-based recovery
- May recover file fragments or corrupt files

### 2. File System Scanning

**Best for:** Drives with intact file systems, recovering specific deleted files

Reads the NTFS Master File Table (MFT) or FAT32 directory structures to find files with their original names and paths.

```bash
bsh recover -d "\\.\C:" -o D:\Recovery --method filesystem
```

**Pros:**
- Preserves original filenames and folder structure
- Faster than carving
- More accurate file boundaries

**Cons:**
- Requires intact file system metadata
- Won't work on formatted or severely corrupted drives

### 3. Both Methods

For maximum recovery, use both methods:

```bash
bsh recover -d "\\.\PhysicalDrive0" -o D:\Recovery --method both
```

This runs file system scanning first (fast), then file carving (comprehensive).

---

## Supported File Types

BlueScreenHelp can recover 30+ file types by signature:

### Images
- JPG/JPEG (`.jpg`)
- PNG (`.png`)
- GIF (`.gif`)
- BMP (`.bmp`)
- TIFF (`.tif`)

### Documents
- PDF (`.pdf`)
- Microsoft Word (`.docx`, `.doc`)
- Microsoft Excel (`.xlsx`, `.xls`)
- Microsoft PowerPoint (`.pptx`, `.ppt`)
- Rich Text Format (`.rtf`)

### Archives
- ZIP (`.zip`)
- RAR (`.rar`)
- 7-Zip (`.7z`)
- GZip (`.gz`)

### Video
- MP4 (`.mp4`)
- AVI (`.avi`)
- QuickTime (`.mov`)
- Windows Media (`.wmv`)

### Audio
- MP3 (`.mp3`)
- WAV (`.wav`)
- FLAC (`.flac`)
- M4A (`.m4a`)

### Other
- Windows Executables (`.exe`, `.dll`)
- SQLite Databases (`.sqlite`)
- Microsoft Access (`.mdb`)

---

## Advanced Usage

### Creating a Disk Image

For severely damaged drives, create a disk image first. This preserves the current state and lets you attempt recovery multiple times without further stressing the failing drive.

```bash
bsh image-drive -d "\\.\PhysicalDrive0" -o D:\backup.img
```

Then recover from the image:

```bash
bsh recover -d D:\backup.img -o D:\Recovery
```

**Note:** Disk imaging can take several hours for large drives. The `--skip-bad-sectors` flag (enabled by default) writes zeros for unreadable sectors instead of failing.

### Drive Path Syntax

**Physical drives (entire disk):**
- Windows: `\\.\PhysicalDrive0`, `\\.\PhysicalDrive1`, etc.
- Linux: `/dev/sda`, `/dev/sdb`, etc.
- macOS: `/dev/disk0`, `/dev/disk1`, etc.

**Logical volumes (partitions):**
- Windows: `\\.\C:`, `\\.\D:`, etc.
- Linux: `/dev/sda1`, `/dev/sdb1`, etc.

**Tip:** Use `bsh scan-drive -d list` to see exact paths.

---

## Best Practices

### Before Recovery

1. **Stop using the drive immediately** - Every write reduces recovery chances
2. **Don't attempt repairs** - Running chkdsk or format will overwrite recoverable data
3. **Use a different drive for output** - Never save recovered files to the same drive
4. **Have enough space** - Ensure your output drive has more free space than the source drive size
5. **Run as Administrator** - Required for low-level drive access on Windows

### During Recovery

1. **Be patient** - Recovery can take hours for large drives
2. **Monitor progress** - BlueScreenHelp reports progress every 100MB
3. **Don't interrupt** - Let the recovery complete; partial results are saved

### After Recovery

1. **Check recovered files** - Some files may be incomplete or corrupted
2. **Sort by size** - Often helps identify valid files vs. fragments
3. **Use file viewers** - Open files to verify they're intact
4. **Backup immediately** - Copy recovered files to a safe location

---

## Troubleshooting

### "Cannot access drive" or "Access Denied"

**Solution:** Run your terminal as Administrator (Windows) or use `sudo` (Linux/macOS).

Windows PowerShell:
```powershell
Start-Process powershell -Verb RunAs
bsh recover -d "\\.\PhysicalDrive0" -o D:\Recovery
```

### Drive Not Detected

1. Check BIOS/UEFI - Is the drive listed?
2. Check cables - Reseat SATA/power cables
3. Try a different port - Use another SATA port on motherboard
4. Use external adapter - Put drive in USB enclosure and scan as external drive

### Recovery Finds No Files

1. Try both recovery methods: `--method both`
2. Check if drive is encrypted (BitLocker, FileVault, LUKS)
3. Drive may be physically damaged beyond software recovery
4. Consider professional data recovery service

### Recovered Files Are Corrupted

- **Fragmented files** - File carving can't handle fragmented files well
- **Overwritten data** - Files were partially overwritten
- **Bad sectors** - Physical damage to disk surface
- **Try filesystem method** - If the MFT is intact, it tracks fragmentation

### Recovery Is Very Slow

- **Normal for large drives** - A 1TB drive can take 4-8 hours
- **Bad sectors** - Drive retrying failed reads (clicking noises)
- **Consider disk imaging first** - Create image, then recover from image

---

## Important Warnings

### Data Privacy

Recovered files are written in plain text to the output directory. If you're recovering sensitive data:

1. Use an encrypted output drive
2. Securely delete the output directory when done
3. Don't leave recovered files on shared computers

### Drive Health

File carving involves reading the entire drive surface. If your drive is making clicking noises or has SMART warnings:

1. **Create a disk image first** - Use `bsh image-drive`
2. **Don't run recovery multiple times** - Each read stresses the failing drive
3. **Consider professional recovery** - For irreplaceable data, pay experts

### Legal Considerations

Only recover data from drives you own or have explicit permission to access. Unauthorized data recovery may violate:

- Computer Fraud and Abuse Act (USA)
- Computer Misuse Act (UK)
- Similar laws in other countries

---

## Example Workflows

### Scenario 1: Drive Won't Boot, Need Photos

You have a laptop with a corrupted drive. Windows won't start, but you need your family photos.

```bash
# 1. Put drive in external USB enclosure
# 2. Connect to working PC

# 3. List drives and find the external drive
bsh scan-drive -d list

# 4. Scan the drive (let's say it shows as PhysicalDrive1)
bsh scan-drive -d "\\.\PhysicalDrive1"

# 5. Recover only image files
bsh recover -d "\\.\PhysicalDrive1" -o D:\Recovery --types jpg,png,gif,bmp,heic

# 6. Check the D:\Recovery folder for your photos
```

### Scenario 2: Accidentally Formatted Drive

You formatted the wrong drive and need to recover everything.

```bash
# 1. STOP USING THE DRIVE IMMEDIATELY
# 2. Don't copy anything to it

# 3. Scan the formatted drive
bsh scan-drive -d "\\.\D:"

# 4. Use carving to recover (filesystem is gone after format)
bsh recover -d "\\.\D:" -o E:\Recovery --method carving

# 5. This will take hours - let it run
# 6. Sort recovered files by type and size
```

### Scenario 3: Drive Making Clicking Noises

Your hard drive is clicking and might die soon. Get critical documents off now.

```bash
# 1. Create disk image FIRST (before drive dies completely)
bsh image-drive -d "\\.\PhysicalDrive0" -o D:\drive_backup.img --skip-bad-sectors

# 2. Now recover from the image (safe, can retry)
bsh recover -d D:\drive_backup.img -o D:\Recovery --types pdf,docx,xlsx

# 3. Stop using the failing drive
# 4. Order a replacement drive
```

---

## When to Seek Professional Help

Consider professional data recovery services if:

- ❌ Drive not detected in BIOS at all
- ❌ Drive making loud clicking, grinding, or beeping noises
- ❌ Drive suffered physical damage (dropped, water damage)
- ❌ Data is business-critical or irreplaceable
- ❌ Drive is encrypted and you lost the key
- ❌ Software recovery finds nothing after multiple attempts

Professional recovery can cost $500-$3,000+ but can recover data from drives with:

- Failed read/write heads
- Damaged platters
- Controller board failures
- Severe physical damage

---

## Additional Resources

- [Diagnostic Tools Guide](diagnostic-tools.md) - Test drive health before recovery
- [USB Boot Recovery Guide](usb-boot-recovery.md) - Boot from USB for offline recovery
- GitHub Issues: Report bugs or request features

---

## Legal Disclaimer

BlueScreenHelp's data recovery tools are provided "as is" without warranty. Data recovery is performed at your own risk. The authors are not responsible for:

- Data loss during recovery attempts
- Damage to drives during recovery operations
- Unauthorized use of recovery tools
- Legal consequences of recovering data without permission

Always back up your important data regularly.
