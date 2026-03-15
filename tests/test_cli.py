"""
Tests for agent/cli.py (Click commands)
"""

import pytest
from click.testing import CliRunner

from agent.cli import cli


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_version(self):
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help(self):
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "diagnose" in result.output
        assert "troubleshoot" in result.output

    def test_diagnose_info_only(self):
        result = self.runner.invoke(cli, ["diagnose", "--checks", "info"])
        assert result.exit_code == 0
        assert "OS Info" in result.output

    def test_diagnose_network(self):
        result = self.runner.invoke(cli, ["diagnose", "--checks", "network"])
        assert result.exit_code == 0
        # Should have OK or Warning for network
        assert any(word in result.output for word in ("Network", "Internet", "reachable", "Cannot"))

    def test_diagnose_invalid_check(self):
        result = self.runner.invoke(cli, ["diagnose", "--checks", "nonexistent"])
        assert result.exit_code != 0
        assert "Unknown check" in result.output

    def test_diagnose_save_txt(self, tmp_path):
        result = self.runner.invoke(
            cli,
            ["diagnose", "--checks", "info", "--save", "--format", "txt",
             "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        txt_files = list(tmp_path.glob("*.txt"))
        assert len(txt_files) == 1

    def test_diagnose_save_html(self, tmp_path):
        result = self.runner.invoke(
            cli,
            ["diagnose", "--checks", "info", "--save", "--format", "html",
             "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        html_files = list(tmp_path.glob("*.html"))
        assert len(html_files) == 1

    def test_info_command(self):
        result = self.runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "OS Info" in result.output

    def test_report_command(self, tmp_path):
        result = self.runner.invoke(
            cli,
            ["report", "--format", "txt", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "Report saved" in result.output

    def test_troubleshoot_quits(self):
        # Provide 'q' immediately to quit
        result = self.runner.invoke(cli, ["troubleshoot"], input="q\n")
        assert result.exit_code == 0

    def test_troubleshoot_full_navigation(self):
        # Navigate: choose option 1 (BSOD) → option 1 (known code) → option 1 (memory) → q
        result = self.runner.invoke(cli, ["troubleshoot"], input="1\n1\n1\nq\n")
        assert result.exit_code == 0
        assert "RAM" in result.output or "MemTest" in result.output
