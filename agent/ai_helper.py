"""
ai_helper.py – Optional AI-powered diagnosis using any OpenAI-compatible endpoint.

The module degrades gracefully when the `openai` package or an API key is absent.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .diagnostics import DiagnosticReport

_OPENAI_AVAILABLE = False
try:
    import openai  # type: ignore
    _OPENAI_AVAILABLE = True
except ImportError:
    pass

SYSTEM_PROMPT = """\
You are a Windows PC diagnostic expert assistant called BlueScreenHelp.
You will be given a JSON diagnostic report collected from a user's Windows machine.
Analyse the results and provide:
1. A concise summary of any issues found (2-3 sentences).
2. A numbered list of recommended actions, most important first.
3. Any additional warnings or observations.
Keep your response concise and beginner-friendly. Use plain text (no markdown headers)."""


def is_available() -> bool:
    """Return True if AI assistance is available (package + API key present)."""
    if not _OPENAI_AVAILABLE:
        return False
    return bool(
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("BSH_AI_KEY")
    )


def analyse(report: "DiagnosticReport", model: str = "gpt-4o-mini") -> str:
    """
    Send the diagnostic report to an AI model and return its analysis.

    Returns a string with the AI's response, or an informational message
    if AI is not available.
    """
    if not _OPENAI_AVAILABLE:
        return (
            "AI analysis is not available.\n"
            "Install the openai package:  pip install openai\n"
            "Then set the OPENAI_API_KEY environment variable."
        )

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("BSH_AI_KEY")
    if not api_key:
        return (
            "AI analysis is not available: no API key found.\n"
            "Set OPENAI_API_KEY (or BSH_AI_KEY) to enable AI-powered diagnosis."
        )

    import json as _json
    report_json = _json.dumps(report.as_dict(), indent=2)

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Diagnostic report:\n{report_json}"},
        ],
        max_tokens=800,
        temperature=0.3,
    )
    return response.choices[0].message.content or "(No response from AI)"
