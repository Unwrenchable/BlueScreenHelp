<#
.SYNOPSIS
    One-click installer for BlueScreenHelp Agent on Windows.

.DESCRIPTION
    This script installs the BlueScreenHelp (bsh) command-line tool on Windows.

    What it does:
      1. Checks for Python 3.9+ (installs via winget if missing)
      2. Creates a virtual environment at %LOCALAPPDATA%\BlueScreenHelp\venv
      3. Installs the bsh package from the local repo or from GitHub
      4. Adds the venv Scripts folder to the current user's PATH
      5. Verifies the installation with: bsh --version

.PARAMETER SourcePath
    Path to the local BlueScreenHelp repo (defaults to the script's parent directory).
    Set to "github" to install directly from GitHub.

.PARAMETER WithAI
    Also install the optional openai package for AI-powered diagnosis.

.EXAMPLE
    # Install from local clone:
    .\install.ps1

    # Install with AI support:
    .\install.ps1 -WithAI

    # Install from GitHub:
    .\install.ps1 -SourcePath github

.NOTES
    Run from PowerShell (no Administrator required for user-level install).
    Execution policy may need to be set: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#>

[CmdletBinding()]
param(
    [string]$SourcePath = "",
    [switch]$WithAI
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$InstallDir = "$env:LOCALAPPDATA\BlueScreenHelp"
$VenvDir    = "$InstallDir\venv"
$PipExe     = "$VenvDir\Scripts\pip.exe"
$BshExe     = "$VenvDir\Scripts\bsh.exe"

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║   BlueScreenHelp Agent — Windows Installer       ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step([string]$msg) {
    Write-Host "  ➡  $msg" -ForegroundColor Cyan
}

function Write-OK([string]$msg) {
    Write-Host "  ✅  $msg" -ForegroundColor Green
}

function Write-Warn([string]$msg) {
    Write-Host "  ⚠️   $msg" -ForegroundColor Yellow
}

Write-Banner

# ── 1. Resolve source path ────────────────────────────────────────────────────

if ($SourcePath -eq "" -or $SourcePath -eq ".") {
    $SourcePath = $PSScriptRoot
}

if ($SourcePath -ne "github") {
    if (-not (Test-Path "$SourcePath\pyproject.toml")) {
        Write-Warn "pyproject.toml not found at '$SourcePath'. Falling back to GitHub install."
        $SourcePath = "github"
    }
}

# ── 2. Check / install Python ─────────────────────────────────────────────────

Write-Step "Checking for Python 3.9+…"

$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]; $minor = [int]$Matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 9)) {
                $python = $cmd
                Write-OK "Found $ver"
                break
            }
        }
    } catch { }
}

if (-not $python) {
    Write-Warn "Python 3.9+ not found. Attempting install via winget…"
    try {
        winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
        $python = "python"
        Write-OK "Python installed. You may need to restart your terminal."
    } catch {
        Write-Host "  ❌  Could not install Python automatically." -ForegroundColor Red
        Write-Host "  Please install Python 3.9+ from https://python.org/downloads" -ForegroundColor Yellow
        exit 1
    }
}

# ── 3. Create virtual environment ─────────────────────────────────────────────

Write-Step "Creating virtual environment at $VenvDir…"
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

if (Test-Path $VenvDir) {
    Write-Warn "Existing venv found — recreating."
    Remove-Item $VenvDir -Recurse -Force
}

& $python -m venv $VenvDir
Write-OK "Virtual environment created."

# ── 4. Upgrade pip ────────────────────────────────────────────────────────────

Write-Step "Upgrading pip…"
& $PipExe install --upgrade pip --quiet
Write-OK "pip upgraded."

# ── 5. Install bsh ────────────────────────────────────────────────────────────

if ($SourcePath -eq "github") {
    Write-Step "Installing BlueScreenHelp from GitHub…"
    $extras = if ($WithAI) { "[ai]" } else { "" }
    & $PipExe install "bluescreenhelp$extras @ git+https://github.com/Unwrenchable/BlueScreenHelp.git" --quiet
} else {
    Write-Step "Installing BlueScreenHelp from local source ($SourcePath)…"
    $extras = if ($WithAI) { ".[ai]" } else { "." }
    & $PipExe install $extras --quiet --find-links $SourcePath
}

Write-OK "BlueScreenHelp installed."

# ── 6. Add to PATH ────────────────────────────────────────────────────────────

$scriptsDir = "$VenvDir\Scripts"
$userPath   = [Environment]::GetEnvironmentVariable("PATH", "User")

if ($userPath -notlike "*$scriptsDir*") {
    Write-Step "Adding $scriptsDir to user PATH…"
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$scriptsDir", "User")
    $env:PATH = "$env:PATH;$scriptsDir"
    Write-OK "PATH updated."
} else {
    Write-OK "PATH already contains $scriptsDir"
}

# ── 7. Verify ─────────────────────────────────────────────────────────────────

Write-Step "Verifying installation…"
try {
    $bshVer = & $BshExe --version 2>&1
    Write-OK "Installed: $bshVer"
} catch {
    Write-Warn "Could not verify. Try opening a new terminal and running: bsh --version"
}

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║   Installation complete!                             ║" -ForegroundColor Green
Write-Host "  ╠══════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "  ║   Open a NEW terminal and run:                       ║" -ForegroundColor White
Write-Host "  ║                                                      ║" -ForegroundColor White
Write-Host "  ║     bsh                  # interactive menu          ║" -ForegroundColor White
Write-Host "  ║     bsh diagnose         # full system diagnostic    ║" -ForegroundColor White
Write-Host "  ║     bsh troubleshoot     # step-by-step guide        ║" -ForegroundColor White
Write-Host "  ║     bsh report --save    # save HTML report          ║" -ForegroundColor White
if ($WithAI) {
Write-Host "  ║     bsh diagnose --ai    # AI-powered analysis       ║" -ForegroundColor White
}
Write-Host "  ╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
