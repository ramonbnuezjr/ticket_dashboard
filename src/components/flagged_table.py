"""Flagged tickets DataTable — immediate action required."""

from __future__ import annotations

from dash import dash_table, html

from src.components import (
    COLOR_BG,
    COLOR_BORDER,
    COLOR_CRITICAL,
    COLOR_MONITOR,
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
)
from src.data.models import FlaggedTicket, TicketState

_STATE_COLORS: dict[str, str] = {
    TicketState.Assigned.value: COLOR_WARNING,
    TicketState.OnHold.value: COLOR_MONITOR,
    TicketState.WorkInProgress.value: COLOR_CRITICAL,
    TicketState.Resolved.value: "#22c55e",
    TicketState.Closed.value: "#6b7280",
    TicketState.Cancelled.value: "#6b7280",
}

_COLUMNS = [
    {"id": "ticket", "name": "Ticket"},
    {"id": "state", "name": "State"},
    {"id": "age", "name": "Age"},
    {"id": "pattern", "name": "Pattern"},
    {"id": "summary", "name": "Issue summary"},
    {"id": "owner", "name": "Owner"},
]


def _state_badge(state_value: str) -> dict[str, object]:
    color = _STATE_COLORS.get(state_value, "#6b7280")
    return {"if": {"filter_query": f'{{state}} = "{state_value}"', "column_id": "state"}, "color": color, "fontWeight": "700"}


def flagged_table(flagged: list[FlaggedTicket]) -> html.Div:
    """Render the flagged tickets table with state-colored rows.

    Args:
        flagged: List of FlaggedTicket objects from compute_flagged_tickets().

    Returns:
        A Dash html.Div with id="flagged-table-section".
    """
    rows = [
        {
            "ticket": ft.number,
            "state": ft.state.value,
            "age": f"{ft.age_days}d",
            "pattern": ft.pattern,
            "summary": ft.issue_summary,
            "owner": ft.owner or "Unassigned",
        }
        for ft in flagged
    ]

    style_conditions = [_state_badge(s.value) for s in TicketState]

    table = dash_table.DataTable(
        id="flagged-datatable",
        columns=_COLUMNS,
        data=rows,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": COLOR_SURFACE,
            "color": COLOR_TEXT_MUTED,
            "fontWeight": "700",
            "fontSize": "11px",
            "textTransform": "uppercase",
            "letterSpacing": "0.06em",
            "border": f"1px solid {COLOR_BORDER}",
        },
        style_cell={
            "backgroundColor": COLOR_BG,
            "color": COLOR_TEXT_PRIMARY,
            "fontSize": "12px",
            "padding": "10px 12px",
            "border": f"1px solid {COLOR_BORDER}",
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_data_conditional=style_conditions,
        page_size=20,
        sort_action="native",
    )

    return html.Div(
        id="flagged-table-section",
        style={"backgroundColor": COLOR_BG},
        children=[
            html.Div(
                "Flagged tickets — immediate action required",
                style={
                    "fontSize": "14px",
                    "fontWeight": "700",
                    "color": COLOR_TEXT_PRIMARY,
                    "marginBottom": "12px",
                },
            ),
            table,
        ],
    )
