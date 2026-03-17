"""Location heat map component — treemap with 3 interchangeable metrics.

The toggle buttons (% active open / avg age / on hold count) are wired via a
Dash callback registered in app.py.  This module provides:
  - heatmap_section(): the full section layout (title + toggle + graph)
  - build_treemap_figure(): a pure function for building the figure given a metric name,
    so the callback in app.py can call it without importing Dash internals.
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
from dash import dcc, html

from src.components import (
    COLOR_BG,
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    PLOTLY_TEMPLATE,
)

# Metric → (display label, colour scale, format string)
_METRIC_CONFIG: dict[str, tuple[str, str, str]] = {
    "pct_active": ("% active open", "RdYlGn_r", "{:.0f}%"),
    "avg_age": ("avg age (days)", "RdYlGn_r", "{:.0f}d"),
    "on_hold_count": ("on hold count", "Blues", "{:.0f}"),
}

_TOGGLE_IDS = {
    "pct_active": "toggle-pct-active",
    "avg_age": "toggle-avg-age",
    "on_hold_count": "toggle-on-hold",
}

_BUTTON_BASE_STYLE: dict[str, str] = {
    "padding": "8px 16px",
    "borderRadius": "4px",
    "border": "1px solid #374151",
    "cursor": "pointer",
    "fontSize": "12px",
    "fontWeight": "600",
    "transition": "all 0.15s",
}

_ACTIVE_STYLE: dict[str, str] = {
    **_BUTTON_BASE_STYLE,
    "backgroundColor": "#374151",
    "color": "#f9fafb",
}

_INACTIVE_STYLE: dict[str, str] = {
    **_BUTTON_BASE_STYLE,
    "backgroundColor": "transparent",
    "color": "#9ca3af",
}


def build_treemap_figure(
    locations: list[dict[str, Any]],
    metric: str = "pct_active",
) -> go.Figure:
    """Build a Plotly treemap figure for the given metric.

    Args:
        locations: List of location dicts from compute_location_heatmap().
        metric: One of "pct_active", "avg_age", "on_hold_count".

    Returns:
        A Plotly Figure ready for use in a dcc.Graph.
    """
    if not locations:
        return go.Figure(layout={"template": PLOTLY_TEMPLATE, "paper_bgcolor": COLOR_SURFACE})

    _, colorscale, fmt = _METRIC_CONFIG.get(metric, _METRIC_CONFIG["pct_active"])

    labels = [loc["location"] for loc in locations]
    parents = ["" for _ in locations]
    values = [loc["total"] for loc in locations]
    metric_values = [loc[metric] for loc in locations]
    custom_text = [
        f"{loc['location']}<br>{fmt.format(loc[metric])}<br>{loc['total']} tickets"
        for loc in locations
    ]

    fig = go.Figure(
        go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            customdata=custom_text,
            hovertemplate="%{customdata}<extra></extra>",
            texttemplate="%{label}<br>" + "<br>".join(
                [fmt.format(v) for v in metric_values[:1]]  # placeholder; real text set below
            ),
            marker={
                "colors": metric_values,
                "colorscale": colorscale,
                "showscale": True,
                "colorbar": {
                    "thickness": 12,
                    "len": 0.8,
                    "tickfont": {"size": 10, "color": COLOR_TEXT_MUTED},
                },
            },
            textinfo="label+text",
            text=[fmt.format(v) for v in metric_values],
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
    )
    return fig


def heatmap_section(
    locations: list[dict[str, Any]],
    active_metric: str = "pct_active",
) -> html.Div:
    """Render the full heat map section: title, metric toggles, treemap.

    Args:
        locations: List of location dicts from compute_location_heatmap().
        active_metric: Initially active metric key.

    Returns:
        A Dash html.Div with id="heatmap-section".
    """
    toggles = html.Div(
        id="heatmap-toggles",
        style={"display": "flex", "gap": "8px", "marginBottom": "12px"},
        children=[
            html.Button(
                "% active open",
                id=_TOGGLE_IDS["pct_active"],
                style=_ACTIVE_STYLE if active_metric == "pct_active" else _INACTIVE_STYLE,
                n_clicks=0,
            ),
            html.Button(
                "avg age (days)",
                id=_TOGGLE_IDS["avg_age"],
                style=_ACTIVE_STYLE if active_metric == "avg_age" else _INACTIVE_STYLE,
                n_clicks=0,
            ),
            html.Button(
                "on hold count",
                id=_TOGGLE_IDS["on_hold_count"],
                style=_ACTIVE_STYLE if active_metric == "on_hold_count" else _INACTIVE_STYLE,
                n_clicks=0,
            ),
        ],
    )

    return html.Div(
        id="heatmap-section",
        style={"backgroundColor": COLOR_BG},
        children=[
            html.Div(
                "Hardware incident heat map — by building",
                style={
                    "fontSize": "14px",
                    "fontWeight": "700",
                    "color": COLOR_TEXT_PRIMARY,
                    "marginBottom": "4px",
                },
            ),
            html.Div(
                "Block size = total tickets · Color = selected metric · "
                f"{len(locations)} buildings with 5+ incidents",
                style={"fontSize": "11px", "color": COLOR_TEXT_MUTED, "marginBottom": "12px"},
            ),
            toggles,
            dcc.Store(id="heatmap-location-store", data=locations),
            dcc.Graph(
                id="heatmap-treemap",
                figure=build_treemap_figure(locations, active_metric),
                config={"displayModeBar": False},
                style={"height": "480px"},
            ),
        ],
    )
