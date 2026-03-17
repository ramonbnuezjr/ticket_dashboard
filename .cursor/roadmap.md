# Roadmap

## v0.1 — MVP

- [x] Core directory structure and toolchain operational
- [x] Environment config loading via pydantic-settings (`src/config.py`)
- [x] Seeded mock data layer with exact KPI targets (`src/data/loader.py`)
- [x] Pydantic data models (`src/data/models.py`)
- [x] Pure transform functions for all 8 dashboard computations (`src/data/transforms.py`)
- [x] KPI strip, state/volume, age, category, patterns, flagged table, heat map components
- [x] Plotly Dash app assembly + heat map toggle callback (`src/app.py`)
- [x] Entrypoint (`src/main.py`: `python -m src.main`)
- [x] TDD test suite covering all core modules
- [x] ServiceNow CSV loader with full 31-column real export schema
- [x] Initial commit pushed to https://github.com/ramonbnuezjr/ticket_dashboard
- [x] Interactive KPI cards with drill-down ticket panel (`dcc.Store` + callback)
- [x] Real CSV compatibility: Windows-1252 encoding, MM-DD-YYYY date format
- [ ] ≥1 passing end-to-end integration test
- [ ] GPIO abstraction layer (hardware-conditional) — deferred to v0.2

## v0.2 — Hardening

- [ ] Coverage ≥90% on all core modules (`pytest --cov-fail-under=90`)
- [ ] Pre-commit hooks passing cleanly
- [ ] mypy strict passing cleanly
- [ ] All required secrets validated as present at startup
- [ ] Structured logging wired throughout (structlog)
- [ ] GPIO abstraction layer (hardware-conditional)
- [x] README complete and accurate

## v1.0 — Production-Ready

- [ ] Cloud deployment configuration (Dockerfile or equivalent) — target TBD
- [ ] CI pipeline (GitHub Actions)
- [ ] Security audit passing (bandit + pip-audit clean)
- [ ] Full documentation in `docs/`
- [ ] CHANGELOG reflects all meaningful changes
