"""Tests for src/ai/analyzer.py — mocks Anthropic API throughout."""

from __future__ import annotations

import json
from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.ai.analyzer import (
    _build_user_message,
    _parse_response,
    _to_pattern_alert,
    discover_patterns,
)
from src.data.models import AlertSeverity, PatternAlert, Ticket, TicketCategory, TicketState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_ticket(
    number: str = "INC001",
    state: TicketState = TicketState.Assigned,
    age_days: int = 10,
    category: TicketCategory = TicketCategory.Hardware,
    location: str = "Clermont",
    short_description: str | None = "Laptop screen broken",
    notification_count: int = 0,
) -> Ticket:
    return Ticket(
        number=number,
        state=state,
        age_days=age_days,
        category=category,
        assigned_tech="Jane Smith",
        location=location,
        created_date=date(2025, 8, 1),
        notification_count=notification_count,
        is_vendor_hold=False,
        is_leadership_flagged=False,
        short_description=short_description,
    )


def _make_tickets(n: int = 5) -> list[Ticket]:
    return [_make_ticket(number=f"INC{i:03d}", age_days=i * 10) for i in range(1, n + 1)]


_VALID_RESPONSE_JSON: list[dict[str, Any]] = [
    {
        "title": "Monitor failure cluster at Garrison",
        "description": "27 tickets cite monitor failure at Garrison — possible batch defect.",
        "count": 27,
        "ticket_numbers": ["INC001", "INC002"],
        "severity": "WARNING",
    },
    {
        "title": "Keyboard replacement spike",
        "description": "14 keyboard replacement requests this month, up 60% MoM.",
        "count": 14,
        "ticket_numbers": ["INC003"],
        "severity": "MONITOR",
    },
]


# ---------------------------------------------------------------------------
# _build_user_message
# ---------------------------------------------------------------------------

class TestBuildUserMessage:
    def test_includes_existing_alerts_header(self) -> None:
        msg = _build_user_message(_make_tickets())
        assert "EXISTING ALERTS" in msg

    def test_includes_ticket_numbers(self) -> None:
        tickets = _make_tickets(3)
        msg = _build_user_message(tickets)
        for t in tickets:
            assert t.number in msg

    def test_only_active_tickets_included(self) -> None:
        active = _make_ticket(number="INC_ACTIVE", state=TicketState.Assigned)
        closed = _make_ticket(number="INC_CLOSED", state=TicketState.Closed)
        msg = _build_user_message([active, closed])
        assert "INC_ACTIVE" in msg
        assert "INC_CLOSED" not in msg

    def test_description_truncated(self) -> None:
        long_desc = "X" * 200
        t = _make_ticket(short_description=long_desc)
        msg = _build_user_message([t])
        assert "X" * 200 not in msg  # truncated
        assert "…" in msg

    def test_none_description_handled(self) -> None:
        t = _make_ticket(short_description=None)
        msg = _build_user_message([t])
        assert t.number in msg  # ticket still appears


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_valid_json_array(self) -> None:
        raw = json.dumps(_VALID_RESPONSE_JSON)
        result = _parse_response(raw)
        assert len(result) == 2
        assert result[0]["title"] == "Monitor failure cluster at Garrison"

    def test_strips_markdown_fences(self) -> None:
        raw = f"```json\n{json.dumps(_VALID_RESPONSE_JSON)}\n```"
        result = _parse_response(raw)
        assert isinstance(result, list)

    def test_empty_array(self) -> None:
        assert _parse_response("[]") == []

    def test_invalid_json_raises(self) -> None:
        with pytest.raises((json.JSONDecodeError, ValueError)):
            _parse_response("not json at all")


# ---------------------------------------------------------------------------
# _to_pattern_alert
# ---------------------------------------------------------------------------

class TestToPatternAlert:
    def test_maps_valid_severity(self) -> None:
        alert = _to_pattern_alert(_VALID_RESPONSE_JSON[0])
        assert alert.severity == AlertSeverity.WARNING

    def test_unknown_severity_defaults_to_monitor(self) -> None:
        item = {**_VALID_RESPONSE_JSON[0], "severity": "UNKNOWN_VALUE"}
        alert = _to_pattern_alert(item)
        assert alert.severity == AlertSeverity.MONITOR

    def test_count_mapped(self) -> None:
        alert = _to_pattern_alert(_VALID_RESPONSE_JSON[0])
        assert alert.count == 27

    def test_ticket_numbers_in_description(self) -> None:
        alert = _to_pattern_alert(_VALID_RESPONSE_JSON[0])
        assert "INC001" in alert.description

    def test_returns_pattern_alert_instance(self) -> None:
        alert = _to_pattern_alert(_VALID_RESPONSE_JSON[0])
        assert isinstance(alert, PatternAlert)

    def test_title_truncated_at_80_chars(self) -> None:
        item = {**_VALID_RESPONSE_JSON[0], "title": "A" * 100}
        alert = _to_pattern_alert(item)
        assert len(alert.title) <= 80


# ---------------------------------------------------------------------------
# discover_patterns (integration — API mocked)
# ---------------------------------------------------------------------------

class TestDiscoverPatterns:
    def _mock_response(self, json_data: list[dict]) -> MagicMock:
        content_block = MagicMock()
        content_block.text = json.dumps(json_data)
        response = MagicMock()
        response.content = [content_block]
        return response

    def test_returns_pattern_alerts_on_success(self) -> None:
        mock_resp = self._mock_response(_VALID_RESPONSE_JSON)
        with patch("src.ai.analyzer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            results = discover_patterns(_make_tickets(10), api_key="test-key")
        assert len(results) == 2
        assert all(isinstance(r, PatternAlert) for r in results)

    def test_empty_response_returns_empty_list(self) -> None:
        mock_resp = self._mock_response([])
        with patch("src.ai.analyzer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            results = discover_patterns(_make_tickets(5), api_key="test-key")
        assert results == []

    def test_malformed_json_returns_error_card(self) -> None:
        content_block = MagicMock()
        content_block.text = "This is not JSON"
        mock_resp = MagicMock()
        mock_resp.content = [content_block]
        with patch("src.ai.analyzer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            results = discover_patterns(_make_tickets(5), api_key="test-key")
        assert len(results) == 1
        assert "parse error" in results[0].title.lower()

    def test_only_sends_active_tickets(self) -> None:
        """Verify the prompt only includes active tickets."""
        active = _make_ticket(number="INC_ACTIVE", state=TicketState.Assigned)
        closed = _make_ticket(number="INC_CLOSED", state=TicketState.Closed)

        mock_resp = self._mock_response([])
        captured_prompt: list[str] = []

        def _capture(**kwargs: Any) -> MagicMock:
            captured_prompt.append(kwargs["messages"][0]["content"])
            return mock_resp

        with patch("src.ai.analyzer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.side_effect = _capture
            discover_patterns([active, closed], api_key="test-key")

        assert "INC_ACTIVE" in captured_prompt[0]
        assert "INC_CLOSED" not in captured_prompt[0]
