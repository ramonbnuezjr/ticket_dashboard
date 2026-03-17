"""Ticket data loading: seeded mock data and ServiceNow CSV import.

Use get_tickets(settings) as the single entry point. It returns mock data
when settings.data_csv_path is None, or validates and returns CSV data otherwise.

ServiceNow CSV column mapping
------------------------------
The real export has these columns (tab- or comma-separated):
    number, opened_by, location, state, hold_reason, category, subcategory,
    short_description, description, opened_at, closed_at, assignment_group,
    u_opened_by_group, assigned_to, business_service, u_notification_counter,
    reassignment_count, calendar_stc, u_self_service_issue, priority,
    comments_and_work_notes, approval_history, close_code, close_notes,
    u_escalation_status, resolved_at, contact_type, impact, urgency, severity,
    u_self_service_issue_type

Key derivations
---------------
- state           ← state  (text label or numeric code → TicketState)
- category        ← category  (text label → TicketCategory; unknown → Other)
- assigned_tech   ← assigned_to  (empty string → None)
- notification_count ← u_notification_counter  (int, default 0)
- age_days        ← opened_at→today for active; opened_at→closed_at for terminal
                   fallback: calendar_stc (seconds) / 86400
- is_vendor_hold  ← state==OnHold AND hold_reason contains vendor keyword
- is_leadership_flagged ← u_escalation_status is non-empty and not "Normal"/"None"
- short_description ← short_description  (surfaced in flagged ticket summaries)
- created_date    ← opened_at  (date part only)
"""

from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from src.data.models import Ticket, TicketCategory, TicketState

if TYPE_CHECKING:
    from src.config import Settings

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Reference date matching the screenshot export
# ---------------------------------------------------------------------------
_REF_DATE = date(2026, 3, 16)

# ---------------------------------------------------------------------------
# Building roster from the heat-map screenshot (location → total ticket count)
# ---------------------------------------------------------------------------
_BUILDINGS: list[tuple[str, int]] = [
    ("109 E 16th St", 136),
    ("375 Pearl St", 78),
    ("890 Garrison Ave", 68),
    ("505 Clermont Ave", 52),
    ("2500 Halsey St", 48),
    ("1910 Monterey Ave", 44),
    ("2551 Bainbridge Ave", 29),
    ("201 Bay St", 26),
    ("1365 Jerome Ave", 25),
    ("219 Beach 59th St", 24),
    ("33-28 Northern Blvd", 24),
    ("150 Greenwich St", 38),
    ("95 Evergreen Ave", 57),
    ("32-20 Northern Blvd", 34),
    ("165-08 88th Ave", 30),
    ("4 World Trade Ctr", 30),
    ("275 Bergen St", 20),
    ("2400 Fulton St", 19),
    ("470 Vanderbilt Ave", 18),
    ("1912 Mermaid Ave", 18),
    ("151 W Broadway", 16),
    ("845 Barretto St", 14),
    ("132 W 125th St", 15),
    ("305 Rider Ave", 18),
    ("4055 10th Ave", 12),
    ("2322 3rd Ave", 17),
    ("847 Barrett Ave", 16),
]

