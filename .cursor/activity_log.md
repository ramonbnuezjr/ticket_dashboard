# Activity Log

## Entries

### 2026-03-17 — Dynamic export date + new CSV import (session 8)

- Mode: PRODUCTION
- Loaded new CSV: `Incidents - ITS Service Desk Hardware Repair.csv` — 86 tickets
  spanning Jan 2025 – Mar 2026; `DATA_CSV_PATH` updated in `.env`
- Replaced hardcoded `_EXPORT_DATE = "Mar 16, 2026"` constant with dynamic derivation
  from the CSV file's modification timestamp (`os.path.getmtime`); export date in
  the dashboard header now updates automatically whenever a new file is dropped in
- Fixed `NameError: name 'export_date' is not defined` — `_header` was a module-level
  function that couldn't see `create_app`'s local variable; fixed by adding
  `export_date: str` as an explicit parameter
- Fixed `AttributeError: 'str' object has no attribute 'exists'` — `settings.data_csv_path`
  is a `str`; wrapped in `Path()` before calling `.exists()`
- `create_app` signature updated: `csv_path: Path | str | None = None`
- Updated all documentation: README, PRD, instructions.md, architecture.md,
  roadmap.md, changelog.md

### 2026-03-17 — AI pattern discovery via Anthropic Claude (session 7)

- Mode: PRODUCTION
- Created `src/ai/` package with `discover_patterns()` using `claude-sonnet-4-20250514`
- Structured prompt returns JSON array of patterns not already covered by the 6 hardcoded
  alerts; capped at 200 active tickets, 200-char description truncation for token budget
- New `src/components/ai_patterns.py`: "Run Analysis" button, `dcc.Loading` spinner,
  session-cached results; gracefully disabled when `ANTHROPIC_API_KEY` is absent
- Wired into `src/app.py` via `dcc.Store(id="ai-patterns-store", storage_type="session")`
  and `_ai_patterns` callback
- `src/config.py` now exposes `anthropic_api_key` field; `src/main.py` passes it to `create_app`
- Fixed structlog vs standard-logging mismatch in `analyzer.py` (keyword args)
- 34 new unit tests across `tests/test_ai_analyzer.py` and `tests/components/test_ai_patterns.py`;
  all 34 pass; Anthropic API fully mocked

### 2026-03-17 — Real CSV compatibility fixes (session 6)

- Mode: PRODUCTION
- Fixed `UnicodeDecodeError`: loader now auto-detects encoding (utf-8-sig → cp1252
  → latin-1); real CSV is Windows-1252 (Excel export with byte 0x96 en-dash)
- Fixed monthly volume showing all 660 tickets in March 2026: `opened_at` in this
  CSV uses `MM-DD-YYYY HH:MM:SS` format not previously in `_SN_DATETIME_FORMATS`
- Fixed `ValidationError: Extra inputs are not permitted` at startup: added
  `extra="ignore"` to `Settings` model_config in `src/config.py`
- Created `.env` (git-ignored) with `DATA_CSV_PATH` pointing to real export
- Confirmed 660 tickets loaded across 18 months (Aug 2024 – Mar 2026)

### 2026-03-17 — Interactive KPI drill-down (session 5)

- Mode: PRODUCTION
- Made all 6 KPI cards clickable: `n_clicks=0`, `id="kpi-card-{key}"`,
  `cursor: pointer`, "click to view ↓" hint text
- Added drill-down panel below KPI strip: `dcc.Store`, `_kpi_drill` callback,
  filterable/sortable `DataTable` with state-coloured rows, ✕ close button
- Toggle behaviour: clicking the active card again dismisses the panel
- Updated `tests/components/test_kpi_strip.py`: 10 new assertions, fixed
  `json.dumps → str()` for `to_plotly_json` serialisation

### 2026-03-16 — Environment setup + dependency fixes (session 4)

- Mode: PRODUCTION
- Resolved `No module named 'structlog'`: created `.venv` with Python 3.11 (Homebrew
  `/opt/homebrew/bin/python3.11`); system `python` resolves to 3.9 on macOS
- Fixed `pyproject.toml`: added `[tool.hatch.build.targets.wheel]` (hatchling src layout)
- Resolved pip dependency conflict chain: mcp 1.0.0→1.9.4, anyio 4.4.0→4.9.0,
  anthropic 0.28.0→0.85.0, pydantic-settings 2.3.4→2.5.2
- Created `data/` directory (git-ignored) for local ServiceNow CSV storage
- Updated `.gitignore`: replaced per-extension data rules with single `data/` entry
- Confirmed dashboard runs: HTTP 200 at http://localhost:8050 with mock data (1,102 tickets)
- Updated documentation: README (venv command, data/ CSV guide), changelog (v0.1.2)

### 2026-03-16 — Documentation update (session 3)

- Mode: PRODUCTION
- Updated all project documentation to reflect built state
- README rewritten: real GitHub URL, correct test paths, CSV column mapping table,
  environment variable table, project structure map, accurate entrypoint instructions
- PRD rewritten: specific ITS Service Desk problem statement with real backlog numbers,
  concrete user flow through the actual dashboard, updated success criteria
- `.cursor/instructions.md` updated: Supported Features now lists all 7 sections + CSV
  loader; Key Dependencies includes Dash/Plotly/Pandas; added component/transform rules
- `.cursor/changelog.md` updated: added v0.1.1 entry for ServiceNow column mapping work
- `.cursor/roadmap.md`: README item ticked in v0.2
- `.env.example`: added `DASHBOARD_HOST` and `DASHBOARD_PORT`

### 2026-03-16 — ServiceNow CSV column mapping (session 2)

- Mode: PRODUCTION
- Updated `src/data/loader.py` to map 31 real ServiceNow columns to `Ticket` model
- Added `short_description` field to `Ticket` model (`src/data/models.py`)
- Updated `compute_flagged_tickets` in `src/data/transforms.py` to use
  `short_description` when available
- Rewrote `tests/test_loader.py` against full 31-column ServiceNow schema
- Pushed v0.1.0 initial commit to https://github.com/ramonbnuezjr/ticket_dashboard

### 2026-03-16 — Dashboard v0.1 implemented (session 1)

- Mode: PRODUCTION
- Built full Plotly Dash dashboard matching all three screenshot sections
- Data layer: seeded mock (1,102 tickets, exact KPI targets), CSV fallback via
  `DATA_CSV_PATH`
- Components: kpi_strip, state_chart, age_chart, category_chart, pattern_alerts,
  flagged_table, heatmap
- TDD: tests written before implementation for models, transforms, loader, and all 7
  components
- App assembly: `src/app.py` (layout + heat map callback), `src/main.py` (entrypoint)
- Docs updated: architecture.md (component map), roadmap.md (v0.1 items ticked),
  changelog.md

### 2026-03-16 — Project initialized via Cursor Bootstrap v2.0

- Mode: PRODUCTION
- Runtime target: Local + Cloud Hybrid (cloud TBD)
- Integrations pre-wired: Anthropic SDK, OpenAI SDK, MCP, Raspberry Pi GPIO
- Toolchain: Black, Ruff, mypy strict, Bandit, pre-commit, pytest-cov
