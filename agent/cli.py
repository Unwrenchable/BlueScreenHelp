"""
cli.py – Command-line interface for BlueScreenHelp Agent.

Usage examples
--------------
    bsh                          # interactive menu
    bsh diagnose                 # full system diagnostic
    bsh diagnose --checks disk   # targeted check
    bsh troubleshoot             # step-by-step troubleshooter
    bsh report                   # save last/current report
    bsh info                     # show system info only
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .diagnostics import (
    run_all,
    check_disk_health,
    check_memory,
    check_event_log_bsod,
    check_windows_integrity,
    check_activation,
    check_boot_config,
    check_cpu_temp,
    check_network,
    check_drivers,
    check_os_info,
)
from .reporter import to_text, save_report
from .troubleshooter import run_tree, NODES, START_MENU

# ── Check registry ────────────────────────────────────────────────────────────

NAMED_CHECKS = {
    "disk":       [check_disk_health],
    "memory":     [check_memory],
    "bsod":       [check_event_log_bsod],
    "integrity":  [check_windows_integrity],
    "activation": [check_activation],
    "boot":       [check_boot_config],
    "temp":       [check_cpu_temp],
    "network":    [check_network],
    "drivers":    [check_drivers],
    "info":       [check_os_info],
}

STATUS_STYLE = {
    "ok":      ("green", "✅"),
    "warning": ("yellow", "⚠️ "),
    "error":   ("red", "❌"),
    "info":    ("cyan", "ℹ️ "),
    "skipped": ("bright_black", "⏭️ "),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _echo_check(result) -> None:
    color, emoji = STATUS_STYLE.get(result.status, ("white", "?"))
    click.echo(f"  {emoji}  ", nl=False)
    click.secho(f"{result.name}", fg=color, bold=True, nl=False)
    click.echo(f"  –  {result.summary}")
    for d in result.details:
        click.echo(f"       • {d}")


def _banner() -> None:
    click.secho(
        r"""
  ____  _            ____                           _   _      _
 |  _ \| |          / ___|  ___ _ __ ___  ___ _ __ | | | | ___| |_ __
 | |_) | |   _____ \___ \ / __| '__/ _ \/ _ \ '_ \| |_| |/ _ \ | '_ \
 |  _ <| |__|_____|  ___) | (__| | |  __/  __/ | | |  _  |  __/ | |_) |
 |_| \_\_____|    |____/ \___|_|  \___|\___|_| |_|_| |_|\___|_| .__/
                                                               |_|
