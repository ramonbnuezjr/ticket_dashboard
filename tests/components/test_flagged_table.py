"""Tests for src/components/flagged_table.py."""

from __future__ import annotations

import json

from src.components.flagged_table import flagged_table
from src.data.models import FlaggedTicket, TicketState


def _make_flagged() -> list[FlaggedTicket]:
    return [
        FlaggedTicket(
            number="INC1784393",
            state=TicketState.Assigned,
            age_days=25,
            pattern="Misrouted",
            issue_summary="Broken headset bounced from RSA",
            owner="N. Cabrera (queue)",
        ),
        FlaggedTicket(
            number="INC1417433",
            state=TicketState.WorkInProgress,
            age_days=388,
            pattern="Zombie · 7 notes",
            issue_summary="Lexmark printer — repair vs. replace decision unresolved",
            owner="N. Babino",
        ),
    ]


class TestFlaggedTable:
    def test_returns_component(self) -> None:
        assert flagged_table(_make_flagged()) is not None

    def test_has_correct_id(self) -> None:
        assert flagged_table(_make_flagged()).id == "flagged-table-section"

    def test_ticket_numbers_in_data(self) -> None:
        serialized = json.dumps(flagged_table(_make_flagged()).to_plotly_json())
        assert "INC1784393" in serialized
        assert "INC1417433" in serialized

    def test_age_values_present(self) -> None:
        serialized = json.dumps(flagged_table(_make_flagged()).to_plotly_json())
        assert "25" in serialized
        assert "388" in serialized

    def test_empty_list_renders(self) -> None:
        component = flagged_table([])
        assert component is not None
