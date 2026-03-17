# Activity Log

## Entries

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