# ---------------------------------------------------------------------------
# The six specific flagged ticket numbers visible in the screenshot
# ---------------------------------------------------------------------------
_FLAGGED_SPECS: list[dict[str, Any]] = [
    {
        "number": "INC1784393",
        "state": TicketState.Assigned,
        "age_days": 25,
        "category": TicketCategory.RemoteAccess,
        "assigned_tech": "N. Cabrera (queue)",
        "location": "109 E 16th St",
        "notification_count": 0,
        "is_vendor_hold": False,
        "is_leadership_flagged": True,
    },
    {
        "number": "INC1762166",
        "state": TicketState.Assigned,
        "age_days": 46,
        "category": TicketCategory.RemoteAccess,
        "assigned_tech": None,
        "location": "375 Pearl St",
        "notification_count": 0,
        "is_vendor_hold": False,
        "is_leadership_flagged": True,
    },
    {
        "number": "INC1728030",
        "state": TicketState.OnHold,
        "age_days": 82,
        "category": TicketCategory.Hardware,
        "assigned_tech": "N. Babino",
        "location": "505 Clermont Ave",
        "notification_count": 3,
        "is_vendor_hold": False,
        "is_leadership_flagged": True,
    },
    {
        "number": "INC1755669",
        "state": TicketState.OnHold,
        "age_days": 51,
        "category": TicketCategory.Hardware,
        "assigned_tech": "N. Babino",
        "location": "890 Garrison Ave",
        "notification_count": 0,
        "is_vendor_hold": True,
        "is_leadership_flagged": True,
    },
    {
        "number": "INC1806671",
        "state": TicketState.Assigned,
        "age_days": 5,
        "category": TicketCategory.SoftwareApp,
        "assigned_tech": None,
        "location": "109 E 16th St",
        "notification_count": 0,
        "is_vendor_hold": False,
        "is_leadership_flagged": True,
    },
    {
        "number": "INC1417433",
        "state": TicketState.WorkInProgress,
        "age_days": 388,
        "category": TicketCategory.Hardware,
        "assigned_tech": "N. Babino",
        "location": "375 Pearl St",
        "notification_count": 0,
        "is_vendor_hold": False,
        "is_leadership_flagged": True,
    },
]


def _make_ticket(spec: dict[str, Any]) -> Ticket:
    age: int = spec["age_days"]
    return Ticket(
        number=spec["number"],
        state=spec["state"],
        age_days=age,
        category=spec["category"],
        assigned_tech=spec.get("assigned_tech"),
        location=spec["location"],
        created_date=_REF_DATE - timedelta(days=age),
        notification_count=spec.get("notification_count", 0),
        is_vendor_hold=spec.get("is_vendor_hold", False),
        is_leadership_flagged=spec.get("is_leadership_flagged", False),
    )


