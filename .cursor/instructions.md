# Project Instructions

## Project Overview

Ticket Dashboard is a local-first Plotly Dash application for ITS Service Desk Hardware
Repair analytics. It provides a single diagnostic view of the ServiceNow ticket backlog:
KPI strip, state donut, monthly volume, age distribution, category breakdown, pattern
alert cards, flagged ticket table, and location heat map. Data comes from a seeded mock
dataset or a real ServiceNow CSV export specified via `DATA_CSV_PATH` in `.env`.

## Project Mode

**Current Mode: PRODUCTION**

> To switch modes, update this line and add a note in activity_log.md.

## Supported Features (v0.1)

- **KPI strip** — six headline metrics (Total, Active Open, Vendor Queue, Unassigned,
  Misclassified, Auto-Resolve Fail)
- **State donut** — ticket state distribution pie chart
- **Monthly volume** — 12-month incident intake bar chart
- **Age distribution** — active tickets by age bucket with red→green gradient
- **Category breakdown** — active tickets by category; misrouted categories in amber
- **Pattern alerts** — six severity-coded operational flag cards (CRITICAL / WARNING /
  MONITOR / IMMEDIATE)
- **Flagged tickets table** — DataTable with state-conditional row colouring
- **Location heat map** — treemap with three-metric toggle (% active, avg age, on hold)
- **ServiceNow CSV loader** — 31-column real export schema with auto-delimiter detection

## Non-Goals

- Writing back to ServiceNow or any ticketing backend.
- Real-time / push-based data sync (v0.1 pulls on startup).
- Multi-user collaboration or access control.
- Mobile-native UI.

## Key Dependencies

- Python 3.11+
- Plotly Dash 2.17.1 + Dash Bootstrap Components 1.6.0
- Plotly 5.22.0
- Pandas 2.2.2
- Pydantic v2 for all data validation
- pydantic-settings for environment config
- structlog for structured logging
- Anthropic SDK / OpenAI SDK (pre-wired, not active in v0.1)
- MCP (Model Context Protocol — pre-wired, not active in v0.1)

## How Cursor Should Behave

- Read this file, architecture.md, and roadmap.md before any structural change.
- Reference all `rules/*.mdc` files on every generation.
- Flag ambiguity before acting, not after.
- Never generate incomplete placeholder code in `src/`.
- Tests live in `tests/` mirroring `src/` structure exactly.
- All secrets via environment variables. See `.env.example`.
- Keep transform functions pure (no I/O, no side effects).
- Component functions are presentational only — they accept pre-computed dicts and return
  Dash elements; no business logic inside components.
