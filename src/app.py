"""Dash application factory — assembles layout and registers callbacks."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table, dcc, html

from src.components import (
    COLOR_BG,
    COLOR_BORDER,
    COLOR_CRITICAL,
    COLOR_MONITOR,
    COLOR_SURFACE,
    COLOR_SURFACE_2,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
)
from src.components.age_chart import age_chart
from src.components.ai_patterns import ai_pattern_section, render_ai_results
from src.components.category_chart import category_chart
from src.components.flagged_table import flagged_table
from src.components.heatmap import build_treemap_figure, heatmap_section
from src.components.kpi_strip import kpi_strip
from src.components.pattern_alerts import pattern_alerts
from src.components.state_chart import state_chart
from src.data.models import Ticket, TicketCategory
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

# ---------------------------------------------------------------------------
# KPI drill-down — filter definitions
# ---------------------------------------------------------------------------

# Maps each card id suffix → display metadata + ticket filter predicate.
# The filter lambda receives a single Ticket and returns True to include it.
_KPI_FILTER_DEFS: dict[str, dict[str, Any]] = {
    "total": {
        "label": "All Incidents",
        "sub": "Complete dataset",
        "color": COLOR_TEXT_PRIMARY,
        "filter": lambda t: True,
    },
    "active_open": {
        "label": "Active Open",
        "sub": "Not closed, resolved, or cancelled",
        "color": COLOR_WARNING,
        "filter": lambda t: t.is_active,
    },
    "vendor_queue": {
        "label": "Vendor Queue",
        "sub": "On Hold · NCT",
        "color": COLOR_MONITOR,
        "filter": lambda t: t.is_vendor_hold,
    },
    "unassigned": {
        "label": "Unassigned",
        "sub": "Active · no tech assigned",
        "color": COLOR_CRITICAL,
        "filter": lambda t: t.is_active and t.assigned_tech is None,
    },
    "misclassified": {
        "label": "Misclassified",
        "sub": "Wrong category for HW Repair queue",
        "color": COLOR_WARNING,
        "filter": lambda t: t.is_active
        and t.category in TicketCategory.misrouted_categories(),
    },
    "auto_resolve_fail": {
        "label": "Auto-Resolve Fail",
        "sub": "3+ notifications · still open",
        "color": COLOR_CRITICAL,
        "filter": lambda t: t.is_active and t.notification_count >= 3,
    },
}

_DRILL_COLUMNS = [
    {"id": "number", "name": "Ticket #"},
    {"id": "state", "name": "State"},
    {"id": "age", "name": "Age (days)", "type": "numeric"},
    {"id": "category", "name": "Category"},
    {"id": "location", "name": "Location"},
    {"id": "tech", "name": "Assigned Tech"},
    {"id": "description", "name": "Description"},
]

_STATE_BADGE_CONDITIONS = [
    {
        "if": {"filter_query": '{state} = "OnHold"', "column_id": "state"},
        "color": COLOR_MONITOR,
        "fontWeight": "700",
    },
    {
        "if": {"filter_query": '{state} = "Assigned"', "column_id": "state"},
        "color": COLOR_WARNING,
        "fontWeight": "700",
    },
    {
        "if": {"filter_query": '{state} = "WorkInProgress"', "column_id": "state"},
        "color": COLOR_CRITICAL,
        "fontWeight": "700",
    },
    {
        "if": {"filter_query": '{state} = "Resolved"', "column_id": "state"},
        "color": "#22c55e",
        "fontWeight": "700",
    },
    {
        "if": {"filter_query": '{state} = "Closed"', "column_id": "state"},
        "color": "#6b7280",
    },
    {
        "if": {"filter_query": '{state} = "Cancelled"', "column_id": "state"},
        "color": "#6b7280",
    },
]


def _filter_tickets(tickets: list[Ticket], key: str) -> list[Ticket]:
    """Return tickets matching the KPI filter identified by *key*."""
    predicate = _KPI_FILTER_DEFS.get(key, {}).get("filter")
    if predicate is None:
        return []
    return [t for t in tickets if predicate(t)]


def _build_drill_table(tickets: list[Ticket], key: str) -> list[html.Div]:
    """Build the DataTable rows for the drill-down panel."""
    filtered = sorted(
        _filter_tickets(tickets, key), key=lambda t: t.age_days, reverse=True
    )
    if not filtered:
        return [
            html.Div(
                "No tickets match this filter.",
                style={"color": COLOR_TEXT_MUTED, "fontSize": "13px", "padding": "8px 0"},
            )
        ]

    rows = [
        {
            "number": t.number,
            "state": t.state.value,
            "age": t.age_days,
            "category": t.category.value,
            "location": t.location,
            "tech": t.assigned_tech or "—",
            "description": t.short_description or "—",
        }
        for t in filtered
    ]

    table = dash_table.DataTable(
        id="kpi-drill-datatable",
        columns=_DRILL_COLUMNS,
        data=rows,
        sort_action="native",
        filter_action="native",
        page_size=25,
        style_as_list_view=False,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": COLOR_SURFACE_2,
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
            "maxWidth": "280px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_data_conditional=_STATE_BADGE_CONDITIONS,
        style_filter={
            "backgroundColor": COLOR_SURFACE,
            "color": COLOR_TEXT_PRIMARY,
            "border": f"1px solid {COLOR_BORDER}",
            "fontSize": "12px",
        },
    )
    return [table]


def _header(total: int, export_date: str) -> html.Div:
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
                f"{total:,} incidents · export date {export_date}",
                style={"fontSize": "12px", "color": COLOR_TEXT_MUTED},
            ),
        ],
    )


def create_app(
    tickets: list[Ticket],
    api_key: str | None = None,
    csv_path: Path | str | None = None,
) -> dash.Dash:
    """Build and return the configured Dash application.

    Args:
        tickets: Full ticket list from get_tickets().
        api_key: Anthropic API key. When provided, the AI Pattern Discovery
                 section is enabled. When None, the button is disabled.
        csv_path: Path to the source CSV file; used to derive the export date
                  from the file's modification timestamp.

    Returns:
        A Dash app instance ready for app.run().
    """
    # Derive export date from the CSV file's modification timestamp (= when it was
    # pulled from ServiceNow), falling back to the latest ticket date if unavailable.
    if csv_path and Path(csv_path).exists():
        export_date = datetime.datetime.fromtimestamp(os.path.getmtime(Path(csv_path))).strftime("%b %-d, %Y")
    elif tickets:
        export_date = max(t.created_date for t in tickets).strftime("%b %-d, %Y")
    else:
        export_date = "unknown"

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
            _header(kpi.total, export_date),

            # 2. KPI strip
            html.Div(
                style={**_SECTION_STYLE, "paddingBottom": "8px"},
                children=[kpi_strip(kpi)],
            ),

            # 3. KPI drill-down panel (hidden until a card is clicked)
            dcc.Store(id="kpi-drill-store", data=None),
            html.Div(
                id="kpi-drill-wrapper",
                style={"display": "none"},
                children=[
                    html.Div(
                        style={
                            **_SECTION_STYLE,
                            "paddingTop": "12px",
                            "paddingBottom": "16px",
                            "borderTop": f"2px solid {COLOR_BORDER}",
                            "borderBottom": f"1px solid {COLOR_BORDER}",
                        },
                        children=[
                            # Panel header: label + count + close button
                            html.Div(
                                style={
                                    "display": "flex",
                                    "justifyContent": "space-between",
                                    "alignItems": "center",
                                    "marginBottom": "14px",
                                },
                                children=[
                                    html.Div(id="kpi-drill-header"),
                                    html.Button(
                                        "✕",
                                        id="kpi-drill-close",
                                        n_clicks=0,
                                        style={
                                            "background": "none",
                                            "border": f"1px solid {COLOR_BORDER}",
                                            "borderRadius": "4px",
                                            "color": COLOR_TEXT_MUTED,
                                            "fontSize": "14px",
                                            "cursor": "pointer",
                                            "lineHeight": "1",
                                            "padding": "4px 8px",
                                        },
                                    ),
                                ],
                            ),
                            # DataTable content
                            html.Div(id="kpi-drill-panel"),
                        ],
                    ),
                ],
            ),

            # 4. State donut + monthly volume
            html.Div(
                style=_SECTION_STYLE,
                children=[state_chart(state_breakdown, monthly_volume)],
            ),

            # 5. Age distribution + category breakdown
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

            # 6. Pattern alerts
            html.Div(style=_SECTION_STYLE, children=[pattern_alerts(alerts)]),

            # 7. AI-discovered patterns
            dcc.Store(id="ai-patterns-store", storage_type="session"),
            html.Div(
                style={**_SECTION_STYLE, "borderTop": f"1px solid {COLOR_BORDER}"},
                children=[ai_pattern_section(has_key=bool(api_key))],
            ),

            # 9. Flagged tickets table
            html.Div(style=_SECTION_STYLE, children=[flagged_table(flagged)]),

            # 10. Heat map
            html.Div(style=_SECTION_STYLE, children=[heatmap_section(locations)]),
        ],
    )

    # -----------------------------------------------------------------------
    # Callback: KPI card drill-down
    # -----------------------------------------------------------------------

    @app.callback(
        Output("kpi-drill-store", "data"),
        Output("kpi-drill-wrapper", "style"),
        Output("kpi-drill-header", "children"),
        Output("kpi-drill-panel", "children"),
        Input("kpi-card-total", "n_clicks"),
        Input("kpi-card-active_open", "n_clicks"),
        Input("kpi-card-vendor_queue", "n_clicks"),
        Input("kpi-card-unassigned", "n_clicks"),
        Input("kpi-card-misclassified", "n_clicks"),
        Input("kpi-card-auto_resolve_fail", "n_clicks"),
        Input("kpi-drill-close", "n_clicks"),
        State("kpi-drill-store", "data"),
        prevent_initial_call=True,
    )
    def _kpi_drill(
        _n_total: int,
        _n_active: int,
        _n_vendor: int,
        _n_unassigned: int,
        _n_misclass: int,
        _n_auto: int,
        _n_close: int,
        current_filter: str | None,
    ) -> tuple[str | None, dict[str, str], list[Any], list[Any]]:
        """Open or close the KPI drill-down panel based on which card was clicked."""
        from dash import ctx

        _hidden = {"display": "none"}
        triggered = ctx.triggered_id

        # Close button or unknown trigger → dismiss panel
        if triggered is None or triggered == "kpi-drill-close":
            return None, _hidden, [], []

        filter_key = str(triggered).replace("kpi-card-", "")

        # Toggle: clicking the active card again dismisses the panel
        if current_filter == filter_key:
            return None, _hidden, [], []

        # Build header
        meta = _KPI_FILTER_DEFS[filter_key]
        filtered_count = len(_filter_tickets(tickets, filter_key))
        header = [
            html.Span(
                meta["label"],
                style={
                    "fontWeight": "700",
                    "fontSize": "15px",
                    "color": meta["color"],
                    "marginRight": "10px",
                },
            ),
            html.Span(
                f"{filtered_count:,} tickets",
                style={
                    "fontSize": "13px",
                    "fontWeight": "600",
                    "color": COLOR_TEXT_PRIMARY,
                    "marginRight": "8px",
                },
            ),
            html.Span(
                f"· {meta['sub']}",
                style={"fontSize": "12px", "color": COLOR_TEXT_MUTED},
            ),
        ]

        table_children = _build_drill_table(tickets, filter_key)
        return filter_key, {"display": "block"}, header, table_children

    # -----------------------------------------------------------------------
    # Callback: AI Pattern Discovery
    # -----------------------------------------------------------------------

    @app.callback(
        Output("ai-pattern-results", "children"),
        Output("ai-patterns-store", "data"),
        Input("ai-run-btn", "n_clicks"),
        State("ai-patterns-store", "data"),
        prevent_initial_call=True,
    )
    def _ai_patterns(
        n_clicks: int,
        cached: list[dict] | None,
    ) -> tuple[list, list[dict] | None]:
        """Run AI pattern discovery or return cached results."""
        from src.ai.analyzer import discover_patterns
        from src.data.models import AlertSeverity, PatternAlert

        if not api_key:
            return (
                [html.Div(
                    "ANTHROPIC_API_KEY is not set. Add it to .env and restart.",
                    style={"color": "#e74c3c", "fontSize": "13px"},
                )],
                None,
            )

        # Return cached results without re-calling the API
        if cached:
            patterns = [
                PatternAlert(
                    severity=AlertSeverity(item["severity"]),
                    title=item["title"],
                    description=item["description"],
                    count=item["count"],
                )
                for item in cached
            ]
            return render_ai_results(patterns), cached

        try:
            patterns = discover_patterns(tickets, api_key)
        except Exception as exc:  # noqa: BLE001
            error_msg = str(exc)[:200]
            return (
                [html.Div(
                    f"Analysis failed: {error_msg}",
                    style={"color": "#e74c3c", "fontSize": "13px"},
                )],
                None,
            )

        # Serialise to plain dicts for dcc.Store (Pydantic models not JSON-serialisable)
        cache_data = [
            {
                "severity": p.severity.value,
                "title": p.title,
                "description": p.description,
                "count": p.count,
            }
            for p in patterns
        ]

        return render_ai_results(patterns), cache_data

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
