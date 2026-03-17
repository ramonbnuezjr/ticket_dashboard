# Product Requirements Document

## Problem Statement

ITS Service Desk managers lack a single diagnostic view of the Hardware Repair ticket
backlog. Without it, they cannot quickly answer the questions that matter most to
operations and leadership: How many tickets are actively open and how long have they been
open? Which sites are driving volume? Which tickets need action today?

The snapshot that motivated this build: 696 active open tickets, 373 of them aged 180+
days, 515 unassigned, a single technician carrying 118 of 181 assigned tickets, and two
categories (Remote Access, Software/App) generating ~30% of volume despite being
out-of-scope for Hardware Repair — all invisible without manually querying ServiceNow.

Ticket Dashboard solves this by providing a local analytics dashboard that surfaces these
signals from a standard ServiceNow CSV export or a reproducible mock dataset.

---

## Core User Flow

1. Analyst runs `python -m src.main` and opens `http://localhost:8050`.
2. The **KPI strip** gives a six-number status snapshot at a glance.
3. The **state donut** shows the distribution of active states; the monthly volume bar
   reveals whether incident intake is trending up or down.
4. The **age distribution** chart uses a red→green gradient to make the 180+-day backlog
   impossible to miss.
5. The **category breakdown** highlights misrouted categories in amber so the manager can
   redirect tickets or update routing rules.
6. The **pattern alert cards** surface six operational flags (e.g., auto-resolve failure,
   notification storm, leadership escalation) with severity coding.
7. The **flagged tickets table** lists the specific records requiring immediate action —
   ticket number, age, pattern, owner, and short description.
8. The **location heat map** (treemap with three-metric toggle) shows whether hardware
   failures are clustering geographically across Clermont, Garrison, Halsey, and other
   sites.
9. Analyst loads a fresh ServiceNow export by updating `DATA_CSV_PATH` in `.env` and
   restarting the server — no code changes required.

---

## Non-Goals

- Replacing ServiceNow or any full ticketing backend — this dashboard reads and
  visualises; it does not write back to the source system.
- Real-time / push-based data sync (v0.1 is pull-on-startup).
- Multi-user collaboration or access control in v0.1.
- Mobile-native or offline-first interface.
- Ticket creation, status updates, or assignment changes.

---

## Success Criteria

- [x] User can run `python -m src.main` and see a complete, meaningful dashboard at
      `http://localhost:8050` with all seven sections rendered.
- [x] Configuration is loaded from `.env` and validated at startup via `pydantic-settings`.
- [x] All core modules pass mypy strict; test suite runs with Black + Ruff + pytest-cov;
      TDD test files written before source for every component.
- [ ] ≥90% test coverage enforced by `--cov-fail-under=90` (v0.2 target).
- [ ] Pre-commit hooks pass cleanly on every commit (v0.2 target).

---

*Engineering rules live in `.cursor/rules/`. This document is scope-only.*
