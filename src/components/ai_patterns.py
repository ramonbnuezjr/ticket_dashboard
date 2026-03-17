"""AI Pattern Discovery section component.

Renders the "AI-Discovered Patterns" section with a "Run Analysis" button,
a loading spinner, and a results container that gets populated via callback.
When no API key is configured the button is disabled and a setup notice is shown.
"""

from __future__ import annotations

from dash import dcc, html

from src.components import (
    COLOR_BG,
    COLOR_BORDER,
    COLOR_MONITOR,
    COLOR_SURFACE,
    COLOR_SURFACE_2,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    SEVERITY_COLORS,
)
from src.data.models import PatternAlert

# Reuse the same card style as pattern_alerts.py for visual consistency.
_CARD_STYLE: dict[str, str] = {
    "backgroundColor": COLOR_SURFACE,
    "borderRadius": "8px",
    "padding": "16px",
    "flex": "1",
    "minWidth": "200px",
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

_BTN_ACTIVE: dict[str, str] = {
    "backgroundColor": COLOR_MONITOR,
    "color": "#111827",
    "border": "none",
    "borderRadius": "6px",
    "padding": "9px 20px",
    "fontSize": "13px",
    "fontWeight": "700",
    "cursor": "pointer",
    "letterSpacing": "0.04em",
    "transition": "opacity 0.15s",
}

_BTN_DISABLED: dict[str, str] = {
    **_BTN_ACTIVE,
    "backgroundColor": COLOR_SURFACE_2,
    "color": COLOR_TEXT_MUTED,
    "cursor": "not-allowed",
    "opacity": "0.6",
}

_AI_BADGE_STYLE: dict[str, str] = {
    "fontSize": "10px",
    "fontWeight": "700",
    "color": COLOR_MONITOR,
    "backgroundColor": "#0c2340",
    "borderRadius": "4px",
    "padding": "2px 8px",
    "border": f"1px solid {COLOR_MONITOR}",
    "marginLeft": "10px",
    "letterSpacing": "0.06em",
}


def ai_pattern_card(alert: PatternAlert) -> html.Div:
    """Render a single AI-discovered pattern card (same visual style as hardcoded alerts)."""
    color = SEVERITY_COLORS.get(alert.severity.value, "#6b7280")
    return html.Div(
        style={**_CARD_STYLE, "borderLeftColor": color},
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "marginBottom": "8px",
                },
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


def ai_pattern_section(has_key: bool) -> html.Div:
    """Render the full AI Pattern Discovery section.

    Args:
        has_key: True when ANTHROPIC_API_KEY is set in the environment.
                 When False, the button is disabled and a setup notice is shown.

    Returns:
        A Dash html.Div with id="ai-pattern-section".
    """
    no_key_notice = (
        []
        if has_key
        else [
            html.Div(
                "Add ANTHROPIC_API_KEY to .env to enable AI analysis.",
                style={
                    "fontSize": "12px",
                    "color": COLOR_TEXT_MUTED,
                    "marginTop": "6px",
                    "fontStyle": "italic",
                },
            )
        ]
    )

    return html.Div(
        id="ai-pattern-section",
        style={"backgroundColor": COLOR_BG},
        children=[
            # Section header
            html.Div(
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "marginBottom": "14px",
                },
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center"},
                        children=[
                            html.Span(
                                "AI-discovered patterns",
                                style={
                                    "fontSize": "14px",
                                    "fontWeight": "700",
                                    "color": COLOR_TEXT_PRIMARY,
                                },
                            ),
                            html.Span("Claude Sonnet", style=_AI_BADGE_STYLE),
                        ],
                    ),
                    html.Div(
                        style={"display": "flex", "flexDirection": "column", "alignItems": "flex-end"},
                        children=[
                            html.Button(
                                "⚡ Run Analysis",
                                id="ai-run-btn",
                                n_clicks=0,
                                disabled=not has_key,
                                style=_BTN_ACTIVE if has_key else _BTN_DISABLED,
                            ),
                            *no_key_notice,
                        ],
                    ),
                ],
            ),

            # Divider
            html.Hr(
                style={
                    "border": "none",
                    "borderTop": f"1px solid {COLOR_BORDER}",
                    "margin": "0 0 14px 0",
                }
            ),

            # Loading wrapper around results
            dcc.Loading(
                id="ai-pattern-loading",
                type="circle",
                color=COLOR_MONITOR,
                children=[
                    html.Div(
                        id="ai-pattern-results",
                        children=[
                            html.Div(
                                "Click \"Run Analysis\" to scan ticket descriptions for new patterns.",
                                style={
                                    "fontSize": "13px",
                                    "color": COLOR_TEXT_MUTED,
                                    "fontStyle": "italic",
                                    "padding": "8px 0",
                                },
                            )
                        ],
                    )
                ],
            ),
        ],
    )


def render_ai_results(patterns: list[PatternAlert]) -> list[html.Div]:
    """Convert a list of PatternAlerts into rendered card rows.

    Called by the app callback to populate ai-pattern-results.
    """
    if not patterns:
        return [
            html.Div(
                "No new patterns found beyond the existing alerts.",
                style={
                    "fontSize": "13px",
                    "color": COLOR_TEXT_MUTED,
                    "fontStyle": "italic",
                    "padding": "8px 0",
                },
            )
        ]

    # Lay out cards in rows of 3 (matching existing pattern alerts layout).
    rows: list[html.Div] = []
    chunk_size = 3
    for i in range(0, len(patterns), chunk_size):
        chunk = patterns[i : i + chunk_size]
        rows.append(
            html.Div(
                style={"display": "flex", "gap": "12px", "marginBottom": "12px", "flexWrap": "wrap"},
                children=[ai_pattern_card(p) for p in chunk],
            )
        )
    return rows