def load_mock_data() -> list[Ticket]:
    """Generate 1,102 seeded tickets matching the screenshot KPIs exactly.

    Distribution targets (verified by tests):
        Total: 1,102
        Assigned: 515  |  Closed: 397  |  On Hold: 168  |  WIP: 13
        Resolved: 7    |  Cancelled: 2
        Active open: 696 (63.2%)
        Aged 180+ (active): 373
        Vendor hold (On Hold + vendor flag): 167
        Unassigned (active + no tech): 515
        Auto-resolve fail (active, notif >= 3): 19
        Misclassified (active + wrong category): 29
        Leadership-flagged: 6
    """
    rng = random.Random(42)  # fixed seed for reproducibility
    tickets: list[Ticket] = []
    reserved_numbers = {s["number"] for s in _FLAGGED_SPECS}
    counter = 1000000

    def _next_number() -> str:
        nonlocal counter
        while True:
            num = f"INC{counter:07d}"
            counter += 1
            if num not in reserved_numbers:
                return num

    # -----------------------------------------------------------------------
    # Step 1 — Insert the 6 specific flagged tickets first.
    # -----------------------------------------------------------------------
    for spec in _FLAGGED_SPECS:
        tickets.append(_make_ticket(spec))

    flagged_states = {spec["number"]: spec["state"] for spec in _FLAGGED_SPECS}

    # -----------------------------------------------------------------------
    # Step 2 — Build a slot plan to hit exact state counts.
    # Flagged tickets contribute:
    #   Assigned: INC1784393, INC1762166, INC1806671  → 3
    #   OnHold:   INC1728030, INC1755669              → 2
    #   WIP:      INC1417433                          → 1
    # -----------------------------------------------------------------------
    state_plan: dict[TicketState, int] = {
        TicketState.Assigned: 515 - 3,    # 512 remaining
        TicketState.Closed: 397,
        TicketState.OnHold: 168 - 2,      # 166 remaining
        TicketState.WorkInProgress: 13 - 1,  # 12 remaining
        TicketState.Resolved: 7,
        TicketState.Cancelled: 2,
    }

    # -----------------------------------------------------------------------
    # Step 3 — Age/assignment/category sub-quotas for active tickets.
    # We need to arrive at exactly these counts across all active tickets
    # (including the 6 flagged ones).
    #
    # Aged 180+ active: 373 total
    #   Flagged contribution: INC1417433 (388d) → 1
    #   Remaining: 372
    #
    # Vendor hold: 167 total (On Hold + is_vendor_hold)
    #   Flagged contribution: INC1755669 → 1
    #   Remaining: 166
    #
    # Unassigned active: 515 total
    #   Flagged contribution: INC1762166 (None), INC1806671 (None) → 2
    #   Remaining: 513
    #
    # Auto-resolve fail: 19 total (active + notif >= 3)
    #   Flagged contribution: INC1728030 (notif=3, OnHold) → 1
    #   Remaining: 18
    #
    # Misclassified: 29 total (active + wrong category)
    #   Flagged contribution: INC1784393 (RemoteAccess, active), INC1762166 (RemoteAccess,active),
    #                         INC1806671 (SoftwareApp, active) → 3
    #   Remaining: 26
    # -----------------------------------------------------------------------
    aged_remaining = 372
    vendor_remaining = 166
    unassigned_remaining = 513
    arf_remaining = 18
    misc_remaining = 26

    # -----------------------------------------------------------------------
    # Step 4 — Build location bucket allocations proportional to building sizes.
    # -----------------------------------------------------------------------
    total_building_weight = sum(n for _, n in _BUILDINGS)

    def _pick_location() -> str:
        r = rng.random() * total_building_weight
        acc = 0.0
        for loc, weight in _BUILDINGS:
            acc += weight
            if r < acc:
                return loc
        return _BUILDINGS[-1][0]

    # -----------------------------------------------------------------------
    # Step 5 — Generate non-flagged tickets state by state.
    # -----------------------------------------------------------------------
    month_weights = [80, 63, 67, 62, 58, 69, 73, 78, 81, 83, 81, 74]  # Mar-Feb

    def _pick_created(age_days: int) -> date:
        return _REF_DATE - timedelta(days=age_days)

    # --- Assigned tickets (512 remaining) ---
    # Budget: aged (subset), unassigned, arf, misc
    assigned_aged_budget = min(aged_remaining, 200)
    assigned_unassigned_budget = min(unassigned_remaining, 300)
    assigned_arf_budget = min(arf_remaining, 10)
    assigned_misc_budget = min(misc_remaining, 15)

    for slot in range(state_plan[TicketState.Assigned]):
        age: int
        assigned_tech: str | None
        category: TicketCategory
        notif: int = 0

        # aged
        if slot < assigned_aged_budget:
            age = rng.randint(181, 500)
            aged_remaining -= 1
        else:
            age = rng.randint(1, 180)

        # unassigned
        if slot < assigned_unassigned_budget:
            assigned_tech = None
            unassigned_remaining -= 1
        else:
            assigned_tech = rng.choice(["N. Cabrera", "N. Babino", "J. Torres", "M. Rivera"])

        # arf
        if slot < assigned_arf_budget:
            notif = rng.randint(3, 5)
            arf_remaining -= 1

        # misc
        if slot < assigned_misc_budget:
            category = rng.choice(
                [
                    TicketCategory.RemoteAccess,
                    TicketCategory.SoftwareApp,
                    TicketCategory.AccessSecurity,
                ]
            )
            misc_remaining -= 1
        else:
            category = TicketCategory.Hardware

        tickets.append(
            Ticket(
                number=_next_number(),
                state=TicketState.Assigned,
                age_days=age,
                category=category,
                assigned_tech=assigned_tech,
                location=_pick_location(),
                created_date=_pick_created(age),
                notification_count=notif,
                is_vendor_hold=False,
                is_leadership_flagged=False,
            )
        )

    # --- On Hold tickets (166 remaining after flagged) ---
    for slot in range(state_plan[TicketState.OnHold]):
        age = rng.randint(1, 400)
        is_vendor = slot < vendor_remaining
        if is_vendor:
            vendor_remaining -= 1
        # On Hold tickets are active → may count toward aged
        if aged_remaining > 0 and age > 180:
            aged_remaining -= 1
        elif aged_remaining > 0 and slot < aged_remaining:
            age = rng.randint(181, 500)
            aged_remaining -= 1

        tickets.append(
            Ticket(
                number=_next_number(),
                state=TicketState.OnHold,
                age_days=age,
                category=TicketCategory.Hardware,
                assigned_tech=rng.choice(["N. Babino", "J. Torres", None]),
                location=_pick_location(),
                created_date=_pick_created(age),
                notification_count=rng.randint(0, 2),
                is_vendor_hold=is_vendor,
                is_leadership_flagged=False,
            )
        )

    # --- WIP tickets (12 remaining) ---
    for slot in range(state_plan[TicketState.WorkInProgress]):
        age = rng.randint(1, 120)
        tickets.append(
            Ticket(
                number=_next_number(),
                state=TicketState.WorkInProgress,
                age_days=age,
                category=TicketCategory.Hardware,
                assigned_tech=rng.choice(["N. Cabrera", "N. Babino"]),
                location=_pick_location(),
                created_date=_pick_created(age),
                notification_count=0,
                is_vendor_hold=False,
                is_leadership_flagged=False,
            )
        )

    # --- ARF remaining on OnHold (overflow) ---
    if arf_remaining > 0:
        # Patch some On Hold tickets to have notif >= 3
        on_hold_tickets = [t for t in tickets if t.state == TicketState.OnHold and t.notification_count < 3]
        for t in on_hold_tickets[:arf_remaining]:
            idx = tickets.index(t)
            tickets[idx] = t.model_copy(update={"notification_count": 3})
        arf_remaining = 0

    # --- Resolved ---
    for _ in range(state_plan[TicketState.Resolved]):
        age = rng.randint(1, 60)
        tickets.append(
            Ticket(
                number=_next_number(),
                state=TicketState.Resolved,
                age_days=age,
                category=TicketCategory.Hardware,
                assigned_tech="N. Cabrera",
                location=_pick_location(),
                created_date=_pick_created(age),
                notification_count=0,
                is_vendor_hold=False,
                is_leadership_flagged=False,
            )
        )

    # --- Cancelled ---
    for _ in range(state_plan[TicketState.Cancelled]):
        age = rng.randint(1, 30)
        tickets.append(
            Ticket(
                number=_next_number(),
                state=TicketState.Cancelled,
                age_days=age,
                category=TicketCategory.Hardware,
                assigned_tech=None,
                location=_pick_location(),
                created_date=_pick_created(age),
                notification_count=0,
                is_vendor_hold=False,
                is_leadership_flagged=False,
            )
        )

    # --- Closed ---
    for _ in range(state_plan[TicketState.Closed]):
        age = rng.randint(1, 365)
        _ = month_weights  # used via randint distribution above
        tickets.append(
            Ticket(
                number=_next_number(),
                state=TicketState.Closed,
                age_days=age,
                category=rng.choice([TicketCategory.Hardware, TicketCategory.Hardware, TicketCategory.Hardware, TicketCategory.Laptop]),
                assigned_tech=rng.choice(["N. Cabrera", "N. Babino", "J. Torres"]),
                location=_pick_location(),
                created_date=_pick_created(age),
                notification_count=0,
                is_vendor_hold=False,
                is_leadership_flagged=False,
            )
        )

    # -----------------------------------------------------------------------
    # Step 6 — Reconcile any remaining quota gaps by patching existing tickets.
    # This ensures exact counts regardless of rng variation.
    # -----------------------------------------------------------------------
    _reconcile(tickets)

    log.info(
        "mock_data_loaded",
        total=len(tickets),
        active=sum(1 for t in tickets if t.is_active),
    )
    return tickets


