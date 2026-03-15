<#
.SYNOPSIS
    Full Windows system diagnostic — BlueScreenHelp

.DESCRIPTION
    Collects system health information, checks for BSOD events, disk health,
    RAM, driver issues, Windows integrity and activation status.
    Outputs a colour-coded console report and optionally saves an HTML report.

.PARAMETER SaveReport
    Save an HTML report to the Desktop.

.PARAMETER OutputPath
    Custom path for the saved report (overrides SaveReport default location).

.EXAMPLE
    .\Invoke-WindowsDiagnostic.ps1
    .\Invoke-WindowsDiagnostic.ps1 -SaveReport
    .\Invoke-WindowsDiagnostic.ps1 -SaveReport -OutputPath C:\Temp\report.html

.NOTES
    Run as Administrator for full disk-health and Event-Log access.
#>

[CmdletBinding()]
param(
    [switch]$SaveReport,
    [string]$OutputPath
)

#Requires -Version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

# ── Colour helpers ────────────────────────────────────────────────────────────

function Write-Header([string]$Text) {
    Write-Host "`n$('─' * 62)" -ForegroundColor DarkCyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "$('─' * 62)" -ForegroundColor DarkCyan
}

function Write-OK([string]$Label, [string]$Value) {
    Write-Host "  ✅  " -NoNewline -ForegroundColor Green
    Write-Host "$Label" -NoNewline -ForegroundColor White
    if ($Value) { Write-Host " — $Value" -ForegroundColor Gray } else { Write-Host "" }
}

function Write-Warn([string]$Label, [string]$Value) {
    Write-Host "  ⚠️   " -NoNewline -ForegroundColor Yellow
    Write-Host "$Label" -NoNewline -ForegroundColor Yellow
    if ($Value) { Write-Host " — $Value" -ForegroundColor Gray } else { Write-Host "" }
}

function Write-Err([string]$Label, [string]$Value) {
    Write-Host "  ❌  " -NoNewline -ForegroundColor Red
    Write-Host "$Label" -NoNewline -ForegroundColor Red
    if ($Value) { Write-Host " — $Value" -ForegroundColor Gray } else { Write-Host "" }
}

function Write-Info([string]$Label, [string]$Value) {
    Write-Host "  ℹ️   " -NoNewline -ForegroundColor Cyan
    Write-Host "$Label" -NoNewline -ForegroundColor White
    if ($Value) { Write-Host " — $Value" -ForegroundColor Gray } else { Write-Host "" }
}

# ── Report accumulator for HTML ───────────────────────────────────────────────

$ReportRows = [System.Collections.Generic.List[pscustomobject]]::new()

function Add-Row([string]$Section, [string]$Status, [string]$Label, [string]$Detail) {
    $ReportRows.Add([pscustomobject]@{
        Section = $Section
        Status  = $Status
        Label   = $Label
        Detail  = $Detail
    })
}

# ── 1. OS Info ────────────────────────────────────────────────────────────────

Write-Header "OS & System Info"

$os   = Get-CimInstance Win32_OperatingSystem
$cs   = Get-CimInstance Win32_ComputerSystem
$bios = Get-CimInstance Win32_BIOS

Write-Info "Computer"  "$($cs.Name)  ($($cs.Manufacturer) $($cs.Model))"
Write-Info "OS"        "$($os.Caption) Build $($os.BuildNumber) ($($os.OSArchitecture))"
Write-Info "BIOS"      "$($bios.Manufacturer) $($bios.SMBIOSBIOSVersion) (Released: $($bios.ReleaseDate))"
Write-Info "Uptime"    "$((Get-Date) - $os.LastBootUpTime | Select-Object -ExpandProperty TotalHours | [math]::Round(1)) hours"

Add-Row "OS" "info" "Computer" "$($cs.Name) — $($cs.Manufacturer) $($cs.Model)"
Add-Row "OS" "info" "OS" "$($os.Caption) Build $($os.BuildNumber)"
Add-Row "OS" "info" "BIOS" "$($bios.Manufacturer) $($bios.SMBIOSBIOSVersion)"

# ── 2. RAM ────────────────────────────────────────────────────────────────────

Write-Header "RAM"

$ram = Get-CimInstance Win32_PhysicalMemory
if ($ram) {
    $totalGB = [math]::Round(($ram | Measure-Object -Property Capacity -Sum).Sum / 1GB, 1)
    Write-OK "Total RAM" "$totalGB GB"
    Add-Row "RAM" "ok" "Total RAM" "$totalGB GB"
    foreach ($stick in $ram) {
        $gb = [math]::Round($stick.Capacity / 1GB, 1)
        Write-Info "  Module" "$($stick.Manufacturer) $gb GB @ $($stick.Speed) MHz"
        Add-Row "RAM" "info" "Module" "$($stick.Manufacturer) $gb GB @ $($stick.Speed) MHz"
    }
} else {
    Write-Warn "RAM" "Could not query RAM (try running as Administrator)"
    Add-Row "RAM" "warning" "RAM" "Query failed"
}