""",
        fg="cyan",
    )
    click.secho(f"  BlueScreenHelp Agent  v{__version__}", fg="bright_white", bold=True)
    click.secho("  Windows Diagnostic & Recovery Tool\n", fg="bright_black")


# ── Root group ────────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-v", "--version")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """BlueScreenHelp Agent – Windows diagnostic & recovery tool.\n
    Run without a sub-command to launch the interactive menu."""
    if ctx.invoked_subcommand is None:
        _banner()
        _interactive_menu()


# ── diagnose ──────────────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--checks", "-c",
    default="all",
    show_default=True,
    help=(
        "Comma-separated list of checks to run.  "
        "Available: " + ", ".join(NAMED_CHECKS) + ", all"
    ),
)
@click.option(
    "--save", "-s",
    is_flag=True,
    default=False,
    help="Save the report to disk (txt + html).",
)
@click.option(
    "--format", "-f",
    "fmt",
    default="txt,html",
    show_default=True,
    help="Comma-separated output formats when --save is used (txt, html, json).",
)
@click.option(
    "--ai", "-a",
    is_flag=True,
    default=False,
    help="Request AI-powered analysis after running checks (requires OPENAI_API_KEY).",
)
@click.option(
    "--output-dir", "-o",
    default=None,
    type=click.Path(),
    help="Directory to save the report (defaults to current directory).",
)
def diagnose(checks: str, save: bool, fmt: str, ai: bool, output_dir: str | None) -> None:
    """Run system diagnostics and display a health report."""
    _banner()

    # Resolve checks
    if checks.strip().lower() == "all":
        fns = None  # run_all defaults to all
    else:
        fns = []
        for name in checks.split(","):
            name = name.strip().lower()
            if name not in NAMED_CHECKS:
                click.secho(f"Unknown check '{name}'. Available: {', '.join(NAMED_CHECKS)}", fg="red")
                sys.exit(1)
            fns.extend(NAMED_CHECKS[name])

    click.secho("Running diagnostics…\n", fg="bright_black")

    def _progress(fn_name: str) -> None:
        label = fn_name.replace("check_", "").replace("_", " ").title()
        click.secho(f"  ⏳ {label}…", fg="bright_black")

    report = run_all(checks=fns, progress_callback=_progress)

    click.echo("")
    click.secho("─" * 60, fg="bright_black")
    click.secho("  Diagnostic Results", bold=True)
    click.secho("─" * 60, fg="bright_black")

    for result in report.checks:
        _echo_check(result)

    # Summary
    counts: dict[str, int] = {}
    for c in report.checks:
        counts[c.status] = counts.get(c.status, 0) + 1
    click.echo("")
    click.secho("─" * 60, fg="bright_black")
    click.secho("  Summary", bold=True)
    for status, count in sorted(counts.items()):
        color, emoji = STATUS_STYLE.get(status, ("white", "?"))
        click.secho(f"  {emoji}  {status.upper()}: {count}", fg=color)

    # AI analysis
    if ai:
        _run_ai_analysis(report)

    # Save
    if save:
        formats = [f.strip() for f in fmt.split(",")]
        out_dir = Path(output_dir) if output_dir else None
        paths = save_report(report, output_dir=out_dir, formats=formats)
        click.echo("")
        click.secho("  Report saved:", bold=True)
        for fmt_key, path in paths.items():
            click.secho(f"    {fmt_key.upper()}: {path}", fg="cyan")


# ── troubleshoot ──────────────────────────────────────────────────────────────

@cli.command()
def troubleshoot() -> None:
    """Interactive step-by-step troubleshooter."""
    _banner()
    click.secho("  Interactive Troubleshooter", bold=True)
    click.secho("  Type the number of your choice and press Enter. 'q' to quit.\n",
                fg="bright_black")

    def _ask(prompt: str, choices: dict[str, str]) -> str:
        click.secho(f"\n  {prompt}", bold=True)
        # Build display labels
        for key, value in choices.items():
            if key == "q":
                label = value
            else:
                node = NODES.get(value, None)
                label = node.prompt if node else value
                # Use START_MENU labels for the start choices
                if value in {v for _, v in START_MENU.values()}:
                    for k2, (lbl, nid) in START_MENU.items():
                        if nid == value:
                            label = lbl
                            break
            click.echo(f"    [{key}] {label}")
        while True:
            answer = click.prompt("  Your choice", default="q").strip().lower()
            if answer in choices or answer == "q":
                return answer
            click.secho("  Invalid choice – please try again.", fg="yellow")

    def _print(lines: list[str]) -> None:
        for line in lines:
            click.echo(line)

    # Patch the start node choices to use our pretty labels
    from .troubleshooter import NODES as _NODES
    _NODES["start"].choices = {k: v for k, (_, v) in START_MENU.items()}

    run_tree(ask_fn=_ask, print_fn=_print)
    click.echo("\n  Goodbye! Visit https://github.com/Unwrenchable/BlueScreenHelp for more help.")


# ── info ──────────────────────────────────────────────────────────────────────

@cli.command()
def info() -> None:
    """Display basic system information."""
    _banner()
    from .diagnostics import check_os_info, check_memory, check_disk_health, check_network
    click.secho("  System Information\n", bold=True)
    for fn in [check_os_info, check_memory, check_disk_health, check_network]:
        _echo_check(fn())


# ── report ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--format", "-f", "fmt", default="txt,html", show_default=True,
              help="Comma-separated formats: txt, html, json.")
@click.option("--output-dir", "-o", default=None, type=click.Path(),
              help="Directory to save the report.")
@click.option("--ai", "-a", is_flag=True, default=False,
              help="Include AI analysis (requires OPENAI_API_KEY).")
def report(fmt: str, output_dir: str | None, ai: bool) -> None:
    """Run a full diagnostic and save the report to disk."""
    _banner()
    click.secho("  Running full diagnostic to generate report…\n", fg="bright_black")

    def _progress(fn_name: str) -> None:
        label = fn_name.replace("check_", "").replace("_", " ").title()
        click.secho(f"  ⏳ {label}…", fg="bright_black")

    diagnostic_report = run_all(progress_callback=_progress)

    if ai:
        _run_ai_analysis(diagnostic_report)

    formats = [f.strip() for f in fmt.split(",")]
    out_dir = Path(output_dir) if output_dir else None
    paths = save_report(diagnostic_report, output_dir=out_dir, formats=formats)
    click.echo("")
    click.secho("  Report saved:", bold=True)
    for fmt_key, path in paths.items():
        click.secho(f"    {fmt_key.upper()}: {path}", fg="cyan")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_ai_analysis(diagnostic_report) -> None:
    from .ai_helper import is_available, analyse
    click.echo("")
    click.secho("─" * 60, fg="bright_black")
    click.secho("  AI Analysis", bold=True)
    click.secho("─" * 60, fg="bright_black")
    if not is_available():
        click.secho(
            "  AI not available. Set OPENAI_API_KEY and install 'openai' package.",
            fg="yellow",
        )
    else:
        click.secho("  Querying AI model…", fg="bright_black")
        analysis = analyse(diagnostic_report)
        click.echo("")
        for line in analysis.splitlines():
            click.echo(f"  {line}")


def _interactive_menu() -> None:
    """Top-level interactive menu when no sub-command is given."""
    click.secho("  What would you like to do?\n", bold=True)
    click.echo("    [1] Run diagnostics")
    click.echo("    [2] Interactive troubleshooter")
    click.echo("    [3] Show system info")
    click.echo("    [4] Save diagnostic report")
    click.echo("    [5] 💾 Data recovery (scan drives)")
    click.echo("    [6] 💾 Data recovery (recover files)")
    click.echo("    [q] Quit\n")

    choice = click.prompt("  Choose", default="q").strip().lower()
    ctx = click.get_current_context()

    if choice == "1":
        ctx.invoke(diagnose, checks="all", save=False, fmt="txt,html", ai=False, output_dir=None)
    elif choice == "2":
        ctx.invoke(troubleshoot)
    elif choice == "3":
        ctx.invoke(info)
    elif choice == "4":
        ctx.invoke(report, fmt="txt,html", output_dir=None, ai=False)
    elif choice == "5":
        drive = click.prompt("  Enter drive path (or 'list' to see all drives)")
        ctx.invoke(scan_drive, drive=drive)
    elif choice == "6":
        drive = click.prompt("  Enter drive path to recover from")
        output = click.prompt("  Enter output directory for recovered files")
        types = click.prompt("  Enter file types to recover (comma-separated, or leave blank for all)", default="")
        ctx.invoke(recover, drive=drive, output=output, types=types if types else None, method="carving", scan_only=False)
    else:
        click.echo("  Goodbye!")


# ── recover (data recovery) ──────────────────────────────────────────────────

@cli.command()
@click.option("--drive", "-d", required=True, help="Drive path (e.g., '\\\\.\\PhysicalDrive0' or '\\\\.\\C:')")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output directory for recovered files")
@click.option("--types", "-t", default=None, help="Comma-separated file types to recover (e.g., 'jpg,pdf,docx')")
@click.option("--method", "-m", default="carving", type=click.Choice(["carving", "filesystem", "both"]),
              help="Recovery method: carving (signature-based), filesystem (MFT scan), or both")
@click.option("--scan-only", is_flag=True, default=False, help="Only scan and report, don't recover files")
def recover(drive: str, output: str, types: str | None, method: str, scan_only: bool) -> None:
    """Recover files from a failing or corrupted drive.

    This command can recover personal data from drives that won't boot or have
    corrupted file systems. It uses file signature detection (carving) to find
    files even when the file system is damaged.

    Examples:
        bsh recover --drive "\\\\.\\PhysicalDrive0" --output D:\\Recovery
        bsh recover -d "\\\\.\\C:" -o D:\\Recovery --types jpg,pdf,docx
        bsh recover -d "\\\\.\\PhysicalDrive1" -o D:\\Recovery --scan-only
    """
    _banner()
    click.secho("  💾 Data Recovery Tool", bold=True, fg="cyan")
    click.echo("")

    output_path = Path(output)

    # Parse file types
    file_types = None
    if types:
        file_types = [t.strip().lower() for t in types.split(',')]
        click.echo(f"  Target file types: {', '.join(file_types)}")
    else:
        click.echo("  Target file types: All supported types")

    click.echo(f"  Drive: {drive}")
    click.echo(f"  Output directory: {output_path}")
    click.echo(f"  Recovery method: {method}")
    click.echo("")

    # Import recovery modules
    from .data_recovery import (
        WindowsDriveAccess, scan_drive_for_recovery,
        quick_file_recovery, list_drives
    )
    from .file_carving import carve_files_from_drive

    # First, assess the drive
    click.secho("  Step 1: Assessing drive condition...", fg="bright_black")
    assessment = scan_drive_for_recovery(drive)

    if not assessment['accessible']:
        click.secho("  ❌ Cannot access drive", fg="red")
        for rec in assessment['recommendations']:
            click.echo(f"     • {rec}")
        return

    click.secho(f"  ✅ Drive is accessible", fg="green")
    click.echo(f"     File system: {assessment['file_system']}")

    for rec in assessment['recommendations']:
        click.echo(f"     • {rec}")

    click.echo("")

    if scan_only:
        click.secho("  Scan-only mode: Not recovering files", fg="yellow")
        return

    # Perform recovery
    click.secho("  Step 2: Starting recovery process...", fg="bright_black")
    click.echo("")

    stats = {'files_found': 0, 'bytes_recovered': 0, 'errors': []}

    # Method 1: File system based recovery
    if method in ['filesystem', 'both'] and assessment['file_system'] in ['NTFS', 'FAT32', 'FAT16']:
        click.secho("  🔍 Scanning file system...", fg="cyan")
        try:
            result = quick_file_recovery(drive, output_path, file_types)
            stats['files_found'] += result.files_found
            stats['bytes_recovered'] += result.bytes_recovered
            stats['errors'].extend(result.errors)

            click.echo(f"     Found {result.files_found} files")
            click.echo(f"     Recovered {result.files_recovered} files")
        except Exception as e:
            click.secho(f"     ⚠️  File system scan failed: {e}", fg="yellow")

    # Method 2: Signature-based recovery (file carving)
    if method in ['carving', 'both']:
        click.secho("  🔍 Scanning for file signatures (carving)...", fg="cyan")
        click.secho("     This may take a while depending on drive size...", fg="bright_black")

        try:
            drive_access = WindowsDriveAccess()
            if drive_access.open_drive(drive, readonly=True):

                def progress(bytes_scanned, total_bytes):
                    if bytes_scanned % (100 * 1024 * 1024) == 0:  # Every 100MB
                        mb_scanned = bytes_scanned / (1024 * 1024)
                        click.secho(f"     Scanned {mb_scanned:.0f} MB...", fg="bright_black")

                carve_stats = carve_files_from_drive(drive_access, output_path, file_types, progress)
                stats['files_found'] += carve_stats['files_found']
                stats['bytes_recovered'] += carve_stats['bytes_recovered']

                drive_access.close()

                click.echo(f"     Found {carve_stats['files_found']} files via carving")
            else:
                click.secho("     ⚠️  Could not open drive for carving", fg="yellow")
        except Exception as e:
            click.secho(f"     ⚠️  Carving failed: {e}", fg="yellow")

    # Summary
    click.echo("")
    click.secho("─" * 60, fg="bright_black")
    click.secho("  Recovery Complete", bold=True, fg="green")
    click.secho("─" * 60, fg="bright_black")
    click.echo(f"  Files found: {stats['files_found']}")
    click.echo(f"  Data recovered: {stats['bytes_recovered'] / (1024*1024):.2f} MB")
    click.echo(f"  Output location: {output_path}")

    if stats['errors']:
        click.echo("")
        click.secho("  Errors encountered:", fg="yellow")
        for err in stats['errors'][:10]:  # Show first 10 errors
            click.echo(f"     • {err}")


@cli.command()
@click.option("--drive", "-d", required=True, help="Drive path to scan")
def scan_drive(drive: str) -> None:
    """Scan a drive and assess recovery options.

    Analyzes a drive's condition and provides recommendations for recovery.

    Example:
        bsh scan-drive --drive "\\\\.\\PhysicalDrive0"
    """
    _banner()
    click.secho("  🔍 Drive Scanner", bold=True, fg="cyan")
    click.echo("")

    from .data_recovery import scan_drive_for_recovery, list_drives

    # Check if user wants to see all drives
    if drive == "list":
        click.secho("  Available drives:", bold=True)
        drives = list_drives()

        if not drives:
            click.echo("     No drives detected")
        else:
            for d in drives:
                size_gb = d.size_bytes / (1024**3)
                click.echo(f"     {d.device_path}")
                click.echo(f"        Model: {d.model}")
                click.echo(f"        Size: {size_gb:.2f} GB")
                if d.serial:
                    click.echo(f"        Serial: {d.serial}")
                click.echo("")
        return

    # Scan specific drive
    click.echo(f"  Scanning: {drive}")
    click.echo("")

    assessment = scan_drive_for_recovery(drive)

    if assessment['accessible']:
        click.secho("  ✅ Drive Status: Accessible", fg="green")
    else:
        click.secho("  ❌ Drive Status: Not Accessible", fg="red")

    click.echo(f"  File System: {assessment['file_system']}")

    if assessment['total_size'] > 0:
        size_gb = assessment['total_size'] / (1024**3)
        click.echo(f"  Total Size: {size_gb:.2f} GB")

    if assessment['estimated_files'] > 0:
        click.echo(f"  Estimated Files: {assessment['estimated_files']}")

    click.echo("")
    click.secho("  Recommendations:", bold=True)

    for rec in assessment['recommendations']:
        click.echo(f"     • {rec}")

    click.echo("")
    click.secho("  Next Steps:", bold=True)
    click.echo("     1. Use 'bsh recover' to start file recovery")
    click.echo("     2. For severely damaged drives, consider 'bsh image-drive' first")
    click.echo("     3. For critical data, consult professional data recovery services")


@cli.command()
@click.option("--drive", "-d", required=True, help="Source drive path")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output image file path")
@click.option("--skip-bad-sectors", is_flag=True, default=True, help="Skip unreadable sectors (recommended)")
def image_drive(drive: str, output: str, skip_bad_sectors: bool) -> None:
    """Create a sector-by-sector image of a failing drive.

    Creates a complete disk image that can be used for recovery later,
    preserving as much data as possible from a failing drive. This is
    recommended before attempting repairs on a physically damaged drive.

    Example:
        bsh image-drive -d "\\\\.\\PhysicalDrive0" -o D:\\backup.img
    """
    _banner()
    click.secho("  💿 Disk Imaging Tool", bold=True, fg="cyan")
    click.echo("")

    from .data_recovery import create_drive_image

    output_path = Path(output)

    click.echo(f"  Source drive: {drive}")
    click.echo(f"  Output image: {output_path}")
    click.echo(f"  Skip bad sectors: {'Yes' if skip_bad_sectors else 'No'}")
    click.echo("")

    if output_path.exists():
        if not click.confirm("  Output file exists. Overwrite?"):
            click.echo("  Cancelled.")
            return

    click.secho("  ⚠️  WARNING:", fg="yellow", bold=True)
    click.echo("     Disk imaging can take several hours for large drives.")
    click.echo("     Ensure you have enough free space for the image.")
    click.echo("")

    if not click.confirm("  Start disk imaging?"):
        click.echo("  Cancelled.")
        return

    click.secho("  Creating disk image...", fg="cyan")

    def progress(bytes_read, total_bytes):
        if bytes_read % (100 * 1024 * 1024) == 0:  # Every 100MB
            mb = bytes_read / (1024 * 1024)
            if total_bytes > 0:
                percent = (bytes_read / total_bytes) * 100
                click.secho(f"     Progress: {mb:.0f} MB ({percent:.1f}%)", fg="bright_black")
            else:
                click.secho(f"     Progress: {mb:.0f} MB", fg="bright_black")

    success = create_drive_image(drive, output_path, skip_bad_sectors, progress)

    click.echo("")

    if success:
        click.secho("  ✅ Disk image created successfully", fg="green")
        click.echo(f"     Image saved to: {output_path}")
        click.echo("")
        click.echo("  Next steps:")
        click.echo("     1. You can now run recovery on this image file")
        click.echo("     2. Use 'bsh recover --drive <image_file>' to extract files")
    else:
        click.secho("  ❌ Disk imaging failed", fg="red")
        click.echo("     Check that you have:")
        click.echo("     • Administrator/root privileges")
        click.echo("     • Sufficient free disk space")
        click.echo("     • Correct drive path")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    cli()


if __name__ == "__main__":
    main()
