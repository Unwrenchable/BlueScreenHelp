<#
.SYNOPSIS
    BlueScreenHelp launcher — run directly from a USB drive or cloned repo.

.DESCRIPTION
    Starts the BlueScreenHelp Agent without requiring a prior pip / install.ps1
    installation.  The script ensures Python 3.9+ is available and installs the
    single required dependency (click) into the current user's environment if it
    is missing, then launches the agent via `python -m agent`.

.PARAMETER Args
    Any arguments are forwarded verbatim to the agent CLI.  Omit to open the
    interactive menu.

.EXAMPLE
    .\run.ps1                              # interactive menu
    .\run.ps1 diagnose                     # full system diagnostic
    .\run.ps1 diagnose --checks disk,memory
    .\run.ps1 troubleshoot                 # step-by-step troubleshooter
    .\run.ps1 report --format html         # save HTML report
    .\run.ps1 info                         # quick system info
    .\run.ps1 --help                       # show all commands

.NOTES
    No installation or Administrator rights required.
    Execution policy may need to be relaxed once:
        Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#>

[CmdletBinding()]
param()

# Forward all remaining arguments to the agent
$agentArgs = $args

# Change to the directory containing this script (repo root)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

# ── Helper functions ──────────────────────────────────────────────────────────

function Write-Step([string]$msg) {
    Write-Host "  $msg" -ForegroundColor Cyan
}

function Write-Err([string]$msg) {
    Write-Host ""
    Write-Host "  [ERROR] $msg" -ForegroundColor Red
    Write-Host ""
}

# ── 1. Locate Python 3.9+ ────────────────────────────────────────────────────

$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 9)) {
                $python = $cmd
                break
            }
        }
    } catch { }
}

if (-not $python) {
    Write-Err "Python 3.9 or later is required but was not found."
    Write-Host "  Install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# ── 2. Ensure 'click' is available (only dependency) ────────────────────────

& $python -c "import click" 2>$null
if ($LASTEXITCODE -ne 0) {
    # click not found — install it for the current user
    Write-Step "Installing required dependency: click ..."
    & $python -m pip install "click>=8.0.0" --quiet --user
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Could not install 'click'. Check your internet connection or run:"
        Write-Host "  $python -m pip install click" -ForegroundColor Yellow
        exit 1
    }
}

# ── 3. Run the agent ─────────────────────────────────────────────────────────

& $python -m agent @agentArgs
exit $LASTEXITCODE
