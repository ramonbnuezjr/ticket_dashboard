"""KPI strip component — six headline metric cards across the top of the dashboard."""

from __future__ import annotations

from dash import html

from src.components import (
    COLOR_BG,
    COLOR_CRITICAL,
    COLOR_GOOD,
    COLOR_MONITOR,
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
)
from src.data.models import KpiData

_CARD_STYLE: dict[str, str] = {
    "backgroundColor": COLOR_SURFACE,
    "borderRadius": "8px",
    "padding": "16px 20px",
    "flex": "1",
    "minWidth": "0",
    "cursor": "pointer",
    "transition": "border 0.15s, box-shadow 0.15s",
    "border": "1px solid transparent",
    "boxSizing": "border-box",
}

_LABEL_STYLE: dict[str, str] = {
    "fontSize": "11px",
    "fontWeight": "700",
    "letterSpacing": "0.08em",
    "color": COLOR_TEXT_MUTED,
    "marginBottom": "6px",
    "textTransform": "uppercase",
}

_VALUE_STYLE_BASE: dict[str, str] = {
    "fontSize": "32px",
    "fontWeight": "700",
    "lineHeight": "1",
    "marginBottom": "4px",
}

_SUB_STYLE: dict[str, str] = {
    "fontSize": "12px",
    "color": COLOR_TEXT_MUTED,
}

_HINT_STYLE: dict[str, str] = {
    "fontSize": "10px",
    "color": "#4b5563",
    "marginTop": "6px",
    "letterSpacing": "0.04em",
}


def _card(
    label: str,
    value: str,
    sub: str,
    value_color: str = COLOR_TEXT_PRIMARY,
    card_id: str | None = None,
) -> html.Div:
    kwargs: dict = {
        "style": _CARD_STYLE,
        "children": [
            html.Div(label, style=_LABEL_STYLE),
            html.Div(value, style={**_VALUE_STYLE_BASE, "color": value_color}),
            html.Div(sub, style=_SUB_STYLE),
            html.Div("click to view ↓", style=_HINT_STYLE),
        ],
    }
    if card_id:
        kwargs["id"] = card_id
        kwargs["n_clicks"] = 0
    return html.Div(**kwargs)


def kpi_strip(kpi: KpiData) -> html.Div:
    """Render the six-card KPI header strip.

    Each card is clickable — clicking fires a Dash callback that opens a
    drill-down panel below the strip filtered to that KPI's ticket subset.

    Args:
        kpi: Pre-computed KpiData from compute_kpis().

    Returns:
        A Dash html.Div with id="kpi-strip" containing 6 metric cards.
    """
    cards = [
        _card(
            label="Total",
            value=f"{kpi.total:,}",
            sub="Aug 2023 – Mar 2026",
            value_color=COLOR_TEXT_PRIMARY,
            card_id="kpi-card-total",
        ),
        _card(
            label="Active Open",
            value=f"{kpi.active_open:,}",
            sub=f"{kpi.active_pct}% of total",
            value_color=COLOR_WARNING,
            card_id="kpi-card-active_open",
        ),
        _card(
            label="Vendor Queue",
            value=f"{kpi.vendor_queue:,}",
            sub="On Hold · NCT",
            value_color=COLOR_MONITOR,
            card_id="kpi-card-vendor_queue",
        ),
        _card(
            label="Unassigned",
            value=f"{kpi.unassigned:,}",
            sub="Active · no tech",
            value_color=COLOR_CRITICAL,
            card_id="kpi-card-unassigned",
        ),
        _card(
            label="Misclassified",
            value=f"{kpi.misclassified:,}",
            sub="Wrong category",
            value_color=COLOR_WARNING,
            card_id="kpi-card-misclassified",
        ),
        _card(
            label="Auto-Resolve Fail",
            value=f"{kpi.auto_resolve_fail:,}",
            sub="3+ notifs · open",
            value_color=COLOR_CRITICAL,
            card_id="kpi-card-auto_resolve_fail",
        ),
    ]

    return html.Div(
        id="kpi-strip",
        style={
            "display": "flex",
            "gap": "12px",
            "backgroundColor": COLOR_BG,
        },
        children=cards,
    )
