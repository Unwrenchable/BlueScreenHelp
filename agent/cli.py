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
    else:
        click.echo("  Goodbye!")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    cli()


if __name__ == "__main__":
    main()
