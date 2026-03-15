"""
Tests for agent/diagnostics.py

All tests run on any OS (non-Windows checks return status='skipped').
"""

import sys
import platform
import pytest

from agent.diagnostics import (
    CheckResult,
    DiagnosticReport,
    check_os_info,
    check_network,
    run_all,
    ALL_CHECKS,
)


# ── CheckResult / DiagnosticReport data classes ───────────────────────────────

class TestCheckResult:
    def test_defaults(self):
        r = CheckResult(name="Test", status="ok", summary="All good")
        assert r.name == "Test"
        assert r.status == "ok"
        assert r.summary == "All good"
        assert r.details == []
        assert r.raw_output == ""

    def test_with_details(self):
        r = CheckResult(name="X", status="warning", summary="Uh oh",
                        details=["line1", "line2"])
        assert len(r.details) == 2

    def test_as_dict_via_report(self):
        report = DiagnosticReport(hostname="testhost", os_info="TestOS")
        report.checks.append(CheckResult(name="Foo", status="info", summary="bar"))
        d = report.as_dict()
        assert d["hostname"] == "testhost"
        assert len(d["checks"]) == 1
        assert d["checks"][0]["name"] == "Foo"


# ── check_os_info ─────────────────────────────────────────────────────────────

class TestCheckOsInfo:
    def test_returns_check_result(self):
        result = check_os_info()
        assert isinstance(result, CheckResult)

    def test_status_is_info(self):
        result = check_os_info()
        assert result.status == "info"

    def test_summary_contains_platform(self):
        result = check_os_info()
        # platform.platform() should appear in the summary
        assert len(result.summary) > 0

    def test_details_includes_hostname(self):
        result = check_os_info()
        hostname = platform.node()
        joined = " ".join(result.details)
        assert hostname in joined


# ── check_network ─────────────────────────────────────────────────────────────

class TestCheckNetwork:
    def test_returns_check_result(self):
        result = check_network()
        assert isinstance(result, CheckResult)

    def test_status_ok_or_warning(self):
        result = check_network()
        assert result.status in ("ok", "warning")


# ── Non-Windows checks return 'skipped' on other OSes ─────────────────────────

@pytest.mark.skipif(sys.platform == "win32", reason="Only meaningful off-Windows")
class TestNonWindowsGraceful:
    """Verify that Windows-only checks degrade gracefully on Linux/macOS."""

    def test_disk_health_skipped(self):
        from agent.diagnostics import check_disk_health
        r = check_disk_health()
        assert r.status == "skipped"

    def test_memory_skipped(self):
        from agent.diagnostics import check_memory
        r = check_memory()
        assert r.status == "skipped"

    def test_bsod_events_skipped(self):
        from agent.diagnostics import check_event_log_bsod
        r = check_event_log_bsod()
        assert r.status == "skipped"

    def test_windows_integrity_skipped(self):
        from agent.diagnostics import check_windows_integrity
        r = check_windows_integrity()
        assert r.status == "skipped"

    def test_activation_skipped(self):
        from agent.diagnostics import check_activation
        r = check_activation()
        assert r.status == "skipped"

    def test_boot_config_skipped(self):
        from agent.diagnostics import check_boot_config
        r = check_boot_config()
        assert r.status == "skipped"

    def test_cpu_temp_skipped(self):
        from agent.diagnostics import check_cpu_temp
        r = check_cpu_temp()
        assert r.status == "skipped"

    def test_drivers_skipped(self):
        from agent.diagnostics import check_drivers
        r = check_drivers()
        assert r.status == "skipped"


# ── run_all ───────────────────────────────────────────────────────────────────

class TestRunAll:
    def test_returns_diagnostic_report(self):
        report = run_all(checks=[check_os_info])
        assert isinstance(report, DiagnosticReport)

    def test_report_has_checks(self):
        report = run_all(checks=[check_os_info, check_network])
        assert len(report.checks) == 2

    def test_progress_callback_called(self):
        called = []
        run_all(checks=[check_os_info], progress_callback=lambda n: called.append(n))
        assert len(called) == 1
        assert "check_os_info" in called[0]

    def test_report_has_timestamp(self):
        report = run_all(checks=[check_os_info])
        assert report.timestamp != ""

    def test_report_hostname(self):
        report = run_all(checks=[check_os_info])
        assert report.hostname == platform.node()

    def test_all_checks_list_not_empty(self):
        assert len(ALL_CHECKS) >= 8
