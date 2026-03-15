"""
Tests for agent/reporter.py
"""

import json
from pathlib import Path

import pytest

from agent.diagnostics import CheckResult, DiagnosticReport
from agent.reporter import to_text, to_html, to_json, save_report


def _make_report() -> DiagnosticReport:
    report = DiagnosticReport(hostname="testhost", os_info="TestOS 1.0")
    report.checks = [
        CheckResult(name="OS Info",    status="info",    summary="TestOS", details=["Hostname: testhost"]),
        CheckResult(name="Disk",       status="ok",      summary="Healthy"),
        CheckResult(name="BSOD",       status="warning", summary="2 events", details=["event1", "event2"]),
        CheckResult(name="Integrity",  status="skipped", summary="Not Windows"),
    ]
    return report


class TestToText:
    def test_contains_header(self):
        text = to_text(_make_report())
        assert "BlueScreenHelp" in text

    def test_contains_hostname(self):
        text = to_text(_make_report())
        assert "testhost" in text

    def test_contains_all_check_names(self):
        text = to_text(_make_report())
        for check_name in ("OS Info", "Disk", "BSOD", "Integrity"):
            assert check_name in text

    def test_contains_status_counts(self):
        text = to_text(_make_report())
        assert "Summary" in text

    def test_details_listed(self):
        text = to_text(_make_report())
        assert "event1" in text


class TestToHtml:
    def test_is_valid_html(self):
        html = to_html(_make_report())
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_hostname(self):
        html = to_html(_make_report())
        assert "testhost" in html

    def test_contains_check_names(self):
        html = to_html(_make_report())
        for name in ("OS Info", "Disk", "BSOD", "Integrity"):
            assert name in html

    def test_status_colors_present(self):
        html = to_html(_make_report())
        assert "#2ecc71" in html   # ok color
        assert "#f39c12" in html   # warning color

    def test_xss_escaping(self):
        report = DiagnosticReport(hostname="<script>alert(1)</script>", os_info="OS")
        html = to_html(report)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestToJson:
    def test_valid_json(self):
        j = to_json(_make_report())
        data = json.loads(j)
        assert "hostname" in data
        assert "checks" in data

    def test_check_count(self):
        j = to_json(_make_report())
        data = json.loads(j)
        assert len(data["checks"]) == 4


class TestSaveReport:
    def test_saves_txt(self, tmp_path: Path):
        paths = save_report(_make_report(), output_dir=tmp_path, formats=["txt"])
        assert "txt" in paths
        assert paths["txt"].exists()
        content = paths["txt"].read_text(encoding="utf-8")
        assert "BlueScreenHelp" in content

    def test_saves_html(self, tmp_path: Path):
        paths = save_report(_make_report(), output_dir=tmp_path, formats=["html"])
        assert "html" in paths
        assert paths["html"].exists()

    def test_saves_json(self, tmp_path: Path):
        paths = save_report(_make_report(), output_dir=tmp_path, formats=["json"])
        assert "json" in paths
        data = json.loads(paths["json"].read_text(encoding="utf-8"))
        assert "checks" in data

    def test_saves_multiple_formats(self, tmp_path: Path):
        paths = save_report(_make_report(), output_dir=tmp_path, formats=["txt", "html", "json"])
        assert len(paths) == 3

    def test_creates_output_dir(self, tmp_path: Path):
        out = tmp_path / "nested" / "reports"
        save_report(_make_report(), output_dir=out, formats=["txt"])
        assert out.exists()