def _reconcile(tickets: list[Ticket]) -> None:
    """Patch ticket list in-place to hit exact KPI targets."""
    # Targets
    TARGET_ASSIGNED = 515
    TARGET_CLOSED = 397
    TARGET_ON_HOLD = 168
    TARGET_WIP = 13
    TARGET_RESOLVED = 7
    TARGET_CANCELLED = 2
    TARGET_AGED = 373
    TARGET_VENDOR = 167
    TARGET_UNASSIGNED = 515
    TARGET_ARF = 19
    TARGET_MISC = 29
    TARGET_LEADERSHIP = 6

    def _count(state: TicketState) -> int:
        return sum(1 for t in tickets if t.state == state)

    def _count_active_aged() -> int:
        return sum(1 for t in tickets if t.is_active and t.age_days > 180)

    def _count_vendor() -> int:
        return sum(1 for t in tickets if t.state == TicketState.OnHold and t.is_vendor_hold)

    def _count_unassigned() -> int:
        return sum(1 for t in tickets if t.is_active and t.assigned_tech is None)

    def _count_arf() -> int:
        return sum(1 for t in tickets if t.is_active and t.notification_count >= 3)

    def _count_misc() -> int:
        from src.data.models import TicketCategory
        return sum(
            1 for t in tickets
            if t.is_active and t.category in TicketCategory.misrouted_categories()
        )

    def _count_leadership() -> int:
        return sum(1 for t in tickets if t.is_leadership_flagged)

    rng = random.Random(99)

    # --- Fix aged 180+ ---
    while _count_active_aged() < TARGET_AGED:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.is_active and t.age_days <= 180 and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        new_age = rng.randint(181, 500)
        tickets[i] = tickets[i].model_copy(
            update={"age_days": new_age, "created_date": _REF_DATE - timedelta(days=new_age)}
        )

    while _count_active_aged() > TARGET_AGED:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.is_active and t.age_days > 180 and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        new_age = rng.randint(1, 180)
        tickets[i] = tickets[i].model_copy(
            update={"age_days": new_age, "created_date": _REF_DATE - timedelta(days=new_age)}
        )

    # --- Fix vendor hold ---
    while _count_vendor() < TARGET_VENDOR:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.state == TicketState.OnHold and not t.is_vendor_hold
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        tickets[i] = tickets[i].model_copy(update={"is_vendor_hold": True})

    while _count_vendor() > TARGET_VENDOR:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.state == TicketState.OnHold and t.is_vendor_hold and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        tickets[i] = tickets[i].model_copy(update={"is_vendor_hold": False})

    # --- Fix unassigned active ---
    while _count_unassigned() < TARGET_UNASSIGNED:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.is_active and t.assigned_tech is not None and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        tickets[i] = tickets[i].model_copy(update={"assigned_tech": None})

    while _count_unassigned() > TARGET_UNASSIGNED:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.is_active and t.assigned_tech is None and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        tickets[i] = tickets[i].model_copy(update={"assigned_tech": "N. Cabrera"})

    # --- Fix auto-resolve fail ---
    while _count_arf() < TARGET_ARF:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.is_active and t.notification_count < 3 and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        tickets[i] = tickets[i].model_copy(update={"notification_count": 3})

    while _count_arf() > TARGET_ARF:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.is_active and t.notification_count >= 3 and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        tickets[i] = tickets[i].model_copy(update={"notification_count": 0})

    # --- Fix misclassified ---
    while _count_misc() < TARGET_MISC:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.is_active
            and t.category == TicketCategory.Hardware
            and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        tickets[i] = tickets[i].model_copy(update={"category": TicketCategory.RemoteAccess})

    while _count_misc() > TARGET_MISC:
        candidates = [
            i for i, t in enumerate(tickets)
            if t.is_active
            and t.category in TicketCategory.misrouted_categories()
            and not t.is_leadership_flagged
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        tickets[i] = tickets[i].model_copy(update={"category": TicketCategory.Hardware})


# ---------------------------------------------------------------------------
# ServiceNow CSV parsing helpers
# ---------------------------------------------------------------------------

_SN_DATETIME_FORMATS: list[str] = [
    "%Y-%m-%d %H:%M:%S",   # 2025-08-14 09:32:00  (standard SN export)
    "%m/%d/%Y %H:%M:%S",   # 08/14/2025 09:32:00
    "%m-%d-%Y %H:%M:%S",   # 08-14-2025 09:32:00  (this export's format)
    "%Y-%m-%dT%H:%M:%S",   # 2025-08-14T09:32:00  (ISO 8601)
    "%Y-%m-%d",            # 2025-08-14
    "%m/%d/%Y",            # 08/14/2025
    "%m-%d-%Y",            # 08-14-2025
]

# ServiceNow state display labels and numeric codes → TicketState
_SN_STATE_MAP: dict[str, TicketState] = {
    "assigned": TicketState.Assigned,
    "closed": TicketState.Closed,
    "on hold": TicketState.OnHold,
    "work in progress": TicketState.WorkInProgress,
    "resolved": TicketState.Resolved,
    "cancelled": TicketState.Cancelled,
    # numeric codes used in some SN exports
    "1": TicketState.Assigned,       # New
    "2": TicketState.WorkInProgress,  # In Progress
    "3": TicketState.OnHold,
    "4": TicketState.Resolved,
    "5": TicketState.Assigned,       # Pending Approval → treat as Assigned
    "6": TicketState.Closed,
    "7": TicketState.Cancelled,
}

# ServiceNow category labels → TicketCategory
_SN_CATEGORY_MAP: dict[str, TicketCategory] = {
    "hardware": TicketCategory.Hardware,
    "hardware / component": TicketCategory.Hardware,
    "hardware/component": TicketCategory.Hardware,
    "remote access": TicketCategory.RemoteAccess,
    "software": TicketCategory.SoftwareApp,
    "software/app": TicketCategory.SoftwareApp,
    "software / app": TicketCategory.SoftwareApp,
    "application": TicketCategory.SoftwareApp,
    "kiosk": TicketCategory.Kiosk,
    "access/security": TicketCategory.AccessSecurity,
    "access / security": TicketCategory.AccessSecurity,
    "security": TicketCategory.AccessSecurity,
    "laptop": TicketCategory.Laptop,
}

# hold_reason substrings that indicate an NCT / vendor hold
_VENDOR_HOLD_KEYWORDS: frozenset[str] = frozenset(
    {"nct", "vendor", "awaiting vendor", "3rd party", "third party", "parts", "awaiting part"}
)

# u_escalation_status values that mean "not escalated"
_NON_ESCALATED: frozenset[str] = frozenset({"", "normal", "none", "false", "no", "0"})


def _parse_sn_date(raw: str) -> date | None:
    """Parse a ServiceNow datetime or date string into a Python date.

    Args:
        raw: Raw string from the CSV cell, e.g. "2024-08-15 09:23:45".

    Returns:
        A date object, or None if the string is empty or unparseable.
    """
    raw = raw.strip()
    if not raw:
        return None
    for fmt in _SN_DATETIME_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    # Last-ditch: try just the first 10 characters as ISO date
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _resolve_state(raw: str) -> TicketState:
    """Map a raw ServiceNow state string to TicketState.

    Args:
        raw: State cell value from the CSV (label or numeric code).

    Returns:
        Matched TicketState.

    Raises:
        ValueError: When the value cannot be mapped to any known state.
    """
    key = raw.strip().lower()
    if key in _SN_STATE_MAP:
        return _SN_STATE_MAP[key]
    raise ValueError(
        f"Unrecognised ServiceNow state: {raw!r}. "
        f"Expected one of: {sorted(_SN_STATE_MAP.keys())}"
    )


def _resolve_category(raw: str) -> TicketCategory:
    """Map a raw ServiceNow category string to TicketCategory.

    Unknown categories fall back to TicketCategory.Other rather than raising,
    because ServiceNow categories vary between organisations.

    Args:
        raw: Category cell value from the CSV.

    Returns:
        Matched TicketCategory, or TicketCategory.Other for unmapped values.
    """
    return _SN_CATEGORY_MAP.get(raw.strip().lower(), TicketCategory.Other)


def _compute_age_days(
    row: dict[str, str],
    state: TicketState,
    opened_date: date | None,
    ref: date,
) -> int:
    """Derive ticket age in days from ServiceNow row data.

    For terminal states (Closed / Resolved / Cancelled) with a valid closed_at
    date, age is opened_at → closed_at.  For active tickets it is opened_at →
    ref (today / reference date).  Falls back to calendar_stc (seconds / 86400)
    when opened_at is unavailable.

    Args:
        row: Raw CSV row dict.
        state: Already-resolved TicketState for this row.
        opened_date: Parsed opened_at date, or None.
        ref: Reference date for computing age of open tickets.

    Returns:
        Non-negative integer days.
    """
    terminal = state in {TicketState.Closed, TicketState.Resolved, TicketState.Cancelled}

    if opened_date is not None:
        if terminal:
            closed_date = _parse_sn_date(row.get("closed_at", "") or row.get("resolved_at", ""))
            end = closed_date if closed_date and closed_date >= opened_date else ref
        else:
            end = ref
        return max(0, (end - opened_date).days)

    # Fallback: calendar_stc is stored in seconds in ServiceNow
    stc_raw = row.get("calendar_stc", "").strip()
    if stc_raw:
        try:
            return max(0, int(float(stc_raw) / 86400))
        except ValueError:
            pass
    return 0


def _detect_delimiter(csv_path: Path) -> str:
    """Sniff the CSV delimiter by comparing tab and comma counts in the header.

    ServiceNow exports are often tab-delimited when downloaded as 'Excel' format.

    Args:
        csv_path: Path to the file.

    Returns:
        "\\t" or "," depending on which appears more in the first line.
    """
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        first_line = f.readline()
    return "\t" if first_line.count("\t") > first_line.count(",") else ","


def load_csv(path: str) -> list[Ticket]:
    """Load and validate tickets from a ServiceNow CSV (or TSV) export.

    Column mapping is performed against the real ServiceNow export schema.
    The file may be comma- or tab-delimited — the delimiter is auto-detected.

    Args:
        path: Absolute path to the ServiceNow incident export file.

    Returns:
        List of validated Ticket objects.

    Raises:
        FileNotFoundError: When the file does not exist.
        ValueError: When a row contains an unrecognised state value.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    delimiter = _detect_delimiter(csv_path)
    today = date.today()
    tickets: list[Ticket] = []

    # Auto-detect encoding: try UTF-8 (with BOM) first, then Windows-1252
    # (Excel exports), then fall back to latin-1 which accepts every byte.
    encoding = "latin-1"
    for enc in ("utf-8-sig", "cp1252"):
        try:
            csv_path.read_text(encoding=enc)
            encoding = enc
            break
        except (UnicodeDecodeError, LookupError):
            continue

    with csv_path.open(newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        # Strip any BOM / whitespace from header names
        if reader.fieldnames:
            reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            state = _resolve_state(row.get("state", ""))
            opened_date = _parse_sn_date(row.get("opened_at", ""))
            age_days = _compute_age_days(row, state, opened_date, today)
            category = _resolve_category(row.get("category", ""))

            assigned_raw = row.get("assigned_to", "").strip()
            assigned_tech: str | None = assigned_raw if assigned_raw else None

            notif_raw = row.get("u_notification_counter", "").strip()
            notification_count = int(notif_raw) if notif_raw and notif_raw.isdigit() else 0

            hold_reason_lower = row.get("hold_reason", "").strip().lower()
            is_vendor_hold = state == TicketState.OnHold and any(
                kw in hold_reason_lower for kw in _VENDOR_HOLD_KEYWORDS
            )

            escalation = row.get("u_escalation_status", "").strip().lower()
            is_leadership_flagged = escalation not in _NON_ESCALATED

            short_desc = row.get("short_description", "").strip() or None

            ticket = Ticket(
                number=row["number"].strip(),
                state=state,
                age_days=age_days,
                category=category,
                assigned_tech=assigned_tech,
                location=row.get("location", "Unknown").strip() or "Unknown",
                created_date=opened_date if opened_date else today,
                notification_count=notification_count,
                is_vendor_hold=is_vendor_hold,
                is_leadership_flagged=is_leadership_flagged,
                short_description=short_desc,
            )
            tickets.append(ticket)

    log.info("csv_loaded", path=path, count=len(tickets), delimiter=repr(delimiter))
    return tickets


def get_tickets(settings: "Settings") -> list[Ticket]:
    """Return the ticket list from CSV if DATA_CSV_PATH is set, else mock data.

    Args:
        settings: Application settings (pydantic-settings instance or compatible mock).

    Returns:
        List of Ticket objects ready for transform functions.
    """
    if settings.data_csv_path:
        log.info("loading_csv", path=settings.data_csv_path)
        return load_csv(settings.data_csv_path)

    log.info("loading_mock_data")
    return load_mock_data()
