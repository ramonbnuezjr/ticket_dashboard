"""Tests for src/components/ai_patterns.py."""

from __future__ import annotations

from src.components.ai_patterns import ai_pattern_card, ai_pattern_section, render_ai_results
from src.data.models import AlertSeverity, PatternAlert


def _make_alert(
    severity: AlertSeverity = AlertSeverity.WARNING,
    title: str = "Monitor cluster",
    description: str = "27 tickets at Garrison.",
    count: int = 27,
) -> PatternAlert:
    return PatternAlert(severity=severity, title=title, description=description, count=count)


class TestAiPatternSection:
    def test_returns_component(self) -> None:
        section = ai_pattern_section(has_key=True)
        assert section is not None

    def test_has_correct_id(self) -> None:
        section = ai_pattern_section(has_key=True)
        assert section.id == "ai-pattern-section"

    def test_button_enabled_when_key_present(self) -> None:
        section = ai_pattern_section(has_key=True)
        serialized = str(section.to_plotly_json())
        assert "ai-run-btn" in serialized

    def test_button_disabled_when_no_key(self) -> None:
        section = ai_pattern_section(has_key=False)
        serialized = str(section.to_plotly_json())
        assert "ANTHROPIC_API_KEY" in serialized

    def test_contains_loading_wrapper(self) -> None:
        section = ai_pattern_section(has_key=True)
        serialized = str(section.to_plotly_json())
        assert "ai-pattern-results" in serialized

    def test_claude_badge_present(self) -> None:
        section = ai_pattern_section(has_key=True)
        serialized = str(section.to_plotly_json())
        assert "Claude Sonnet" in serialized


class TestAiPatternCard:
    def test_returns_component(self) -> None:
        card = ai_pattern_card(_make_alert())
        assert card is not None

    def test_severity_label_present(self) -> None:
        card = ai_pattern_card(_make_alert(severity=AlertSeverity.CRITICAL))
        serialized = str(card.to_plotly_json())
        assert "CRITICAL" in serialized

    def test_count_present(self) -> None:
        card = ai_pattern_card(_make_alert(count=42))
        serialized = str(card.to_plotly_json())
        assert "42" in serialized

    def test_title_present(self) -> None:
        card = ai_pattern_card(_make_alert(title="Unique title XYZ"))
        serialized = str(card.to_plotly_json())
        assert "Unique title XYZ" in serialized


class TestRenderAiResults:
    def test_empty_list_returns_no_patterns_message(self) -> None:
        result = render_ai_results([])
        serialized = str(result)
        assert "No new patterns" in serialized

    def test_single_alert_renders(self) -> None:
        result = render_ai_results([_make_alert()])
        assert len(result) == 1  # one row of cards

    def test_four_alerts_render_in_two_rows(self) -> None:
        alerts = [_make_alert(title=f"Alert {i}") for i in range(4)]
        result = render_ai_results(alerts)
        assert len(result) == 2  # ceil(4/3) = 2 rows

    def test_six_alerts_render_in_two_rows(self) -> None:
        alerts = [_make_alert(title=f"Alert {i}") for i in range(6)]
        result = render_ai_results(alerts)
        assert len(result) == 2  # ceil(6/3) = 2 rows

    def test_seven_alerts_render_in_three_rows(self) -> None:
        alerts = [_make_alert(title=f"Alert {i}") for i in range(7)]
        result = render_ai_results(alerts)
        assert len(result) == 3  # ceil(7/3) = 3 rows
