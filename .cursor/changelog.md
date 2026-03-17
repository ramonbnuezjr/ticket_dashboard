# Changelog

## [Unreleased]

## v0.1.0 — Dashboard MVP

- Built Plotly Dash dashboard for ITS Service Desk Hardware Repair analytics
- Six sections: KPI strip, state donut + monthly volume, age distribution, category breakdown, pattern alerts, flagged ticket table, location heat map with 3-metric toggle
- Seeded mock data layer (1,102 tickets) matching screenshot KPIs exactly
- Pure transform functions for all 8 computed views (fully tested, TDD)
- Pydantic v2 models for all domain types (Ticket, KpiData, PatternAlert, FlaggedTicket)
- CSV loading path via DATA_CSV_PATH env var with Pydantic validation
- pydantic-settings config (DATA_CSV_PATH, ENVIRONMENT, LOG_LEVEL, DASHBOARD_HOST/PORT)
- Added dependencies: dash==2.17.1, plotly==5.22.0, pandas==2.2.2, dash-bootstrap-components==1.6.0

## v0.0.1 — Bootstrap

- Initialized project scaffold via Cursor Bootstrap v2.0
- Layer 1: Cursor rules (standards, security, workflow, agent)
- Layer 2: pyproject.toml, .pre-commit-config.yaml, .env.example
- Layer 3: instructions.md, architecture.md, roadmap.md, activity_log.md
