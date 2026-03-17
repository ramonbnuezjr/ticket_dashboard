"""Age distribution horizontal bar chart — active tickets only."""

from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html

from src.components import (
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    PLOTLY_TEMPLATE,
)

# Red → orange → green gradient (oldest to newest — screenshot order reversed)
_AGE_COLORS: list[str] = [
    "#e74c3c",  # 365+d
    "#e67e22",  # 181-365d
    "#f59e0b",  # 91-180d
    "#84cc16",  # 31-90d
    "#22c55e",  # 0-30d
]

_BUCKET_ORDER = ["0-30d", "31-90d", "91-180d", "181-365d", "365+d"]


def age_chart(age_distribution: dict[str, int]) -> html.Div:
    """Render a horizontal bar chart of active ticket age distribution.

    Args:
        age_distribution: Ordered dict from compute_age_distribution().

    Returns:
        A Dash html.Div with id="age-chart".
    """
    # Display bottom→top so oldest is at the bottom (matching the screenshot)
    buckets = _BUCKET_ORDER
    values = [age_distribution.get(b, 0) for b in buckets]
    colors = _AGE_COLORS

    fig = go.Figure(
        go.Bar(
            x=values,
            y=buckets,
            orientation="h",
            marker={"color": colors},
            hovertemplate="%{y}: %{x:,} tickets<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        margin={"l": 70, "r": 20, "t": 40, "b": 20},
        title={
            "text": "Age distribution — active tickets only",
            "font": {"size": 13, "color": COLOR_TEXT_PRIMARY},
            "x": 0.0,
            "xanchor": "left",
        },
        xaxis={
            "gridcolor": "#374151",
            "tickfont": {"size": 10, "color": COLOR_TEXT_MUTED},
        },
        yaxis={
            "tickfont": {"size": 11, "color": COLOR_TEXT_MUTED},
            "showgrid": False,
        },
        bargap=0.3,
    )

    return html.Div(
        id="age-chart",
        style={"backgroundColor": COLOR_SURFACE, "borderRadius": "8px"},
        children=[
            dcc.Graph(
                id="age-distribution-graph",
                figure=fig,
                config={"displayModeBar": False},
                style={"height": "280px"},
            )
        ],
    )
