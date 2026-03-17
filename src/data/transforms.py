"""Pure compute functions that derive dashboard data from a list of Tickets.

All functions are stateless and free of side effects, making them fully testable
without any I/O or framework dependency.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from src.data.models import (
    AlertSeverity,
    FlaggedTicket,
    KpiData,
    PatternAlert,
    Ticket,
    TicketCategory,
    TicketState,
)

_AGE_BUCKETS: list[tuple[str, int, int]] = [
    ("0-30d", 0, 30),
    ("31-90d", 31, 90),
    ("91-180d", 91, 180),
    ("181-365d", 181, 365),
    ("365+d", 366, 999_999),
]


def compute_kpis(tickets: list[Ticket]) -> KpiData:
    """Compute the six headline KPI values from a ticket list."""
    total = len(tickets)
    active = [t for t in tickets if t.is_active]
    active_open = len(active)
    active_pct = round(active_open / total * 100, 1) if total else 0.0

    vendor_queue = sum(
        1 for t in tickets if t.is_active and t.state == TicketState.OnHold and t.is_vendor_hold
    )
    unassigned = sum(1 for t in active if t.assigned_tech is None)
    misclassified = sum(
        1 for t in active if t.category in TicketCategory.misrouted_categories()
    )
    auto_resolve_fail = sum(1 for t in active if t.notification_count >= 3)

    return KpiData(
        total=total,
        active_open=active_open,
        active_pct=active_pct,
        vendor_queue=vendor_queue,
        unassigned=unassigned,
        misclassified=misclassified,
        auto_resolve_fail=auto_resolve_fail,
    )


def compute_state_breakdown(tickets: list[Ticket]) -> dict[str, int]:
    """Return a mapping of state label → ticket count."""
    counts: dict[str, int] = defaultdict(int)
    for t in tickets:
        counts[t.state.value] += 1
    return dict(counts)


def compute_monthly_volume(
    tickets: list[Ticket],
    reference_date: date | None = None,
) -> dict[str, int]:
    """Return ordered month → count for the 12 months ending at reference_date.

    Args:
        tickets: Full ticket list; all creation dates are considered.
        reference_date: The end of the 12-month window. Defaults to today.

    Returns:
        Ordered dict of "YYYY-MM" → count, all 12 months present (zero-filled).
    """
    if reference_date is None:
        reference_date = date.today()

    # Build the ordered list of the last 12 year-month keys.
    months: list[str] = []
    year, month = reference_date.year, reference_date.month
    for _ in range(12):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()

    counts: dict[str, int] = {m: 0 for m in months}
    for t in tickets:
        key = f"{t.created_date.year:04d}-{t.created_date.month:02d}"
        if key in counts:
            counts[key] += 1
    return counts


def compute_age_distribution(tickets: list[Ticket]) -> dict[str, int]:
    """Return age-bucket → count for active tickets only."""
    result = {label: 0 for label, _, _ in _AGE_BUCKETS}
    for t in tickets:
        if not t.is_active:
            continue
        for label, lo, hi in _AGE_BUCKETS:
            if lo <= t.age_days <= hi:
                result[label] += 1
                break
    return result


def compute_category_breakdown(tickets: list[Ticket]) -> dict[str, int]:
    """Return category → count for active tickets, sorted descending."""
    counts: dict[str, int] = defaultdict(int)
    for t in tickets:
        if t.is_active:
            counts[t.category.value] += 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def compute_pattern_alerts(tickets: list[Ticket]) -> list[PatternAlert]:
    """Compute all six operational pattern alerts from the ticket list.

    Returns:
        Exactly six PatternAlert objects in the order shown in the dashboard.
    """
    active = [t for t in tickets if t.is_active]

    aged_180 = sum(1 for t in active if t.age_days > 180)
    auto_resolve = sum(1 for t in active if t.notification_count >= 3)
    unassigned = sum(1 for t in active if t.assigned_tech is None)
    vendor = sum(
        1 for t in tickets
        if t.state == TicketState.OnHold and t.is_vendor_hold
    )
    taxonomy = sum(1 for t in active if t.category in TicketCategory.misrouted_categories())
    leadership = sum(1 for t in tickets if t.is_leadership_flagged)

    return [
        PatternAlert(
            severity=AlertSeverity.CRITICAL,
            title="Tickets aged 180+ days",
            description=(
                "Active, not closed — some open since Aug 2024. "
                "Requires N. Cabrera sweep"
            ),
            count=aged_180,
        ),
        PatternAlert(
            severity=AlertSeverity.CRITICAL,
            title="Auto-resolve business rule failure",
            description=(
                "3+ notifications sent — ticket state not transitioning. "
                "Platform bug confirmed"
            ),
            count=auto_resolve,
        ),
        PatternAlert(
            severity=AlertSeverity.WARNING,
            title="No assigned tech — active queue",
            description=(
                "74% of active queue has no owner. "
                "All assignment is group-level only"
            ),
            count=unassigned,
        ),
        PatternAlert(
            severity=AlertSeverity.MONITOR,
            title="NCT vendor queue depth",
            description=(
                "Audit for closed NCT work orders with still-open ServiceNow tickets "
                "(e.g. INC1755669)"
            ),
            count=vendor,
        ),
        PatternAlert(
            severity=AlertSeverity.WARNING,
            title="Taxonomy drift — active queue",
            description=(
                "Remote Access (22), Software/App (5), Access/Security (1) "
                "misrouted to HW Repair"
            ),
            count=taxonomy,
        ),
        PatternAlert(
            severity=AlertSeverity.IMMEDIATE,
            title="Leadership-flagged tickets",
            description="Misrouted, dead vendor calls, zombie tickets — detail below",
            count=leadership,
        ),
    ]


def compute_flagged_tickets(tickets: list[Ticket]) -> list[FlaggedTicket]:
    """Return the union of all pattern-rule flagged tickets, deduplicated.

    Priority order for pattern label when a ticket matches multiple rules:
    leadership > auto-resolve > aged > misrouted.
    """
    seen: set[str] = set()
    result: list[FlaggedTicket] = []

    def _add(t: Ticket, pattern: str, fallback_summary: str) -> None:
        if t.number in seen:
            return
        seen.add(t.number)
        # Use the real ServiceNow short_description when available; fall back to
        # the computed summary so mock data and real CSV both look meaningful.
        issue_summary = t.short_description or fallback_summary
        result.append(
            FlaggedTicket(
                number=t.number,
                state=t.state,
                age_days=t.age_days,
                pattern=pattern,
                issue_summary=issue_summary,
                owner=t.assigned_tech,
            )
        )

    # Leadership-flagged (highest priority)
    for t in tickets:
        if t.is_leadership_flagged:
            _add(t, "Leadership-flagged", "Flagged for leadership review")

    # Auto-resolve failures
    for t in tickets:
        if t.is_active and t.notification_count >= 3:
            _add(
                t,
                "Auto-resolve fail",
                f"Awaiting Caller · {t.notification_count} notifications sent · "
                "business rule not closing ticket",
            )

    # Aged 180+
    for t in tickets:
        if t.is_active and t.age_days > 180:
            _add(t, "Aged 180+d", f"Active ticket open for {t.age_days} days without resolution")

    # Misrouted
    for t in tickets:
        if t.is_active and t.category in TicketCategory.misrouted_categories():
            _add(
                t,
                "Wrong queue",
                f"{t.category.value} ticket in HW Repair queue — should route elsewhere",
            )

    return result


def compute_location_heatmap(tickets: list[Ticket]) -> list[dict[str, Any]]:
    """Return one record per location with heat map metrics.

    Each record contains:
        location, total, pct_active, avg_age, on_hold_count

    avg_age is computed over active tickets only.  Locations with zero tickets
    are excluded.
    """
    grouped: dict[str, list[Ticket]] = defaultdict(list)
    for t in tickets:
        grouped[t.location].append(t)

    result: list[dict[str, Any]] = []
    for location, group in grouped.items():
        total = len(group)
        active = [t for t in group if t.is_active]
        on_hold = sum(1 for t in group if t.state == TicketState.OnHold)
        pct_active = round(len(active) / total * 100, 1) if total else 0.0
        avg_age = round(sum(t.age_days for t in active) / len(active), 1) if active else 0.0

        result.append(
            {
                "location": location,
                "total": total,
                "pct_active": pct_active,
                "avg_age": avg_age,
                "on_hold_count": on_hold,
            }
        )
    return result
