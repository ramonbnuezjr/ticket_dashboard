"""Entrypoint for the ticket dashboard.

Run with:
    python -m src.main

The Dash dev server will start at http://localhost:8050 by default.
Set DASHBOARD_HOST, DASHBOARD_PORT in .env to override.
"""

from __future__ import annotations

import logging

import structlog

from src.app import create_app
from src.config import Settings
from src.data.loader import get_tickets


def main() -> None:
    """Load config, load data, create app, and start the server."""
    settings = Settings()

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level.upper())
        ),
    )

    log = structlog.get_logger(__name__)
    log.info(
        "dashboard_starting",
        environment=settings.environment,
        host=settings.dashboard_host,
        port=settings.dashboard_port,
        data_source="csv" if settings.data_csv_path else "mock",
    )

    tickets = get_tickets(settings)
    app = create_app(tickets)

    app.run(
        host=settings.dashboard_host,
        port=settings.dashboard_port,
        debug=(settings.environment == "local"),
    )


if __name__ == "__main__":
    main()
