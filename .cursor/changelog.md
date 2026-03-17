# Changelog

## [Unreleased]

## v0.1.6 — Dynamic export date + new CSV import

- `src/app.py`: `_header` now accepts `export_date: str` as an explicit parameter
  instead of reading a module-level constant; `create_app` accepts
  `csv_path: Path | str | None` and derives the export date from the CSV file's
  modification timestamp via `os.path.getmtime`; falls back to latest ticket date
  if no path is provided, or "unknown" for mock data
- `src/main.py`: passes `csv_path=settings.data_csv_path` to `create_app`
- Added `import datetime`, `import os`, `from pathlib import Path` to `src/app.py`
- New CSV loaded: `Incidents - ITS Service Desk Hardware Repair.csv` (86 tickets,
  Jan 2025 – Mar 2026, exported Mar 17 2026); `DATA_CSV_PATH` updated in `.env`
- Documentation updated: README (AI section, dynamic export date, updated structure),
  PRD (user flow step 10, success criteria), instructions.md (AI feature active,
  dynamic export date), architecture.md (mermaid diagram, AI layer, constraints),
  roadmap.md (dynamic export date ticked), changelog, activity_log

## v0.1.5 — AI-powered pattern discovery via Anthropic Claude

- `src/ai/__init__.py` + `src/ai/analyzer.py`: new module; `discover_patterns(tickets,
  api_key)` sends structured prompt to `claude-sonnet-4-20250514`, parses JSON
  response into `PatternAlert` objects; handles malformed JSON gracefully; filters
  to active tickets and caps at 200 to stay within token budget
- `src/components/ai_patterns.py`: new component; `ai_pattern_section(has_key)` renders
  "Run Analysis" button (disabled when `ANTHROPIC_API_KEY` absent), `dcc.Loading`
  spinner, and results container; `ai_pattern_card` reuses existing pattern-alert
  visual style; `render_ai_results` packs cards into rows of three
- `src/app.py`: added `dcc.Store(id="ai-patterns-store", storage_type="session")` +
  `_ai_patterns` callback; results cached for the browser session to avoid redundant
  API calls
- `src/config.py`: added `anthropic_api_key: Optional[str]` field; Settings now reads
  `ANTHROPIC_API_KEY` from `.env`
- `src/main.py`: passes `api_key=settings.anthropic_api_key` to `create_app`; logs
  whether AI discovery is enabled or disabled at startup
- `.env.example`: clarified `ANTHROPIC_API_KEY` usage note
- `tests/test_ai_analyzer.py`: 19 unit tests covering `_build_user_message`,
  `_parse_response`, `_to_pattern_alert`, and `discover_patterns` (Anthropic API
  fully mocked)
- `tests/components/test_ai_patterns.py`: 15 unit tests covering component rendering,
  button state, loading wrapper, and result layout for 1–7 alerts
- Fixed `src/ai/analyzer.py`: switched from `logging.getLogger` to `structlog.get_logger`
  so keyword-argument log calls (`error=`, `raw=`) work correctly

## v0.1.4 — Real CSV compatibility fixes

- `src/data/loader.py`: encoding auto-detection added — tries `utf-8-sig` first,
  then `cp1252` (Windows-1252 / Excel export), then `latin-1` fallback; previously
  crashed with `UnicodeDecodeError` on byte `0x96` (Windows en-dash)
- `src/data/loader.py`: added `MM-DD-YYYY HH:MM:SS` (`%m-%d-%Y %H:%M:%S`) and
  related date-only variants to `_SN_DATETIME_FORMATS`; previously all tickets
  fell back to `date.today()` so every ticket appeared in the current month
- `src/config.py`: added `extra="ignore"` to `SettingsConfigDict` so pre-wired
  env vars (`ANTHROPIC_MODEL`, `OPENAI_MODEL`, `GPIO_MODE`) don't raise
  `ValidationError: Extra inputs are not permitted` at startup
- `.env` created (git-ignored); `DATA_CSV_PATH` auto-resolved to correct filename

## v0.1.3 — Interactive KPI cards with drill-down panel

- `src/components/kpi_strip.py`: each card now has `id="kpi-card-{key}"`,
  `n_clicks=0`, `cursor: pointer`, and a "click to view ↓" hint
- `src/app.py`: added `dcc.Store` + drill-down wrapper panel below the KPI strip;
  `_kpi_drill` callback handles all 6 card inputs and the ✕ close button; renders
  a filterable, sortable `DataTable` with state-coloured rows sorted oldest-first
- Filter mapping: Total → all, Active Open → `is_active`, Vendor Queue →
  `is_vendor_hold`, Unassigned → `is_active and no tech`, Misclassified →
  `is_active and misrouted_category`, Auto-Resolve Fail → `notification_count ≥ 3`
- Clicking the same card a second time toggles the panel closed
- `tests/components/test_kpi_strip.py`: 10 new assertions (card IDs, n_clicks,
  cursor style, drill hint text); fixed `to_plotly_json` serialisation (`str()`
  instead of `json.dumps()`)

## v0.1.2 — Dependency fixes + environment setup

- Added `[tool.hatch.build.targets.wheel] packages = ["src"]` to `pyproject.toml` so
  hatchling can locate the `src/` layout during editable install
- Resolved cascading dependency conflicts caused by `mcp 1.0.0`:
  - `mcp` 1.0.0 → 1.9.4
  - `anyio` 4.4.0 → 4.9.0 (mcp 1.9.4 requires ≥4.6)
  - `anthropic` 0.28.0 → 0.85.0 (latest stable)
  - `pydantic-settings` 2.3.4 → 2.5.2 (mcp 1.9.4 minimum)
- Created `data/` directory for local ServiceNow CSV placement (git-ignored)
- Updated `.gitignore` to ignore entire `data/` directory (replaces per-extension rules)
- Confirmed first successful run: `python -m src.main` serves at http://localhost:8050
- README updated: `python3.11` venv creation, `data/` folder usage in CSV loading guide

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
