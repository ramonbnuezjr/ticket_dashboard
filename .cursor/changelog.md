# Changelog

## [Unreleased]

## v0.1.1 — ServiceNow CSV column mapping

- Updated `src/data/loader.py` to map all 31 real ServiceNow export columns to the
  `Ticket` model (previously mapped generic/placeholder columns)
- Added helpers: `_SN_STATE_MAP`, `_SN_CATEGORY_MAP`, `_parse_sn_date`,
  `_resolve_state`, `_resolve_category`, `_compute_age_days`, `_detect_delimiter`
- `age_days` derived from `opened_at`/`closed_at`; falls back to `calendar_stc`
  (seconds) when datetime fields are absent
- `is_vendor_hold` derived from `hold_reason` keyword matching
- `is_leadership_flagged` derived from `u_escalation_status`
- `u_notification_counter` mapped to `notification_count`
- `short_description` added to `Ticket` model; used as issue summary in flagged table
- `compute_flagged_tickets` updated to prefer `short_description` over computed summaries
- `tests/test_loader.py` rewritten against full 31-column ServiceNow schema with
  dedicated tests for each derived field
- Documentation updated: README, PRD, instructions.md, architecture.md, roadmap.md,
  activity_log.md, .env.example

## v0.1.0 — Dashboard MVP

- Built Plotly Dash dashboard for ITS Service Desk Hardware Repair analytics
- Seven sections: KPI strip, state donut + monthly volume, age distribution, category
  breakdown, pattern alerts, flagged ticket table, location heat map with 3-metric toggle
- Seeded mock data layer (1,102 tickets) matching screenshot KPIs exactly
- Pure transform functions for all 8 computed views (fully tested, TDD)
- Pydantic v2 models for all domain types (Ticket, KpiData, PatternAlert, FlaggedTicket)
- CSV loading path via `DATA_CSV_PATH` env var with Pydantic validation
- pydantic-settings config (`DATA_CSV_PATH`, `ENVIRONMENT`, `LOG_LEVEL`,
  `DASHBOARD_HOST`, `DASHBOARD_PORT`)
- Dependencies added: `dash==2.17.1`, `plotly==5.22.0`, `pandas==2.2.2`,
  `dash-bootstrap-components==1.6.0`
- Dash app factory (`src/app.py`) + entrypoint (`src/main.py`)

## v0.0.1 — Bootstrap

- Initialized project scaffold via Cursor Bootstrap v2.0
- Layer 1: Cursor rules (standards, security, workflow, agent)
- Layer 2: `pyproject.toml`, `.pre-commit-config.yaml`, `.env.example`
- Layer 3: `instructions.md`, `architecture.md`, `roadmap.md`, `activity_log.md`
