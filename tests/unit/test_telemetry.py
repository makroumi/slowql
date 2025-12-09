import os
from unittest.mock import patch

import pytest

from slowql.telemetry import Telemetry


class TestTelemetry:
    def test_telemetry_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("SLOWQL_TELEMETRY", raising=False)
        telemetry = Telemetry()
        assert not telemetry.enabled

    def test_telemetry_enabled_by_env_var(self, monkeypatch):
        monkeypatch.setenv("SLOWQL_TELEMETRY", "true")
        telemetry = Telemetry()
        assert telemetry.enabled

    def test_telemetry_disabled_by_env_var(self, monkeypatch):
        monkeypatch.setenv("SLOWQL_TELEMETRY", "false")
        telemetry = Telemetry()
        assert not telemetry.enabled

    def test_track_analysis_disabled_no_output(self, monkeypatch, capsys):
        monkeypatch.setenv("SLOWQL_TELEMETRY", "false")
        telemetry = Telemetry()
        telemetry.track_analysis({"key": "value"})
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_track_analysis_enabled_output(self, monkeypatch, capsys):
        monkeypatch.setenv("SLOWQL_TELEMETRY", "true")
        telemetry = Telemetry()
        metrics = {"total_issues": 5, "parse_time": 0.1}
        telemetry.track_analysis(metrics)
        captured = capsys.readouterr()
        assert "Telemetry:" in captured.out
        assert str(metrics) in captured.out
        assert captured.err == ""

    def test_track_analysis_with_different_case(self, monkeypatch):
        monkeypatch.setenv("SLOWQL_TELEMETRY", "TRUE")
        telemetry = Telemetry()
        assert telemetry.enabled
        monkeypatch.setenv("SLOWQL_TELEMETRY", "False")
        telemetry = Telemetry()
        assert not telemetry.enabled
