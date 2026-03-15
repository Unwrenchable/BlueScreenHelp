@echo off
setlocal EnableDelayedExpansion

REM ─────────────────────────────────────────────────────────────────────────────
REM  run.bat — BlueScreenHelp launcher (no installation required)
REM
REM  Run from a USB drive or cloned repo without pip install:
REM
REM    run.bat                   <- interactive menu
REM    run.bat diagnose          <- full system diagnostic
REM    run.bat diagnose --checks disk,memory
REM    run.bat troubleshoot      <- step-by-step troubleshooter
REM    run.bat report            <- save diagnostic report
REM    run.bat info              <- quick system info
REM    run.bat --help            <- show all commands
REM ─────────────────────────────────────────────────────────────────────────────

REM Change to the directory containing this script (repo root)
cd /d "%~dp0"

REM ── 1. Locate Python ─────────────────────────────────────────────────────────
set PYTHON=
for %%C in (python python3 py) do (
    if not defined PYTHON (
        %%C --version >nul 2>nul
        if not errorlevel 1 (
            set PYTHON=%%C
        )
    )
)

if not defined PYTHON (
    echo.
    echo   [ERROR] Python 3.9 or later is required but was not found.
    echo   Please install Python from https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM ── 2. Ensure 'click' is available (only dependency) ─────────────────────────
%PYTHON% -c "import click" >nul 2>nul
if errorlevel 1 (
    echo   Installing required dependency: click ...
    %PYTHON% -m pip install "click>=8.0.0" --quiet --user
    if errorlevel 1 (
        echo.
        echo   [ERROR] Could not install 'click'. Check your internet connection or
        echo   run:  %PYTHON% -m pip install click
        echo.
        pause
        exit /b 1
    )
)

REM ── 3. Run the agent ──────────────────────────────────────────────────────────
%PYTHON% -m agent %*
