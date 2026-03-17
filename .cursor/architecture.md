# System Architecture

## Overview

Ticket Dashboard is a local-first Plotly Dash application for ITS Service Desk Hardware Repair analytics. It renders eight sections (KPI strip, state/volume charts, age/category charts, pattern alerts, flagged ticket table, location heat map, AI pattern discovery) from a seeded mock dataset or a real ServiceNow CSV export. All data computation is performed in pure transform functions; Dash components are purely presentational. AI analysis is an optional, on-demand feature that calls Anthropic Claude with active ticket data.

## Runtime Targets

- **Local:** development, prototyping — `python -m src.main` at http://localhost:8050
- **Cloud:** none yet (TBD)
- **Edge:** Raspberry Pi optional when HARDWARE_ENABLED=true

## Component Map

```mermaid
graph TD
    User[User / Browser] --> DashApp[Dash App - src/app.py]
    DashApp --> Layout[Layout Assembly]
    Layout --> KPI[kpi_strip]
    Layout --> StateChart[state_chart]
    Layout --> AgeChart[age_chart]
    Layout --> CatChart[category_chart]
    Layout --> Alerts[pattern_alerts]
    Layout --> FlaggedTbl[flagged_table]
    Layout --> Heatmap[heatmap]
    Layout --> AiSection[ai_patterns]
    DashApp --> Callbacks[Callbacks]
    Callbacks --> DrillDown[_kpi_drill - KPI drill-down panel]
    Callbacks --> HeatmapToggle[_heatmap_metric - heat map toggle]
    Callbacks --> AiPatterns[_ai_patterns - Claude analysis]
    AiPatterns --> Analyzer[src/ai/analyzer.py]
    Analyzer --> Claude[Anthropic Claude API]
    DashApp --> Transforms[src/data/transforms.py]
    Transforms --> Loader[src/data/loader.py]
    Loader --> MockData[load_mock_data]
    Loader --> CSV[load_csv]
    CSV --> CSVFile[ServiceNow CSV Export]
    DashApp --> Config[src/config.py - pydantic-settings]
    Config --> Env[.env / Environment Variables]
```

## Layer Responsibilities

- **Dash App (`src/app.py`):** layout assembly, callback registration (KPI drill-down,
  heat map toggle, AI patterns), startup; derives export date from CSV file mtime
- **Components (`src/components/`):** pure presentational functions; accept pre-computed
  dicts, return Dash elements; no business logic
- **AI Analyzer (`src/ai/analyzer.py`):** `discover_patterns(tickets, api_key)` builds
  a structured prompt, calls `claude-sonnet-4-20250514`, parses JSON response into
  `PatternAlert` objects; only called on user request (not at startup)
- **Transforms (`src/data/transforms.py`):** pure functions computing KPIs, state
  breakdown, monthly volume, age distribution, category breakdown, pattern alerts,
  flagged tickets, location heat map
- **Loader (`src/data/loader.py`):** seeded mock data (1,102 tickets matching
  screenshots) and CSV import with Pydantic validation; auto-detects encoding and
  date formats
- **Config (`src/config.py`):** pydantic-settings BaseSettings; loaded once at startup;
  exposes `anthropic_api_key` for AI feature gating

## Key Constraints

- Secrets never leave the environment layer
- All data from CSV is validated via Pydantic before use
- Mock data is deterministically seeded (random.Random(42)) — always reproducible
- Hardware layer must degrade gracefully when not on Pi hardware
- AI analysis is on-demand only — no network calls at dashboard startup
- AI feature is fully disabled (button hidden, no error) when `ANTHROPIC_API_KEY` is absent
