# Ticket Dashboard

## Prerequisites

- Python 3.11+

## Setup

```bash
# Clone and enter project
git clone <repo-url> && cd <project-dir>

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Configure environment
cp .env.example .env
# Edit .env — fill in required values
```

## Running Tests

```bash
pytest                          # Run all tests with coverage
pytest tests/unit/              # Unit tests only
pytest --no-cov                # Skip coverage (faster iteration)
```

## Running the Application

```bash
python -m src.main              # Update with actual entrypoint when added
```

## Environment Variables

See `.env.example` for all required and optional variables with descriptions.

## Hardware Notes (Raspberry Pi)

Set `HARDWARE_ENABLED=false` in `.env` for non-Pi environments. GPIO functionality degrades gracefully when disabled.
