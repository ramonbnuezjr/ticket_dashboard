"""Dash application factory — assembles layout and registers callbacks."""

from __future__ import annotations

from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html

from src.components import COLOR_BG, COLOR_SURFACE, COLOR_TEXT_MUTED, COLOR_TEXT_PRIMARY
from src.components.age_chart import age_chart
from src.components.category_chart import category_chart
from src.components.flagged_table import flagged_table
from src.components.heatmap import build_treemap_figure, heatmap_section
from src.components.kpi_strip import kpi_strip
from src.components.pattern_alerts import pattern_alerts
from src.components.state_chart import state_chart
from src.data.models import Ticket
from src.data.transforms import (
    compute_age_distribution,
    compute_category_breakdown,
    compute_flagged_tickets,
    compute_kpis,
    compute_location_heatmap,
    compute_monthly_volume,
    compute_pattern_alerts,
    compute_state_breakdown,
)

_EXPORT_DATE = "Mar 16, 2026"

_HEADER_STYLE: dict[str, str] = {
    "backgroundColor": COLOR_SURFACE,
    "padding": "14px 24px",
    "borderBottom": f"1px solid #374151",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
}

_SECTION_STYLE: dict[str, str] = {
    "padding": "16px 24px",
    "backgroundColor": COLOR_BG,
}


def _header(total: int) -> html.Div:
    return html.Div(
        style=_HEADER_STYLE,
        children=[
            html.Div(
                children=[
                    html.Span(
                        "ITS Service Desk — Hardware Repair",
                        style={
                            "fontSize": "18px",
                            "fontWeight": "700",
                            "color": COLOR_TEXT_PRIMARY,
                            "marginRight": "12px",
                        },
                    ),
                    html.Span(
                        "ServiceNow",
                        style={
                            "fontSize": "11px",
                            "fontWeight": "700",
                            "color": "#22c55e",
                            "backgroundColor": "#052e16",
                            "borderRadius": "4px",
                            "padding": "3px 8px",
                            "border": "1px solid #166534",
                        },
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            html.Div(
                f"Assignment group: ITS Service Desk Hardware Repair · "
                f"{total:,} incidents · export date {_EXPORT_DATE}",
                style={"fontSize": "12px", "color": COLOR_TEXT_MUTED},
            ),
        ],
    )


def create_app(tickets: list[Ticket]) -> dash.Dash:
    """Build and return the configured Dash application.

    Args:
        tickets: Full ticket list from get_tickets().

    Returns:
        A Dash app instance ready for app.run().
    """
    # Pre-compute all data once at startup — components are purely presentational.
    kpi = compute_kpis(tickets)
    state_breakdown = compute_state_breakdown(tickets)
    monthly_volume = compute_monthly_volume(tickets)
    age_distribution = compute_age_distribution(tickets)
    cat_breakdown = compute_category_breakdown(tickets)
    alerts = compute_pattern_alerts(tickets)
    flagged = compute_flagged_tickets(tickets)
    locations = compute_location_heatmap(tickets)

    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        title="ITS Service Desk — Hardware Repair",
        suppress_callback_exceptions=True,
    )

    app.layout = html.Div(
        style={"backgroundColor": COLOR_BG, "minHeight": "100vh", "fontFamily": "'Inter', sans-serif"},
        children=[
            # 1. Header
            _header(kpi.total),

            # 2. KPI strip
            html.Div(
                style={**_SECTION_STYLE, "paddingBottom": "8px"},
                children=[kpi_strip(kpi)],
            ),

            # 3. State donut + monthly volume
            html.Div(
                style=_SECTION_STYLE,
                children=[state_chart(state_breakdown, monthly_volume)],
            ),

            # 4. Age distribution + category breakdown
            html.Div(
                style=_SECTION_STYLE,
                children=[
                    html.Div(
                        style={"display": "flex", "gap": "16px"},
                        children=[
                            html.Div(style={"flex": "1"}, children=[age_chart(age_distribution)]),
                            html.Div(style={"flex": "1"}, children=[category_chart(cat_breakdown)]),
                        ],
                    )
                ],
            ),

            # 5. Pattern alerts
            html.Div(style=_SECTION_STYLE, children=[pattern_alerts(alerts)]),

            # 6. Flagged tickets table
            html.Div(style=_SECTION_STYLE, children=[flagged_table(flagged)]),

            # 7. Heat map
            html.Div(style=_SECTION_STYLE, children=[heatmap_section(locations)]),
        ],
    )

    # -----------------------------------------------------------------------
    # Callback: heat map metric toggle
    # -----------------------------------------------------------------------

    @app.callback(
        Output("heatmap-treemap", "figure"),
        Output("toggle-pct-active", "style"),
        Output("toggle-avg-age", "style"),
        Output("toggle-on-hold", "style"),
        Input("toggle-pct-active", "n_clicks"),
        Input("toggle-avg-age", "n_clicks"),
        Input("toggle-on-hold", "n_clicks"),
        prevent_initial_call=True,
    )
    def _update_heatmap(
        n_pct: int,
        n_age: int,
        n_hold: int,
    ) -> tuple[Any, dict[str, str], dict[str, str], dict[str, str]]:
        """Switch the heat map metric based on which toggle button was last clicked."""
        from dash import ctx  # local import avoids circular at module load

        _active: dict[str, str] = {
            "padding": "8px 16px",
            "borderRadius": "4px",
            "border": "1px solid #374151",
            "cursor": "pointer",
            "fontSize": "12px",
            "fontWeight": "600",
            "backgroundColor": "#374151",
            "color": "#f9fafb",
            "transition": "all 0.15s",
        }
        _inactive: dict[str, str] = {
            "padding": "8px 16px",
            "borderRadius": "4px",
            "border": "1px solid #374151",
            "cursor": "pointer",
            "fontSize": "12px",
            "fontWeight": "600",
            "backgroundColor": "transparent",
            "color": "#9ca3af",
            "transition": "all 0.15s",
        }

        triggered_id = ctx.triggered_id
        if triggered_id == "toggle-avg-age":
            metric = "avg_age"
            styles = (_inactive, _active, _inactive)
        elif triggered_id == "toggle-on-hold":
            metric = "on_hold_count"
            styles = (_inactive, _inactive, _active)
        else:
            metric = "pct_active"
            styles = (_active, _inactive, _inactive)

        fig = build_treemap_figure(locations, metric)
        return (fig, *styles)

    return app