# ── 3. Disk Health ────────────────────────────────────────────────────────────

Write-Header "Disk Health"

$disks = Get-PhysicalDisk
if ($disks) {
    foreach ($disk in $disks) {
        $sizeGB = [math]::Round($disk.Size / 1GB, 1)
        $label  = "$($disk.FriendlyName) ($($disk.MediaType)) $sizeGB GB"
        if ($disk.HealthStatus -eq 'Healthy') {
            Write-OK $label "Health: $($disk.HealthStatus)"
            Add-Row "Disk" "ok" $label "Health: $($disk.HealthStatus)"
        } else {
            Write-Warn $label "Health: $($disk.HealthStatus)"
            Add-Row "Disk" "warning" $label "Health: $($disk.HealthStatus)"
        }
    }
} else {
    Write-Warn "Disk" "Could not query disk health (run as Administrator)"
    Add-Row "Disk" "warning" "Disk" "Query failed — run as Administrator"
}

# ── 4. BSOD / Crash Events ────────────────────────────────────────────────────

Write-Header "Recent BSOD / Crash Events (last 30 days)"

$since  = (Get-Date).AddDays(-30)
$events = Get-WinEvent -FilterHashtable @{
    LogName   = 'System'
    Id        = 41, 1001, 6008
    StartTime = $since
} -MaxEvents 20 -ErrorAction SilentlyContinue

if ($events) {
    Write-Warn "Crash events found" "$($events.Count) event(s) in the last 30 days"
    Add-Row "BSOD" "warning" "Crash events" "$($events.Count) event(s) in last 30 days"
    foreach ($ev in $events | Select-Object -First 5) {
        $msg = ($ev.Message -replace '\s+', ' ').Substring(0, [Math]::Min(80, $ev.Message.Length))
        Write-Host "      [$($ev.TimeCreated.ToString('yyyy-MM-dd HH:mm'))] ID $($ev.Id) — $msg" -ForegroundColor DarkGray
        Add-Row "BSOD" "warning" "Event $($ev.Id) @ $($ev.TimeCreated.ToString('yyyy-MM-dd HH:mm'))" $msg
    }
} else {
    Write-OK "No crash events" "No BSOD or unexpected shutdown events in the last 30 days"
    Add-Row "BSOD" "ok" "No crash events" "Clean for 30 days"
}

# ── 5. Windows Integrity (DISM) ───────────────────────────────────────────────

Write-Header "Windows Component Store (DISM CheckHealth)"

$dismResult = & dism /Online /Cleanup-Image /CheckHealth 2>&1
if ($LASTEXITCODE -eq 0 -and ($dismResult -join '') -match 'No component store corruption detected') {
    Write-OK "Windows image" "No corruption detected"
    Add-Row "DISM" "ok" "Windows image" "No corruption detected"
} else {
    Write-Warn "Windows image" "Possible corruption — run Repair-Windows.ps1"
    Add-Row "DISM" "warning" "Windows image" "Possible corruption — run Repair-Windows.ps1"
}

# ── 6. Activation Status ──────────────────────────────────────────────────────

Write-Header "Windows Activation"

$slmgr = & cscript //NoLogo "$env:SystemRoot\System32\slmgr.vbs" /dli 2>&1
$slmgrText = $slmgr -join "`n"
if ($slmgrText -match 'Licensed') {
    Write-OK "Activation" "Windows is activated"
    Add-Row "Activation" "ok" "Activation" "Licensed"
} elseif ($slmgrText -match 'Notification|Grace') {
    Write-Warn "Activation" "NOT activated or in grace period"
    Add-Row "Activation" "warning" "Activation" "Not activated"
} else {
    Write-Info "Activation" "Could not determine status"
    Add-Row "Activation" "info" "Activation" "Unknown"
}

# ── 7. Driver Issues ──────────────────────────────────────────────────────────

Write-Header "Driver Status"

$badDevices = Get-PnpDevice | Where-Object { $_.Status -ne 'OK' } -ErrorAction SilentlyContinue
if ($badDevices) {
    Write-Warn "Driver issues" "$($badDevices.Count) device(s) with problems"
    Add-Row "Drivers" "warning" "Driver issues" "$($badDevices.Count) problem device(s)"
    foreach ($dev in $badDevices | Select-Object -First 10) {
        Write-Host "      [$($dev.Status)] $($dev.FriendlyName) ($($dev.Class))" -ForegroundColor DarkYellow
        Add-Row "Drivers" "warning" "  $($dev.FriendlyName)" "$($dev.Status)"
    }
} else {
    Write-OK "Drivers" "All devices OK"
    Add-Row "Drivers" "ok" "Drivers" "All devices OK"
}

