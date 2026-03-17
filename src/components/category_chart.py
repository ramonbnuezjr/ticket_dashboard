"""Category breakdown horizontal bar chart — active tickets, amber for misrouted."""

from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html

from src.components import (
    COLOR_MONITOR,
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    PLOTLY_TEMPLATE,
)
from src.data.models import TicketCategory

_MISROUTED_VALUES = {c.value for c in TicketCategory.misrouted_categories()}


def category_chart(category_breakdown: dict[str, int]) -> html.Div:
    """Render a horizontal bar chart of active ticket category breakdown.

    Non-hardware categories are rendered in amber to flag misrouting.

    Args:
        category_breakdown: Ordered dict from compute_category_breakdown().

    Returns:
        A Dash html.Div with id="category-chart".
    """
    categories = list(category_breakdown.keys())
    values = list(category_breakdown.values())
    colors = [COLOR_WARNING if cat in _MISROUTED_VALUES else COLOR_MONITOR for cat in categories]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=categories,
            orientation="h",
            marker={"color": colors},
            hovertemplate="%{y}: %{x:,} tickets<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        margin={"l": 110, "r": 20, "t": 50, "b": 20},
        title={
            "text": "Category breakdown — active tickets",
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
            "autorange": "reversed",
        },
        bargap=0.35,
        annotations=[
            {
                "x": 0.0,
                "y": -0.18,
                "xref": "paper",
                "yref": "paper",
                "text": "Non-hardware categories flagged in amber/red — routing issues",
                "font": {"size": 10, "color": COLOR_TEXT_MUTED},
                "showarrow": False,
                "align": "left",
            }
        ],
    )

    return html.Div(
        id="category-chart",
        style={"backgroundColor": COLOR_SURFACE, "borderRadius": "8px"},
        children=[
            dcc.Graph(
                id="category-breakdown-graph",
                figure=fig,
                config={"displayModeBar": False},
                style={"height": "280px"},
            )
        ],
    )
