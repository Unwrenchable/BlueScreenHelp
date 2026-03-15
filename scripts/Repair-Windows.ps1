<#
.SYNOPSIS
    Automated Windows repair — BlueScreenHelp

.DESCRIPTION
    Runs a series of Windows repair operations in order:
      1. SFC (System File Checker)
      2. DISM RestoreHealth
      3. Check Disk (schedules for next reboot if C: is locked)
      4. Boot record repair (MBR/BCD)

    Safe to run on a healthy system — each step reports what it finds.

.PARAMETER SkipSFC
    Skip the System File Checker step.

.PARAMETER SkipDISM
    Skip the DISM RestoreHealth step.

.PARAMETER SkipChkdsk
    Skip scheduling Check Disk.

.PARAMETER SkipBootRepair
    Skip boot record repair.

.EXAMPLE
    .\Repair-Windows.ps1
    .\Repair-Windows.ps1 -SkipChkdsk -SkipBootRepair

.NOTES
    Must be run as Administrator.
    Boot record repair requires WinRE / Recovery Console if Windows won't start.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$SkipSFC,
    [switch]$SkipDISM,
    [switch]$SkipChkdsk,
    [switch]$SkipBootRepair
)

#Requires -Version 5.1
#Requires -RunAsAdministrator

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

function Write-Step([int]$n, [string]$text) {
    Write-Host "`n[$n] " -NoNewline -ForegroundColor Cyan
    Write-Host $text -ForegroundColor White
    Write-Host "$('─' * 60)" -ForegroundColor DarkCyan
}

function Write-Result([bool]$ok, [string]$text) {
    if ($ok) {
        Write-Host "  ✅  $text" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️   $text" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   BlueScreenHelp — Windows Repair Tool   ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Running as: $($env:USERNAME)" -ForegroundColor Gray
Write-Host "  Date/Time : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# ── Step 1: SFC ───────────────────────────────────────────────────────────────

if (-not $SkipSFC) {
    Write-Step 1 "System File Checker (sfc /scannow)"
    Write-Host "  This may take several minutes…" -ForegroundColor Gray

    $sfcResult = & sfc /scannow 2>&1
    $sfcOK = $LASTEXITCODE -eq 0

    if ($sfcResult -join '' | Select-String 'did not find any integrity violations', 'successfully repaired') {
        Write-Result $true "SFC completed — no integrity violations or repairs made successfully."
    } elseif ($sfcResult -join '' | Select-String 'found corrupt files') {
        Write-Host "  ⚠️   SFC found and repaired corrupt files. Run DISM to ensure full repair." -ForegroundColor Yellow
    } else {
        Write-Result $sfcOK "SFC completed (exit code $LASTEXITCODE)."
    }
    Write-Host ($sfcResult -join "`n") -ForegroundColor DarkGray
} else {
    Write-Host "`n[1] SFC — SKIPPED" -ForegroundColor DarkGray
}

# ── Step 2: DISM ──────────────────────────────────────────────────────────────

if (-not $SkipDISM) {
    Write-Step 2 "DISM — Restore Windows Component Store"
    Write-Host "  This may take 10-20 minutes and requires internet access…" -ForegroundColor Gray

    $dismResult = & dism /Online /Cleanup-Image /RestoreHealth 2>&1
    $dismOK = $LASTEXITCODE -eq 0

    if ($dismResult -join '' | Select-String 'The restore operation completed successfully') {
        Write-Result $true "DISM RestoreHealth completed successfully."
    } elseif ($dismResult -join '' | Select-String 'No component store corruption detected') {
        Write-Result $true "DISM: No component store corruption detected."
    } else {
        Write-Result $dismOK "DISM completed (exit code $LASTEXITCODE)."
    }
    Write-Host ($dismResult | Select-Object -Last 5 | Out-String).Trim() -ForegroundColor DarkGray
} else {
    Write-Host "`n[2] DISM — SKIPPED" -ForegroundColor DarkGray
}

# ── Step 3: Check Disk ────────────────────────────────────────────────────────

if (-not $SkipChkdsk) {
    Write-Step 3 "Check Disk (chkdsk C: /f /r)"
    Write-Host "  The C: drive is in use — scheduling chkdsk for next reboot." -ForegroundColor Gray

    if ($PSCmdlet.ShouldProcess("C:", "Schedule chkdsk /f /r")) {
        $chkdskResult = & chkdsk C: /f /r 2>&1
        # chkdsk exits 0 (no errors) or 1 (errors found/fixed) or 2 (disk dirty, scheduled)
        if ($LASTEXITCODE -le 1) {
            Write-Result $true "chkdsk scheduled — will run on next reboot."
        } else {
            Write-Result $false "chkdsk returned exit code $LASTEXITCODE."
        }
        Write-Host ($chkdskResult | Select-Object -Last 3 | Out-String).Trim() -ForegroundColor DarkGray
    }
} else {
    Write-Host "`n[3] Check Disk — SKIPPED" -ForegroundColor DarkGray
}

# ── Step 4: Boot Record ───────────────────────────────────────────────────────

if (-not $SkipBootRepair) {
    Write-Step 4 "Boot Record Repair (bootrec)"
    Write-Host "  Note: bootrec is most effective from Windows Recovery Environment (WinRE)." -ForegroundColor Gray
    Write-Host "  Running from live Windows may produce 'Access Denied' for some operations." -ForegroundColor DarkGray

    if ($PSCmdlet.ShouldProcess("BCD", "Run bootrec /fixmbr, /fixboot, /rebuildbcd")) {
        $r1 = & bootrec /fixmbr  2>&1; Write-Host "  /fixmbr  : $($r1 -join ' ')" -ForegroundColor DarkGray
        $r2 = & bootrec /fixboot 2>&1; Write-Host "  /fixboot : $($r2 -join ' ')" -ForegroundColor DarkGray
        $r3 = & bootrec /rebuildbcd 2>&1
        Write-Host "  /rebuildbcd:`n$($r3 | Select-Object -Last 5 | Out-String)" -ForegroundColor DarkGray
        Write-Result ($LASTEXITCODE -eq 0) "Boot record repair completed."
    }
} else {
    Write-Host "`n[4] Boot Record — SKIPPED" -ForegroundColor DarkGray
}

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "$('═' * 62)" -ForegroundColor Cyan
Write-Host "  Repair sequence complete." -ForegroundColor Green
Write-Host "  ➡  Restart your PC to apply chkdsk and any SFC repairs." -ForegroundColor Cyan
Write-Host "  ➡  After reboot, run Invoke-WindowsDiagnostic.ps1 to verify." -ForegroundColor Cyan
Write-Host "$('═' * 62)" -ForegroundColor Cyan
Write-Host ""