# ── 8. Network ────────────────────────────────────────────────────────────────

Write-Header "Network Connectivity"

$ping = Test-Connection -ComputerName 8.8.8.8 -Count 3 -ErrorAction SilentlyContinue
if ($ping) {
    $avgMs = [math]::Round(($ping | Measure-Object -Property ResponseTime -Average).Average, 0)
    Write-OK "Internet" "Reachable — avg $avgMs ms"
    Add-Row "Network" "ok" "Internet" "Reachable — avg $avgMs ms"
} else {
    Write-Warn "Internet" "Cannot reach 8.8.8.8 — check your network"
    Add-Row "Network" "warning" "Internet" "Cannot reach 8.8.8.8"
}

# ── Summary ───────────────────────────────────────────────────────────────────

Write-Header "Summary"

$okCount   = ($ReportRows | Where-Object Status -eq 'ok').Count
$warnCount = ($ReportRows | Where-Object Status -eq 'warning').Count
$errCount  = ($ReportRows | Where-Object Status -eq 'error').Count

Write-OK    "OK"      "$okCount item(s)"
if ($warnCount -gt 0) { Write-Warn  "Warnings" "$warnCount item(s)" }
if ($errCount  -gt 0) { Write-Err   "Errors"   "$errCount item(s)" }

Write-Host ""
Write-Host "  Tip: Run " -NoNewline -ForegroundColor Gray
Write-Host "Repair-Windows.ps1" -NoNewline -ForegroundColor Cyan
Write-Host " to fix common issues automatically." -ForegroundColor Gray
Write-Host ""

# ── HTML Report ───────────────────────────────────────────────────────────────

if ($SaveReport -or $OutputPath) {
    $defaultPath = "$env:USERPROFILE\Desktop\bsh_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
    $htmlPath    = if ($OutputPath) { $OutputPath } else { $defaultPath }

    $rowsHtml = $ReportRows | ForEach-Object {
        $color = switch ($_.Status) {
            'ok'      { '#2ecc71' }
            'warning' { '#f39c12' }
            'error'   { '#e74c3c' }
            default   { '#3498db' }
        }
        "<tr><td>$([System.Web.HttpUtility]::HtmlEncode($_.Section))</td>" +
        "<td><span style='color:$color;font-weight:bold'>$([System.Web.HttpUtility]::HtmlEncode($_.Status.ToUpper()))</span></td>" +
        "<td>$([System.Web.HttpUtility]::HtmlEncode($_.Label))</td>" +
        "<td>$([System.Web.HttpUtility]::HtmlEncode($_.Detail))</td></tr>"
    }

    $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BlueScreenHelp Diagnostic Report</title>
  <style>
    body{font-family:'Segoe UI',Arial,sans-serif;background:#1a1a2e;color:#eee;padding:20px;margin:0}
    h1{color:#00bcd4;border-bottom:2px solid #00bcd4;padding-bottom:10px}
    .meta{color:#aaa;font-size:.9em;margin-bottom:20px}
    table{width:100%;border-collapse:collapse;background:#16213e;border-radius:8px;overflow:hidden}
    th{background:#0f3460;padding:10px 14px;text-align:left;color:#00bcd4;font-size:.85em;text-transform:uppercase}
    td{padding:8px 14px;border-bottom:1px solid #0f3460;font-size:.9em}
    tr:last-child td{border-bottom:none}
    footer{margin-top:30px;font-size:.8em;color:#555;text-align:center}
  </style>
</head>
<body>
  <h1>🖥 BlueScreenHelp — Diagnostic Report</h1>
  <div class="meta">
    <strong>Generated:</strong> $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')<br>
    <strong>Host:</strong> $($cs.Name)<br>
    <strong>OS:</strong> $($os.Caption) Build $($os.BuildNumber)
  </div>
  <table>
    <thead><tr><th>Section</th><th>Status</th><th>Label</th><th>Detail</th></tr></thead>
    <tbody>$($rowsHtml -join '')</tbody>
  </table>
  <footer>Generated by BlueScreenHelp Agent &bull; github.com/Unwrenchable/BlueScreenHelp</footer>
</body>
</html>
"@

    Add-Type -AssemblyName System.Web -ErrorAction SilentlyContinue
    $html | Out-File -FilePath $htmlPath -Encoding utf8 -Force
    Write-Host "  📄 Report saved to: " -NoNewline -ForegroundColor Cyan
    Write-Host $htmlPath -ForegroundColor White
}
