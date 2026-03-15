<#
.SYNOPSIS
    Extract recent BSOD information from Windows crash dumps and Event Log.

.DESCRIPTION
    Queries the System Event Log for kernel-crash events (ID 41, 1001, 6008)
    and lists available minidump files in C:\Windows\Minidump.

    Does NOT require WinDbg or symbols — provides immediately actionable info.

.PARAMETER Days
    Number of days back to search Event Log. Default: 30.

.PARAMETER MaxEvents
    Maximum number of events to display. Default: 20.

.PARAMETER OpenDumpFolder
    Open the Minidump folder in Explorer after the check.

.EXAMPLE
    .\Get-BSODInfo.ps1
    .\Get-BSODInfo.ps1 -Days 7 -MaxEvents 10
    .\Get-BSODInfo.ps1 -OpenDumpFolder

.NOTES
    Run as Administrator to access all Event Log entries and dump files.
#>

[CmdletBinding()]
param(
    [int]   $Days         = 30,
    [int]   $MaxEvents    = 20,
    [switch]$OpenDumpFolder
)

#Requires -Version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

function Write-Header([string]$Text) {
    Write-Host "`n$('─' * 64)" -ForegroundColor DarkCyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "$('─' * 64)" -ForegroundColor DarkCyan
}

Write-Host ""
Write-Host "  ┌─────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "  │   BlueScreenHelp — BSOD Info Collector  │" -ForegroundColor Cyan
Write-Host "  └─────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Searching last $Days day(s) of event logs…" -ForegroundColor Gray

# ── Event Log query ───────────────────────────────────────────────────────────

Write-Header "Kernel Crash Events (Event IDs 41, 1001, 6008)"

$since  = (Get-Date).AddDays(-$Days)
$events = Get-WinEvent -FilterHashtable @{
    LogName   = 'System'
    Id        = 41, 1001, 6008
    StartTime = $since
} -MaxEvents $MaxEvents -ErrorAction SilentlyContinue

$idDescriptions = @{
    41   = "Kernel-Power (unexpected shutdown / reboot — likely BSOD or power loss)"
    1001 = "BugCheck (BSOD collected a minidump)"
    6008 = "EventLog (unexpected system shutdown)"
}

if ($events) {
    Write-Host "  Found $($events.Count) event(s):" -ForegroundColor Yellow
    Write-Host ""
    foreach ($ev in $events) {
        $desc = $idDescriptions[$ev.Id]
        Write-Host "  [$($ev.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))]" -ForegroundColor DarkYellow -NoNewline
        Write-Host "  Event ID $($ev.Id)" -ForegroundColor Yellow -NoNewline
        Write-Host "  — $desc" -ForegroundColor Gray

        # Try to extract BugCheck code / stop code from message
        if ($ev.Message -match 'BugcheckCode\s*:\s*(\d+)|0x([0-9A-Fa-f]+)') {
            $code = $Matches[0]
            Write-Host "    Stop Code: $code" -ForegroundColor Red
        }

        # Show first 200 chars of message
        $snippet = ($ev.Message -replace '\s+', ' ').Substring(0, [Math]::Min(200, $ev.Message.Length))
        Write-Host "    $snippet" -ForegroundColor DarkGray
        Write-Host ""
    }
} else {
    Write-Host "  ✅  No BSOD or unexpected-shutdown events in the last $Days day(s)." -ForegroundColor Green
}

# ── Minidump files ────────────────────────────────────────────────────────────

Write-Header "Minidump Files"

$dumpPath = "$env:SystemRoot\Minidump"
if (Test-Path $dumpPath) {
    $dumps = Get-ChildItem -Path $dumpPath -Filter "*.dmp" -ErrorAction SilentlyContinue |
             Sort-Object LastWriteTime -Descending |
             Select-Object -First 10

    if ($dumps) {
        Write-Host "  Found $($dumps.Count) dump file(s) in $dumpPath :" -ForegroundColor Yellow
        Write-Host ""
        foreach ($dump in $dumps) {
            $sizeKB = [math]::Round($dump.Length / 1KB, 0)
            Write-Host "    $($dump.Name)   [$sizeKB KB]   $($dump.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
        }
        Write-Host ""
        Write-Host "  To analyse dump files, use WinDbg:" -ForegroundColor Cyan
        Write-Host "    winget install Microsoft.WinDbg" -ForegroundColor White
        Write-Host "    Open WinDbg → File → Open Crash Dump → run: !analyze -v" -ForegroundColor White
        Write-Host ""
        Write-Host "  Or upload to https://www.osronline.com/page.cfm?name=analyze for free online analysis." -ForegroundColor Gray
    } else {
        Write-Host "  ✅  No minidump files found — crash dumps may be disabled." -ForegroundColor Green
    }
} else {
    Write-Host "  ℹ️   Minidump folder not found ($dumpPath)." -ForegroundColor Gray
    Write-Host "  To enable small memory dumps:" -ForegroundColor Gray
    Write-Host "    SystemPropertiesAdvanced → Startup and Recovery → Small memory dump (256 KB)" -ForegroundColor White
}

