"""Pattern alert cards — six severity-coded operational pattern notifications."""

from __future__ import annotations

from dash import html

from src.components import (
    COLOR_BG,
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    SEVERITY_COLORS,
)
from src.data.models import PatternAlert

_CARD_STYLE: dict[str, str] = {
    "backgroundColor": COLOR_SURFACE,
    "borderRadius": "8px",
    "padding": "16px",
    "flex": "1",
    "minWidth": "0",
    "borderLeft": "4px solid",
}

_SEVERITY_LABEL_STYLE_BASE: dict[str, str] = {
    "fontSize": "10px",
    "fontWeight": "800",
    "letterSpacing": "0.1em",
    "marginBottom": "6px",
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "6px",
}

_COUNT_BADGE_STYLE_BASE: dict[str, str] = {
    "fontSize": "11px",
    "fontWeight": "700",
    "borderRadius": "4px",
    "padding": "2px 7px",
    "color": "#111827",
}

_TITLE_STYLE: dict[str, str] = {
    "fontSize": "13px",
    "fontWeight": "700",
    "color": COLOR_TEXT_PRIMARY,
    "marginBottom": "6px",
    "lineHeight": "1.3",
}

_DESC_STYLE: dict[str, str] = {
    "fontSize": "12px",
    "color": COLOR_TEXT_MUTED,
    "lineHeight": "1.5",
}


def _alert_card(alert: PatternAlert) -> html.Div:
    color = SEVERITY_COLORS.get(alert.severity.value, "#6b7280")
    return html.Div(
        style={
            **_CARD_STYLE,
            "borderLeftColor": color,
        },
        children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "8px"},
                children=[
                    html.Span(
                        alert.severity.value,
                        style={**_SEVERITY_LABEL_STYLE_BASE, "color": color},
                    ),
                    html.Span(
                        str(alert.count),
                        style={**_COUNT_BADGE_STYLE_BASE, "backgroundColor": color},
                    ),
                ],
            ),
            html.Div(alert.title, style=_TITLE_STYLE),
            html.Div(alert.description, style=_DESC_STYLE),
        ],
    )


def pattern_alerts(alerts: list[PatternAlert]) -> html.Div:
    """Render a 2×3 grid of severity-coded pattern alert cards.

    Args:
        alerts: Exactly six PatternAlert objects from compute_pattern_alerts().

    Returns:
        A Dash html.Div with id="pattern-alerts".
    """
    mid = len(alerts) // 2
    row1 = alerts[:mid]
    row2 = alerts[mid:]

    def _row(items: list[PatternAlert]) -> html.Div:
        return html.Div(
            style={"display": "flex", "gap": "12px"},
            children=[_alert_card(a) for a in items],
        )

    return html.Div(
        id="pattern-alerts",
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "12px",
            "backgroundColor": COLOR_BG,
        },
        children=[
            html.Div(
                "Operational patterns flagged",
                style={
                    "fontSize": "14px",
                    "fontWeight": "700",
                    "color": COLOR_TEXT_PRIMARY,
                    "marginBottom": "4px",
                },
            ),
            _row(row1),
            _row(row2),
        ],
    )
