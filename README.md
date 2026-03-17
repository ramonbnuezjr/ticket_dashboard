# Ticket Dashboard — ITS Service Desk Hardware Repair

A local-first analytics dashboard for ITS Service Desk Hardware Repair operations.
Built with Plotly Dash, it surfaces ticket backlog health, age risk, misrouting patterns,
and location concentration from a ServiceNow CSV export — or from a seeded mock dataset
that reproduces the exact KPIs from the source analysis.

**GitHub:** https://github.com/ramonbnuezjr/ticket_dashboard

---

## Dashboard sections

| Section | What it shows |
|---|---|
| **KPI strip** | Total, Active Open, Vendor Queue, Unassigned, Misclassified, Auto-Resolve Fail — **click any card to drill into the matching tickets** |
| **State donut** | Ticket state breakdown (Assigned / Closed / On Hold / WIP / Resolved / Cancelled) |
| **Monthly volume** | Incident count by month — last 12 months |
| **Age distribution** | Active ticket count by age bucket (0–30d → 365+d), red→green gradient |
| **Category breakdown** | Active tickets by category; misrouted categories highlighted in amber |
| **Pattern alerts** | Six severity-coded operational flags (CRITICAL / WARNING / MONITOR / IMMEDIATE) |
| **Flagged tickets** | Immediate-action table: ticket number, state, age, pattern, issue summary, owner |
| **Location heat map** | Treemap by building; toggle between % active open, avg age, on hold count |

---

## Prerequisites

- Python 3.11+
- Git

---

## Setup

```bash
# Clone the repository
git clone https://github.com/ramonbnuezjr/ticket_dashboard.git
cd ticket_dashboard

# Create and activate a virtual environment
# macOS ships Python 3.9 — use the Homebrew 3.11 binary explicitly
python3.11 -m venv .venv && source .venv/bin/activate

# Install the package with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env — DATA_CSV_PATH is optional; all other vars have safe defaults
```

---

## Running the dashboard

```bash
python -m src.main
```

Opens at **http://localhost:8050** by default.

The dashboard loads from seeded mock data (1,102 tickets, exact KPI targets) unless
`DATA_CSV_PATH` is set. Set `ENVIRONMENT=local` (default) to enable Dash's hot-reload.

---

## Loading real ServiceNow data

Export your incident list from ServiceNow, place the file in the `data/` folder
(git-ignored — nothing in that folder will ever be committed), then set the path in `.env`:

```bash
# Recommended — keeps the file inside the project but out of git
cp /path/to/export.csv data/export.csv
```

```dotenv
DATA_CSV_PATH=/absolute/path/to/ticket_dashboard/data/export.csv
```

The loader auto-detects comma or tab delimiters and handles both UTF-8 and
Windows-1252 encoding (standard Excel exports work without any conversion).
`opened_at` accepts multiple date formats including `MM-DD-YYYY HH:MM:SS`.

Required CSV columns (from a standard ServiceNow incident export):

| Column | Used for |
|---|---|
| `number` | Ticket number |
| `state` | Ticket state (text label or numeric code) |
| `category` | Incident category → mapped to Hardware / Remote Access / etc. |
| `assigned_to` | Technician name (`assigned_tech`; empty → unassigned) |
| `location` | Building / site name |
| `opened_at` | Creation date (datetime string) → `created_date` + `age_days` |
| `closed_at` | Close date for terminal tickets (used in age calculation) |
| `u_notification_counter` | Auto-resolve notification count |
| `hold_reason` | Vendor/NCT hold detection |
| `u_escalation_status` | Leadership escalation flag (non-empty, non-"Normal" → flagged) |
| `short_description` | Ticket summary (shown in flagged table) |
| `calendar_stc` | Fallback age (seconds) when `opened_at` is missing |

All other export columns are accepted and silently ignored.

---

## Running tests

```bash
pytest                    # Full suite with coverage report (≥90% gate)
pytest tests/             # All tests, explicit path
pytest tests/components/  # Component tests only
pytest --no-cov           # Skip coverage gate (faster iteration)
```

Test layout mirrors `src/` exactly:

```
tests/
├── test_models.py
├── test_transforms.py
├── test_loader.py
└── components/
    ├── test_kpi_strip.py
    ├── test_state_chart.py
    ├── test_age_chart.py
    ├── test_category_chart.py
    ├── test_pattern_alerts.py
    ├── test_flagged_table.py
    └── test_heatmap.py
```

---

## Environment variables

See `.env.example` for the full list with descriptions. Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATA_CSV_PATH` | _(unset)_ | Absolute path to ServiceNow CSV export. Mock data used if unset. |
| `ENVIRONMENT` | `local` | `local` enables Dash debug/hot-reload |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `DASHBOARD_HOST` | `0.0.0.0` | Bind host for the Dash server |
| `DASHBOARD_PORT` | `8050` | Bind port for the Dash server |

---

## Project structure

```
src/
├── config.py          pydantic-settings — all runtime config
├── main.py            entrypoint
├── app.py             Dash app factory + heat map callback
├── data/
│   ├── models.py      Pydantic: Ticket, KpiData, PatternAlert, FlaggedTicket
│   ├── transforms.py  8 pure compute functions (no I/O)
│   └── loader.py      mock data generator + ServiceNow CSV parser
└── components/        7 presentational Dash components
    ├── kpi_strip.py
    ├── state_chart.py
    ├── age_chart.py
    ├── category_chart.py
    ├── pattern_alerts.py
    ├── flagged_table.py
    └── heatmap.py
```

---

## Hardware notes (Raspberry Pi)

Set `HARDWARE_ENABLED=false` in `.env` for non-Pi environments (the default).
GPIO functionality is stubbed and degrades gracefully when disabled.
