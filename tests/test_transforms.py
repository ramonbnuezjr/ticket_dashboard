"""Tests for src/data/transforms.py — all pure compute functions."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.data.models import (
    AlertSeverity,
    Ticket,
    TicketCategory,
    TicketState,
)
from src.data.transforms import (
    compute_age_distribution,
    compute_category_breakdown,
    compute_flagged_tickets,
    compute_kpis,
    compute_location_heatmap,
    compute_monthly_volume,
    compute_pattern_alerts,
    compute_state_breakdown,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = date(2026, 3, 16)


def _t(
    *,
    number: str = "INC0000001",
    state: TicketState = TicketState.Assigned,
    age_days: int = 10,
    category: TicketCategory = TicketCategory.Hardware,
    assigned_tech: str | None = "J. Smith",
    location: str = "Building A",
    created_date: date | None = None,
    notification_count: int = 0,
    is_vendor_hold: bool = False,
    is_leadership_flagged: bool = False,
) -> Ticket:
    if created_date is None:
        created_date = TODAY - timedelta(days=age_days)
    return Ticket(
        number=number,
        state=state,
        age_days=age_days,
        category=category,
        assigned_tech=assigned_tech,
        location=location,
        created_date=created_date,
        notification_count=notification_count,
        is_vendor_hold=is_vendor_hold,
        is_leadership_flagged=is_leadership_flagged,
    )


# ---------------------------------------------------------------------------
# compute_kpis
# ---------------------------------------------------------------------------

class TestComputeKpis:
    def test_totals(self) -> None:
        tickets = [
            _t(number="INC1", state=TicketState.Assigned),
            _t(number="INC2", state=TicketState.Closed),
            _t(number="INC3", state=TicketState.OnHold, is_vendor_hold=True),
        ]
        kpi = compute_kpis(tickets)
        assert kpi.total == 3
        assert kpi.active_open == 2

    def test_active_pct(self) -> None:
        tickets = [_t(number=f"INC{i}", state=TicketState.Assigned) for i in range(4)]
        tickets += [_t(number=f"INC_C{i}", state=TicketState.Closed) for i in range(6)]
        kpi = compute_kpis(tickets)
        assert kpi.active_pct == pytest.approx(40.0)

    def test_vendor_queue(self) -> None:
        tickets = [
            _t(number="INC1", state=TicketState.OnHold, is_vendor_hold=True),
            _t(number="INC2", state=TicketState.OnHold, is_vendor_hold=False),
            _t(number="INC3", state=TicketState.Assigned, is_vendor_hold=True),
        ]
        kpi = compute_kpis(tickets)
        assert kpi.vendor_queue == 1  # only On Hold + vendor

    def test_unassigned(self) -> None:
        tickets = [
            _t(number="INC1", state=TicketState.Assigned, assigned_tech=None),
            _t(number="INC2", state=TicketState.Assigned, assigned_tech="J. Smith"),
            _t(number="INC3", state=TicketState.Closed, assigned_tech=None),
        ]
        kpi = compute_kpis(tickets)
        assert kpi.unassigned == 1  # only active + no tech

    def test_misclassified(self) -> None:
        tickets = [
            _t(number="INC1", state=TicketState.Assigned, category=TicketCategory.RemoteAccess),
            _t(number="INC2", state=TicketState.Assigned, category=TicketCategory.Hardware),
            _t(number="INC3", state=TicketState.Closed, category=TicketCategory.SoftwareApp),
        ]
        kpi = compute_kpis(tickets)
        assert kpi.misclassified == 1  # active + wrong category

    def test_auto_resolve_fail(self) -> None:
        tickets = [
            _t(number="INC1", state=TicketState.Assigned, notification_count=3),
            _t(number="INC2", state=TicketState.Assigned, notification_count=2),
            _t(number="INC3", state=TicketState.Assigned, notification_count=4),
        ]
        kpi = compute_kpis(tickets)
        assert kpi.auto_resolve_fail == 2  # notification_count >= 3 and active

    def test_empty_list(self) -> None:
        kpi = compute_kpis([])
        assert kpi.total == 0
        assert kpi.active_pct == 0.0


# ---------------------------------------------------------------------------
# compute_state_breakdown
# ---------------------------------------------------------------------------

class TestComputeStateBreakdown:
    def test_counts_by_state(self) -> None:
        tickets = [
            _t(number="INC1", state=TicketState.Assigned),
            _t(number="INC2", state=TicketState.Assigned),
            _t(number="INC3", state=TicketState.Closed),
        ]
        result = compute_state_breakdown(tickets)
        assert result["Assigned"] == 2
        assert result["Closed"] == 1
        assert result.get("OnHold", 0) == 0

    def test_all_states_present(self) -> None:
        tickets = [_t(number=f"INC{i}") for i in range(3)]
        result = compute_state_breakdown(tickets)
        assert "Assigned" in result


# ---------------------------------------------------------------------------
# compute_monthly_volume
# ---------------------------------------------------------------------------

class TestComputeMonthlyVolume:
    def test_groups_by_year_month(self) -> None:
        tickets = [
            _t(number="INC1", created_date=date(2025, 6, 1)),
            _t(number="INC2", created_date=date(2025, 6, 15)),
            _t(number="INC3", created_date=date(2025, 7, 1)),
        ]
        result = compute_monthly_volume(tickets, reference_date=date(2026, 3, 16))
        assert result["2025-06"] == 2
        assert result["2025-07"] == 1

    def test_returns_last_12_months(self) -> None:
        result = compute_monthly_volume([], reference_date=date(2026, 3, 16))
        assert len(result) == 12

    def test_months_are_sorted(self) -> None:
        result = compute_monthly_volume([], reference_date=date(2026, 3, 16))
        keys = list(result.keys())
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# compute_age_distribution
# ---------------------------------------------------------------------------

class TestComputeAgeDistribution:
    def test_buckets(self) -> None:
        tickets = [
            _t(number="INC1", state=TicketState.Assigned, age_days=15),
            _t(number="INC2", state=TicketState.Assigned, age_days=60),
            _t(number="INC3", state=TicketState.Assigned, age_days=120),
            _t(number="INC4", state=TicketState.Assigned, age_days=200),
            _t(number="INC5", state=TicketState.Assigned, age_days=400),
            _t(number="INC6", state=TicketState.Closed, age_days=400),  # excluded
        ]
        result = compute_age_distribution(tickets)
        assert result["0-30d"] == 1
        assert result["31-90d"] == 1
        assert result["91-180d"] == 1
        assert result["181-365d"] == 1
        assert result["365+d"] == 1

    def test_closed_tickets_excluded(self) -> None:
        tickets = [_t(number="INC1", state=TicketState.Closed, age_days=500)]
        result = compute_age_distribution(tickets)
        assert result["365+d"] == 0

    def test_bucket_keys_present(self) -> None:
        result = compute_age_distribution([])
        assert set(result.keys()) == {"0-30d", "31-90d", "91-180d", "181-365d", "365+d"}


# ---------------------------------------------------------------------------
# compute_category_breakdown
# ---------------------------------------------------------------------------

class TestComputeCategoryBreakdown:
    def test_active_only(self) -> None:
        tickets = [
            _t(number="INC1", state=TicketState.Assigned, category=TicketCategory.Hardware),
            _t(number="INC2", state=TicketState.Closed, category=TicketCategory.Hardware),
            _t(number="INC3", state=TicketState.Assigned, category=TicketCategory.RemoteAccess),
        ]
        result = compute_category_breakdown(tickets)
        assert result["Hardware"] == 1
        assert result["Remote Access"] == 1

    def test_sorted_descending(self) -> None:
        tickets = [
            _t(number=f"INC_H{i}", state=TicketState.Assigned, category=TicketCategory.Hardware)
            for i in range(5)
        ] + [
            _t(number=f"INC_R{i}", state=TicketState.Assigned, category=TicketCategory.RemoteAccess)
            for i in range(2)
        ]
        result = compute_category_breakdown(tickets)
        values = list(result.values())
        assert values == sorted(values, reverse=True)


# ---------------------------------------------------------------------------
# compute_pattern_alerts
# ---------------------------------------------------------------------------

class TestComputePatternAlerts:
    def _make_tickets(self) -> list[Ticket]:
        """Small ticket set that produces all six pattern types."""
        tickets: list[Ticket] = []
        # aged 180+
        for i in range(3):
            tickets.append(_t(number=f"OLD{i}", state=TicketState.Assigned, age_days=200))
        # auto-resolve fail
        for i in range(2):
            tickets.append(_t(number=f"ARF{i}", state=TicketState.Assigned, notification_count=3))
        # unassigned active
        for i in range(4):
            tickets.append(
                _t(number=f"UNASSIGNED{i}", state=TicketState.Assigned, assigned_tech=None)
            )
        # vendor hold
        for i in range(2):
            tickets.append(
                _t(number=f"VENDOR{i}", state=TicketState.OnHold, is_vendor_hold=True)
            )
        # misclassified
        tickets.append(
            _t(number="MISC1", state=TicketState.Assigned, category=TicketCategory.RemoteAccess)
        )
        # leadership flagged
        tickets.append(_t(number="LEAD1", state=TicketState.Assigned, is_leadership_flagged=True))
        return tickets

    def test_returns_six_alerts(self) -> None:
        alerts = compute_pattern_alerts(self._make_tickets())
        assert len(alerts) == 6

    def test_critical_alerts_present(self) -> None:
        alerts = compute_pattern_alerts(self._make_tickets())
        severities = [a.severity for a in alerts]
        assert AlertSeverity.CRITICAL in severities

    def test_immediate_alert_present(self) -> None:
        alerts = compute_pattern_alerts(self._make_tickets())
        severities = [a.severity for a in alerts]
        assert AlertSeverity.IMMEDIATE in severities

    def test_aged_count_matches(self) -> None:
        tickets = [
            _t(number=f"OLD{i}", state=TicketState.Assigned, age_days=200) for i in range(5)
        ]
        alerts = compute_pattern_alerts(tickets)
        aged = next(a for a in alerts if "180" in a.title)
        assert aged.count == 5


# ---------------------------------------------------------------------------
# compute_flagged_tickets
# ---------------------------------------------------------------------------

class TestComputeFlaggedTickets:
    def test_leadership_flagged_included(self) -> None:
        tickets = [
            _t(number="INC_L1", state=TicketState.Assigned, is_leadership_flagged=True),
            _t(number="INC_NORMAL", state=TicketState.Assigned),
        ]
        flagged = compute_flagged_tickets(tickets)
        numbers = [f.number for f in flagged]
        assert "INC_L1" in numbers
        assert "INC_NORMAL" not in numbers

    def test_auto_resolve_fail_included(self) -> None:
        tickets = [
            _t(number="INC_ARF", state=TicketState.Assigned, notification_count=3),
        ]
        flagged = compute_flagged_tickets(tickets)
        assert any(f.number == "INC_ARF" for f in flagged)

    def test_no_duplicates(self) -> None:
        tickets = [
            _t(
                number="INC_BOTH",
                state=TicketState.Assigned,
                notification_count=3,
                is_leadership_flagged=True,
            )
        ]
        flagged = compute_flagged_tickets(tickets)
        numbers = [f.number for f in flagged]
        assert len(numbers) == len(set(numbers))


# ---------------------------------------------------------------------------
# compute_location_heatmap
# ---------------------------------------------------------------------------

class TestComputeLocationHeatmap:
    def test_groups_by_location(self) -> None:
        tickets = [
            _t(number="INC1", location="Building A", state=TicketState.Assigned),
            _t(number="INC2", location="Building A", state=TicketState.Closed),
            _t(number="INC3", location="Building B", state=TicketState.Assigned),
        ]
        result = compute_location_heatmap(tickets)
        locations = {r["location"] for r in result}
        assert "Building A" in locations
        assert "Building B" in locations

    def test_pct_active_calculated(self) -> None:
        tickets = [
            _t(number="INC1", location="Building A", state=TicketState.Assigned),
            _t(number="INC2", location="Building A", state=TicketState.Closed),
        ]
        result = compute_location_heatmap(tickets)
        entry = next(r for r in result if r["location"] == "Building A")
        assert entry["pct_active"] == pytest.approx(50.0)

    def test_avg_age_active_only(self) -> None:
        tickets = [
            _t(number="INC1", location="Building A", state=TicketState.Assigned, age_days=10),
            _t(number="INC2", location="Building A", state=TicketState.Assigned, age_days=30),
            _t(number="INC3", location="Building A", state=TicketState.Closed, age_days=999),
        ]
        result = compute_location_heatmap(tickets)
        entry = next(r for r in result if r["location"] == "Building A")
        assert entry["avg_age"] == pytest.approx(20.0)

    def test_on_hold_count(self) -> None:
        tickets = [
            _t(number="INC1", location="Building A", state=TicketState.OnHold),
            _t(number="INC2", location="Building A", state=TicketState.Assigned),
        ]
        result = compute_location_heatmap(tickets)
        entry = next(r for r in result if r["location"] == "Building A")
        assert entry["on_hold_count"] == 1

    def test_total_count_included(self) -> None:
        tickets = [
            _t(number=f"INC{i}", location="Building A") for i in range(5)
        ]
        result = compute_location_heatmap(tickets)
        entry = next(r for r in result if r["location"] == "Building A")
        assert entry["total"] == 5
