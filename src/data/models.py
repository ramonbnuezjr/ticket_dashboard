"""Pydantic models for the ticket dashboard domain."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class TicketState(str, Enum):
    """Possible states for a ServiceNow incident ticket."""

    Assigned = "Assigned"
    Closed = "Closed"
    OnHold = "OnHold"
    WorkInProgress = "WorkInProgress"
    Resolved = "Resolved"
    Cancelled = "Cancelled"

    @classmethod
    def active_states(cls) -> frozenset["TicketState"]:
        """States that count as active/open (not terminal)."""
        return frozenset(
            {cls.Assigned, cls.OnHold, cls.WorkInProgress}
        )


class TicketCategory(str, Enum):
    """Incident category as assigned in ServiceNow."""

    Hardware = "Hardware"
    RemoteAccess = "Remote Access"
    SoftwareApp = "Software/App"
    Kiosk = "Kiosk"
    AccessSecurity = "Access/Security"
    Laptop = "Laptop"
    Other = "Other"

    @classmethod
    def misrouted_categories(cls) -> frozenset["TicketCategory"]:
        """Categories that should not appear in the HW Repair queue."""
        return frozenset(
            {cls.RemoteAccess, cls.SoftwareApp, cls.Kiosk, cls.AccessSecurity, cls.Laptop}
        )


class Ticket(BaseModel):
    """A single ServiceNow incident record."""

    number: str = Field(..., min_length=1)
    state: TicketState
    age_days: int = Field(..., ge=0)
    category: TicketCategory
    assigned_tech: Optional[str] = None
    location: str = Field(..., min_length=1)
    created_date: date
    notification_count: int = Field(default=0, ge=0)
    is_vendor_hold: bool = False
    is_leadership_flagged: bool = False
    # Populated from ServiceNow short_description when loading a real CSV export;
    # empty string for mock data.  Used as the primary issue summary in flagged
    # ticket cards when present.
    short_description: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """True when the ticket state is not a terminal state."""
        return self.state in TicketState.active_states()


class KpiData(BaseModel):
    """Pre-computed KPI values for the header strip."""

    total: int = Field(..., ge=0)
    active_open: int = Field(..., ge=0)
    active_pct: float = Field(..., ge=0.0, le=100.0)
    vendor_queue: int = Field(..., ge=0)
    unassigned: int = Field(..., ge=0)
    misclassified: int = Field(..., ge=0)
    auto_resolve_fail: int = Field(..., ge=0)

    @model_validator(mode="after")
    def _active_open_le_total(self) -> "KpiData":
        if self.active_open > self.total:
            raise ValueError("active_open cannot exceed total")
        return self


class AlertSeverity(str, Enum):
    """Severity levels for operational pattern alerts."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    MONITOR = "MONITOR"
    IMMEDIATE = "IMMEDIATE"


class PatternAlert(BaseModel):
    """A single operational pattern alert card."""

    severity: AlertSeverity
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    count: int = Field(..., ge=0)


class FlaggedTicket(BaseModel):
    """A ticket surfaced in the immediate-action table."""

    number: str = Field(..., min_length=1)
    state: TicketState
    age_days: int = Field(..., ge=0)
    pattern: str = Field(..., min_length=1)
    issue_summary: str = Field(..., min_length=1)
    owner: Optional[str] = None
