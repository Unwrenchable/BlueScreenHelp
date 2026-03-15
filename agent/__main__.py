"""
Allow the agent package to be executed as a module.

This enables running the tool directly from the repository root
without installing it first — useful when running from a USB drive:

    python -m agent               # interactive menu
    python -m agent diagnose      # full diagnostic
    python -m agent troubleshoot  # step-by-step troubleshooter
    python -m agent report        # save diagnostic report
    python -m agent info          # quick system info
"""

from agent.cli import main

if __name__ == "__main__":
    main()
