# Project Instructions

## Project Overview

Ticket Dashboard is a local-first application for viewing and managing tickets. It provides a single place to see, filter, and work with tickets. The stack is designed for local execution with optional cloud deployment later. Integrations include AI (Anthropic/OpenAI) and MCP for extensibility.

## Project Mode

**Current Mode: PRODUCTION**

> To switch modes, update this line and add a note in activity_log.md.

## Supported Features

TBD until PRD is complete.

## Non-Goals

- Full ticketing system backend (e.g., Jira/Linear) replacement — this dashboard consumes or aggregates; it does not replace source systems.
- Real-time multi-user collaboration in v0.1.
- Mobile-native UI in initial scope.

## Key Dependencies

- Python 3.11+
- Anthropic SDK / OpenAI SDK
- MCP (Model Context Protocol)
- Pydantic v2 for all data validation
- Raspberry Pi GPIO (conditionally enabled via HARDWARE_ENABLED env var)

## How Cursor Should Behave

- Read this file, architecture.md, and roadmap.md before any structural change.
- Reference all rules/*.mdc files on every generation.
- Flag ambiguity before acting, not after.
- Never generate incomplete placeholder code in src/.
- Tests live in tests/ mirroring src/ structure exactly.
- All secrets via environment variables. See .env.example.
