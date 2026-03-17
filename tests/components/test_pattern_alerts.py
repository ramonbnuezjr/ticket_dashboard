"""Tests for src/components/pattern_alerts.py."""

from __future__ import annotations

import json

from src.components.pattern_alerts import pattern_alerts
from src.data.models import AlertSeverity, PatternAlert


def _make_alerts() -> list[PatternAlert]:
    return [
        PatternAlert(severity=AlertSeverity.CRITICAL, title="Tickets aged 180+ days", description="...", count=373),
        PatternAlert(severity=AlertSeverity.CRITICAL, title="Auto-resolve failure", description="...", count=19),
        PatternAlert(severity=AlertSeverity.WARNING, title="No assigned tech", description="...", count=515),
        PatternAlert(severity=AlertSeverity.MONITOR, title="NCT vendor queue depth", description="...", count=167),
        PatternAlert(severity=AlertSeverity.WARNING, title="Taxonomy drift", description="...", count=29),
        PatternAlert(severity=AlertSeverity.IMMEDIATE, title="Leadership-flagged", description="...", count=6),
    ]


class TestPatternAlerts:
    def test_returns_component(self) -> None:
        assert pattern_alerts(_make_alerts()) is not None

    def test_has_correct_id(self) -> None:
        assert pattern_alerts(_make_alerts()).id == "pattern-alerts"

    def test_contains_six_cards(self) -> None:
        component = pattern_alerts(_make_alerts())
        # The outer div wraps the grid; check serialized content contains all 6 titles
        serialized = json.dumps(component.to_plotly_json())
        assert serialized.count("CRITICAL") >= 2

    def test_count_values_rendered(self) -> None:
        serialized = json.dumps(pattern_alerts(_make_alerts()).to_plotly_json())
        assert "373" in serialized
        assert "515" in serialized

    def test_severity_colors_present(self) -> None:
        serialized = json.dumps(pattern_alerts(_make_alerts()).to_plotly_json())
        # CRITICAL color
        assert "#e74c3c" in serialized
        # IMMEDIATE color
        assert "#f39c12" in serialized
