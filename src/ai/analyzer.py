"""AI-powered pattern discovery using Anthropic Claude.

Sends active ticket descriptions to Claude and returns a list of newly
discovered operational clusters that are not covered by the six hardcoded
rule-based alerts.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic
import structlog

from src.data.models import AlertSeverity, PatternAlert, Ticket

log = structlog.get_logger(__name__)

# Claude model to use — sonnet balances capability and cost.
_MODEL = "claude-sonnet-4-20250514"

# Maximum characters per short_description sent to Claude.
_DESC_TRUNCATE = 120

# Maximum number of active tickets to send (avoids extreme token counts).
_MAX_TICKETS = 800

_SYSTEM_PROMPT = """\
You are an IT service desk operations analyst. You will be given a list of \
active IT support tickets from a Hardware Repair queue, each with an incident \
number, short description, location, category, and age in days.

Your task is to identify NEW operational patterns or clusters of tickets that \
share a common root cause, hardware component, location issue, or process failure. \
Do NOT report patterns that are already covered by the existing alerts listed in \
the user message.

You MUST respond with a single valid JSON array and nothing else — no markdown, \
no prose, no code fences. Each element must have exactly these fields:
  "title":          short name for the pattern (≤ 60 chars)
  "description":    one sentence explaining the cluster and its operational impact
  "count":          integer — number of tickets in this cluster
  "ticket_numbers": list of up to 10 representative ticket numbers (strings)
  "severity":       one of "CRITICAL", "WARNING", or "MONITOR"

Severity guidance:
  CRITICAL  — active data loss, complete service outage, or safety risk
  WARNING   — degraded service or growing backlog requiring prompt action
  MONITOR   — noteworthy trend worth tracking; no immediate action needed

Return between 3 and 8 patterns. If you cannot find meaningful clusters beyond \
the existing alerts, return an empty array [].
"""


def _build_user_message(tickets: list[Ticket]) -> str:
    """Construct the user message sent to Claude."""
    active = [t for t in tickets if t.is_active][:_MAX_TICKETS]

    existing_alerts = (
        "EXISTING ALERTS (do NOT duplicate these):\n"
        "1. Tickets aged 180+ days\n"
        "2. Auto-resolve business rule failure (3+ notifications sent, still open)\n"
        "3. No assigned tech — active queue\n"
        "4. NCT vendor queue depth\n"
        "5. Taxonomy drift — misrouted categories (Remote Access, Software/App, etc.)\n"
        "6. Leadership-flagged tickets\n"
    )

    lines: list[str] = [
        existing_alerts,
        f"\nACTIVE TICKETS ({len(active)} records):\n",
        "number | location | category | age_days | short_description",
        "-" * 70,
    ]

    for t in active:
        desc = (t.short_description or "").strip()
        if len(desc) > _DESC_TRUNCATE:
            desc = desc[:_DESC_TRUNCATE] + "…"
        lines.append(
            f"{t.number} | {t.location} | {t.category.value} | "
            f"{t.age_days}d | {desc}"
        )

    return "\n".join(lines)


def _parse_response(raw: str) -> list[dict[str, Any]]:
    """Extract and validate the JSON array from Claude's response."""
    text = raw.strip()
    # Strip markdown code fences if Claude wraps anyway
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.startswith("```")
        ).strip()
    return json.loads(text)  # raises json.JSONDecodeError on bad output


def _to_pattern_alert(item: dict[str, Any]) -> PatternAlert:
    """Convert one Claude-returned dict to a PatternAlert model."""
    raw_severity = str(item.get("severity", "MONITOR")).upper()
    try:
        severity = AlertSeverity(raw_severity)
    except ValueError:
        severity = AlertSeverity.MONITOR

    tickets_preview = item.get("ticket_numbers", [])[:5]
    count = int(item.get("count", 0))

    ticket_str = (
        f"Sample tickets: {', '.join(str(n) for n in tickets_preview)}"
        if tickets_preview
        else ""
    )
    description = str(item.get("description", "")).strip()
    if ticket_str:
        description = f"{description} ({ticket_str})"

    return PatternAlert(
        severity=severity,
        title=str(item.get("title", "AI-detected pattern"))[:80],
        description=description or "Cluster detected by AI analysis.",
        count=count,
    )


def discover_patterns(tickets: list[Ticket], api_key: str) -> list[PatternAlert]:
    """Call Claude to discover operational patterns beyond the six hardcoded alerts.

    Args:
        tickets: Full ticket list (active tickets are extracted internally).
        api_key: Anthropic API key.

    Returns:
        List of PatternAlert objects, empty list if no patterns found or on error.

    Raises:
        anthropic.APIError: On unrecoverable API failures (caller should handle).
    """
    client = anthropic.Anthropic(api_key=api_key)
    user_message = _build_user_message(tickets)

    log.info(
        "ai_pattern_discovery_start",
        active_tickets=sum(1 for t in tickets if t.is_active),
        model=_MODEL,
    )

    response = client.messages.create(
        model=_MODEL,
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text if response.content else "[]"

    try:
        items = _parse_response(raw_text)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        log.warning("ai_pattern_discovery_parse_error", error=str(exc), raw=raw_text[:200])
        return [
            PatternAlert(
                severity=AlertSeverity.MONITOR,
                title="AI analysis — parse error",
                description=(
                    "Claude returned an unexpected response format. "
                    "Try running the analysis again."
                ),
                count=0,
            )
        ]

    patterns = [_to_pattern_alert(item) for item in items if isinstance(item, dict)]

    log.info("ai_pattern_discovery_complete", patterns_found=len(patterns))
    return patterns
