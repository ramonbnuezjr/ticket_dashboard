"""Dashboard component library.

Color constants are defined here and shared across all components so the
visual language is consistent and easy to update from a single location.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Severity colors (match the screenshots exactly)
# ---------------------------------------------------------------------------
COLOR_CRITICAL = "#e74c3c"
COLOR_WARNING = "#e67e22"
COLOR_MONITOR = "#3498db"
COLOR_IMMEDIATE = "#f39c12"
COLOR_GOOD = "#27ae60"

# ---------------------------------------------------------------------------
# Background / surface
# ---------------------------------------------------------------------------
COLOR_BG = "#111827"
COLOR_SURFACE = "#1f2937"
COLOR_SURFACE_2 = "#374151"
COLOR_BORDER = "#374151"

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------
COLOR_TEXT_PRIMARY = "#f9fafb"
COLOR_TEXT_MUTED = "#9ca3af"

# ---------------------------------------------------------------------------
# Chart template
# ---------------------------------------------------------------------------
PLOTLY_TEMPLATE = "plotly_dark"

# ---------------------------------------------------------------------------
# Severity → color mapping (keyed by AlertSeverity.value)
# ---------------------------------------------------------------------------
SEVERITY_COLORS: dict[str, str] = {
    "CRITICAL": COLOR_CRITICAL,
    "WARNING": COLOR_WARNING,
    "MONITOR": COLOR_MONITOR,
    "IMMEDIATE": COLOR_IMMEDIATE,
}
