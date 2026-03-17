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


def _card(
    label: str,
    value: str,
    sub: str,
    value_color: str = COLOR_TEXT_PRIMARY,
) -> html.Div:
    return html.Div(
        style={**_CARD_STYLE},
        children=[
            html.Div(label, style=_LABEL_STYLE),
            html.Div(value, style={**_VALUE_STYLE_BASE, "color": value_color}),
            html.Div(sub, style=_SUB_STYLE),
        ],
    )


def kpi_strip(kpi: KpiData) -> html.Div:
    """Render the six-card KPI header strip.

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
        ),
        _card(
            label="Active Open",
            value=f"{kpi.active_open:,}",
            sub=f"{kpi.active_pct}% of total",
            value_color=COLOR_WARNING,
        ),
        _card(
            label="Vendor Queue",
            value=f"{kpi.vendor_queue:,}",
            sub="On Hold · NCT",
            value_color=COLOR_MONITOR,
        ),
        _card(
            label="Unassigned",
            value=f"{kpi.unassigned:,}",
            sub="Active · no tech",
            value_color=COLOR_CRITICAL,
        ),
        _card(
            label="Misclassified",
            value=f"{kpi.misclassified:,}",
            sub="Wrong category",
            value_color=COLOR_WARNING,
        ),
        _card(
            label="Auto-Resolve Fail",
            value=f"{kpi.auto_resolve_fail:,}",
            sub="3+ notifs · open",
            value_color=COLOR_CRITICAL,
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