# ── Memory dump settings ──────────────────────────────────────────────────────

Write-Header "Crash Dump Configuration"

try {
    $crashKey = "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl"
    $dumpType = (Get-ItemProperty $crashKey).CrashDumpEnabled

    $typeNames = @{
        0 = "None (dumps disabled)"
        1 = "Complete memory dump"
        2 = "Kernel memory dump"
        3 = "Small memory dump (minidump)"
        7 = "Automatic memory dump"
    }
    $typeName = $typeNames[$dumpType] ?? "Unknown ($dumpType)"

    if ($dumpType -eq 0) {
        Write-Host "  ⚠️   Crash dumps are DISABLED — enable them to diagnose future BSODs." -ForegroundColor Yellow
        Write-Host "    Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl' CrashDumpEnabled 3" -ForegroundColor White
    } else {
        Write-Host "  ✅  Dump type: $typeName" -ForegroundColor Green
    }

    $autoReboot = (Get-ItemProperty $crashKey).AutoReboot
    if ($autoReboot -eq 1) {
        Write-Host "  ℹ️   Auto-reboot on BSOD is ENABLED — you may miss the stop code on screen." -ForegroundColor Cyan
        Write-Host "    To disable: System Properties → Advanced → Startup & Recovery → uncheck 'Automatically restart'" -ForegroundColor Gray
    } else {
        Write-Host "  ✅  Auto-reboot is DISABLED — stop code will remain on screen after a BSOD." -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not read crash control settings." -ForegroundColor DarkGray
}

# ── Known stop codes ──────────────────────────────────────────────────────────

Write-Header "Quick Stop-Code Reference"

$stopCodes = @(
    @{ Code = "MEMORY_MANAGEMENT (0x0000001A)";        Cause = "Faulty RAM or driver memory corruption" }
    @{ Code = "PAGE_FAULT_IN_NONPAGED_AREA (0x50)";   Cause = "Driver bug or failing RAM" }
    @{ Code = "IRQL_NOT_LESS_OR_EQUAL (0xA)";         Cause = "Driver accessing invalid memory address" }
    @{ Code = "SYSTEM_SERVICE_EXCEPTION (0x3B)";       Cause = "Driver or system service crash" }
    @{ Code = "NTFS_FILE_SYSTEM (0x24)";               Cause = "NTFS driver issue or disk corruption" }
    @{ Code = "INACCESSIBLE_BOOT_DEVICE (0x7B)";       Cause = "Boot drive not readable — driver/disk issue" }
    @{ Code = "KERNEL_SECURITY_CHECK_FAILURE (0x139)"; Cause = "Driver or system data corruption detected" }
    @{ Code = "CRITICAL_PROCESS_DIED (0xEF)";          Cause = "Critical Windows process crashed" }
    @{ Code = "VIDEO_TDR_FAILURE (0x116)";             Cause = "GPU driver crash — update or roll back GPU drivers" }
    @{ Code = "DPC_WATCHDOG_VIOLATION (0x133)";        Cause = "Driver taking too long — SSD/NVMe driver issue" }
)

foreach ($sc in $stopCodes) {
    Write-Host "  • $($sc.Code)" -ForegroundColor Yellow -NoNewline
    Write-Host "  →  $($sc.Cause)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "  Full reference: https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/bug-check-code-reference2" -ForegroundColor Cyan
Write-Host ""

# ── Open dump folder ──────────────────────────────────────────────────────────

if ($OpenDumpFolder -and (Test-Path $dumpPath)) {
    Start-Process explorer.exe $dumpPath
    Write-Host "  📂 Minidump folder opened in Explorer." -ForegroundColor Cyan
}

Write-Host "$('═' * 64)" -ForegroundColor DarkCyan
Write-Host "  BSOD info collection complete." -ForegroundColor Green
Write-Host "  ➡  Run Repair-Windows.ps1 to attempt automated fixes." -ForegroundColor Cyan
Write-Host "$('═' * 64)" -ForegroundColor DarkCyan
Write-Host ""
