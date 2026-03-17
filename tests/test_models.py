"""Tests for src/data/models.py — Pydantic model validation."""

from __future__ import annotations

import pytest
from datetime import date

from src.data.models import (
    AlertSeverity,
    FlaggedTicket,
    KpiData,
    PatternAlert,
    Ticket,
    TicketCategory,
    TicketState,
)


# ---------------------------------------------------------------------------
# TicketState
# ---------------------------------------------------------------------------

class TestTicketState:
    def test_all_states_defined(self) -> None:
        expected = {
            "Assigned",
            "Closed",
            "OnHold",
            "WorkInProgress",
            "Resolved",
            "Cancelled",
        }
        assert {s.value for s in TicketState} == expected

    def test_active_states(self) -> None:
        active = TicketState.active_states()
        assert TicketState.Assigned in active
        assert TicketState.OnHold in active
        assert TicketState.WorkInProgress in active
        assert TicketState.Closed not in active
        assert TicketState.Resolved not in active
        assert TicketState.Cancelled not in active


# ---------------------------------------------------------------------------
# TicketCategory
# ---------------------------------------------------------------------------

class TestTicketCategory:
    def test_hardware_is_primary(self) -> None:
        assert TicketCategory.Hardware.value == "Hardware"

    def test_misrouted_categories(self) -> None:
        misrouted = TicketCategory.misrouted_categories()
        assert TicketCategory.RemoteAccess in misrouted
        assert TicketCategory.SoftwareApp in misrouted
        assert TicketCategory.Hardware not in misrouted


# ---------------------------------------------------------------------------
# Ticket
# ---------------------------------------------------------------------------

class TestTicket:
    def _make_ticket(self, **overrides: object) -> Ticket:
        defaults: dict[str, object] = {
            "number": "INC0000001",
            "state": TicketState.Assigned,
            "age_days": 10,
            "category": TicketCategory.Hardware,
            "assigned_tech": "J. Smith",
            "location": "109 E 16th St",
            "created_date": date(2025, 6, 1),
            "notification_count": 0,
            "is_vendor_hold": False,
            "is_leadership_flagged": False,
        }
        defaults.update(overrides)
        return Ticket(**defaults)  # type: ignore[arg-type]

    def test_valid_ticket(self) -> None:
        t = self._make_ticket()
        assert t.number == "INC0000001"
        assert t.state == TicketState.Assigned

    def test_assigned_tech_optional(self) -> None:
        t = self._make_ticket(assigned_tech=None)
        assert t.assigned_tech is None

    def test_is_active_true_for_assigned(self) -> None:
        t = self._make_ticket(state=TicketState.Assigned)
        assert t.is_active is True

    def test_is_active_false_for_closed(self) -> None:
        t = self._make_ticket(state=TicketState.Closed)
        assert t.is_active is False

    def test_is_active_false_for_resolved(self) -> None:
        t = self._make_ticket(state=TicketState.Resolved)
        assert t.is_active is False

    def test_is_active_false_for_cancelled(self) -> None:
        t = self._make_ticket(state=TicketState.Cancelled)
        assert t.is_active is False

    def test_is_active_true_for_on_hold(self) -> None:
        t = self._make_ticket(state=TicketState.OnHold)
        assert t.is_active is True

    def test_number_validation_rejects_empty(self) -> None:
        with pytest.raises(Exception):
            self._make_ticket(number="")

    def test_age_days_non_negative(self) -> None:
        with pytest.raises(Exception):
            self._make_ticket(age_days=-1)

    def test_notification_count_non_negative(self) -> None:
        with pytest.raises(Exception):
            self._make_ticket(notification_count=-1)


# ---------------------------------------------------------------------------
# KpiData
# ---------------------------------------------------------------------------

class TestKpiData:
    def test_valid_kpi(self) -> None:
        kpi = KpiData(
            total=1102,
            active_open=696,
            active_pct=63.2,
            vendor_queue=167,
            unassigned=515,
            misclassified=29,
            auto_resolve_fail=19,
        )
        assert kpi.total == 1102
        assert kpi.active_pct == pytest.approx(63.2)

    def test_totals_non_negative(self) -> None:
        with pytest.raises(Exception):
            KpiData(
                total=-1,
                active_open=0,
                active_pct=0.0,
                vendor_queue=0,
                unassigned=0,
                misclassified=0,
                auto_resolve_fail=0,
            )

    def test_active_pct_range(self) -> None:
        with pytest.raises(Exception):
            KpiData(
                total=100,
                active_open=50,
                active_pct=110.0,
                vendor_queue=0,
                unassigned=0,
                misclassified=0,
                auto_resolve_fail=0,
            )


# ---------------------------------------------------------------------------
# AlertSeverity
# ---------------------------------------------------------------------------

class TestAlertSeverity:
    def test_severity_order(self) -> None:
        assert AlertSeverity.CRITICAL.value == "CRITICAL"
        assert AlertSeverity.WARNING.value == "WARNING"
        assert AlertSeverity.MONITOR.value == "MONITOR"
        assert AlertSeverity.IMMEDIATE.value == "IMMEDIATE"


# ---------------------------------------------------------------------------
# PatternAlert
# ---------------------------------------------------------------------------

class TestPatternAlert:
    def test_valid_alert(self) -> None:
        alert = PatternAlert(
            severity=AlertSeverity.CRITICAL,
            title="Tickets aged 180+ days",
            description="Active, not closed — some open since Aug 2024.",
            count=373,
        )
        assert alert.count == 373
        assert alert.severity == AlertSeverity.CRITICAL

    def test_count_non_negative(self) -> None:
        with pytest.raises(Exception):
            PatternAlert(
                severity=AlertSeverity.WARNING,
                title="Test",
                description="Test",
                count=-1,
            )


# ---------------------------------------------------------------------------
# FlaggedTicket
# ---------------------------------------------------------------------------

class TestFlaggedTicket:
    def test_valid_flagged_ticket(self) -> None:
        ft = FlaggedTicket(
            number="INC1784393",
            state=TicketState.Assigned,
            age_days=25,
            pattern="Misrouted",
            issue_summary="Broken headset bounced from RSA — no owner, no resolution path",
            owner="N. Cabrera (queue)",
        )
        assert ft.number == "INC1784393"
        assert ft.age_days == 25

    def test_owner_optional(self) -> None:
        ft = FlaggedTicket(
            number="INC1784393",
            state=TicketState.Assigned,
            age_days=25,
            pattern="Misrouted",
            issue_summary="Summary",
            owner=None,
        )
        assert ft.owner is None
