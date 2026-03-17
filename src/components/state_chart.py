"""State donut chart + monthly incident volume bar chart, rendered side by side."""

from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html

from src.components import (
    COLOR_BG,
    COLOR_GOOD,
    COLOR_MONITOR,
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    PLOTLY_TEMPLATE,
)

# State value → display label mapping
_STATE_LABELS: dict[str, str] = {
    "Assigned": "Assigned",
    "Closed": "Closed",
    "OnHold": "On Hold",
    "WorkInProgress": "Work in Progress",
    "Resolved": "Resolved",
    "Cancelled": "Cancelled",
}

_STATE_COLORS: list[str] = [
    "#3b82f6",   # Assigned — blue
    "#6b7280",   # Closed — grey
    "#f59e0b",   # On Hold — amber
    "#94a3b8",   # WIP — slate
    COLOR_GOOD,  # Resolved — green
    "#374151",   # Cancelled — dark grey
]


def _donut_figure(state_breakdown: dict[str, int]) -> go.Figure:
    labels = [_STATE_LABELS.get(k, k) for k in state_breakdown]
    values = list(state_breakdown.values())
    total = sum(values)

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker={"colors": _STATE_COLORS[: len(labels)]},
            textinfo="none",
            hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        title={
            "text": "Ticket state",
            "font": {"size": 13, "color": COLOR_TEXT_PRIMARY},
            "x": 0.0,
            "xanchor": "left",
        },
        showlegend=True,
        legend={
            "font": {"size": 11, "color": COLOR_TEXT_MUTED},
            "bgcolor": "rgba(0,0,0,0)",
            "orientation": "v",
        },
        annotations=[
            {
                "text": f"<b>{total:,}</b>",
                "x": 0.5,
                "y": 0.5,
                "font": {"size": 22, "color": COLOR_TEXT_PRIMARY},
                "showarrow": False,
            }
        ],
    )
    return fig


def _monthly_figure(monthly_volume: dict[str, int]) -> go.Figure:
    months = list(monthly_volume.keys())
    counts = list(monthly_volume.values())

    fig = go.Figure(
        go.Bar(
            x=months,
            y=counts,
            marker_color="#3b82f6",
            hovertemplate="%{x}: %{y} incidents<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        margin={"l": 40, "r": 10, "t": 40, "b": 60},
        title={
            "text": "Monthly incident volume — Mar 2025 through Feb 2026",
            "font": {"size": 13, "color": COLOR_TEXT_PRIMARY},
            "x": 0.0,
            "xanchor": "left",
        },
        xaxis={
            "tickangle": -45,
            "tickfont": {"size": 10, "color": COLOR_TEXT_MUTED},
            "showgrid": False,
        },
        yaxis={
            "gridcolor": "#374151",
            "tickfont": {"size": 10, "color": COLOR_TEXT_MUTED},
        },
        bargap=0.3,
    )
    return fig


def state_chart(
    state_breakdown: dict[str, int],
    monthly_volume: dict[str, int],
) -> html.Div:
    """Render the donut chart and monthly volume bar chart side by side.

    Args:
        state_breakdown: Mapping of state name → ticket count.
        monthly_volume: Ordered mapping of "YYYY-MM" → ticket count.

    Returns:
        A Dash html.Div with id="state-chart-row" containing two dcc.Graph elements.
    """
    return html.Div(
        id="state-chart-row",
        style={
            "display": "flex",
            "gap": "16px",
            "backgroundColor": COLOR_BG,
        },
        children=[
            html.Div(
                style={"flex": "1", "backgroundColor": COLOR_SURFACE, "borderRadius": "8px"},
                children=[
                    dcc.Graph(
                        id="state-donut",
                        figure=_donut_figure(state_breakdown),
                        config={"displayModeBar": False},
                        style={"height": "320px"},
                    )
                ],
            ),
            html.Div(
                style={"flex": "2", "backgroundColor": COLOR_SURFACE, "borderRadius": "8px"},
                children=[
                    dcc.Graph(
                        id="monthly-volume-bar",
                        figure=_monthly_figure(monthly_volume),
                        config={"displayModeBar": False},
                        style={"height": "320px"},
                    )
                ],
            ),
        ],
    )
