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
- [ ] GPIO abstraction layer (hardware-conditional) — deferred to v0.2
- [ ] ≥1 passing end-to-end integration test

## v0.2 — Hardening

- [ ] Coverage ≥90% on all core modules (run `pytest`)
- [ ] Pre-commit hooks passing cleanly
- [ ] mypy strict passing cleanly
- [ ] All secrets validated as present at startup
- [ ] Structured logging wired throughout
- [ ] GPIO abstraction layer (hardware-conditional)
- [ ] README complete and accurate

## v1.0 — Production-Ready

- [ ] Cloud deployment configuration (Dockerfile or equivalent) — none yet; target TBD
- [ ] CI pipeline (GitHub Actions or equivalent)
- [ ] Security audit passing (bandit + pip-audit clean)
- [ ] Full documentation in docs/
- [ ] CHANGELOG reflects all meaningful changes
