# Activity Log

## Entries

### 2026-03-16 — Dashboard v0.1 implemented (Cursor Bootstrap v2.0 session)

- Mode: PRODUCTION
- Built full Plotly Dash dashboard matching all three screenshot sections
- Data layer: seeded mock (1,102 tickets, exact KPI targets), CSV fallback via DATA_CSV_PATH
- Components: kpi_strip, state_chart, age_chart, category_chart, pattern_alerts, flagged_table, heatmap
- TDD: tests written before implementation for models, transforms, loader, and all 7 components
- App assembly: src/app.py (layout + heat map callback), src/main.py (entrypoint)
- Docs updated: architecture.md (component map), roadmap.md (v0.1 items ticked), changelog.md

### 2026-03-16 — Project initialized via Cursor Bootstrap v2.0

- Mode: PRODUCTION
- Runtime target: Local + Cloud Hybrid (cloud TBD)
- Integrations pre-wired: Anthropic SDK, OpenAI SDK, MCP, Raspberry Pi GPIO
- Toolchain: Black, Ruff, mypy strict, Bandit, pre-commit, pytest-cov
