"""Tests for src/components/heatmap.py."""

from __future__ import annotations

import json
from typing import Any

from src.components.heatmap import heatmap_section


def _locations() -> list[dict[str, Any]]:
    return [
        {"location": "109 E 16th St", "total": 136, "pct_active": 68.0, "avg_age": 95.0, "on_hold_count": 12},
        {"location": "375 Pearl St", "total": 78, "pct_active": 55.0, "avg_age": 110.0, "on_hold_count": 8},
        {"location": "890 Garrison Ave", "total": 68, "pct_active": 76.0, "avg_age": 130.0, "on_hold_count": 10},
    ]


class TestHeatmapSection:
    def test_returns_component(self) -> None:
        assert heatmap_section(_locations()) is not None

    def test_has_correct_id(self) -> None:
        assert heatmap_section(_locations()).id == "heatmap-section"

    def test_location_names_in_serialized(self) -> None:
        serialized = json.dumps(heatmap_section(_locations()).to_plotly_json())
        assert "109 E 16th St" in serialized

    def test_toggle_buttons_present(self) -> None:
        serialized = json.dumps(heatmap_section(_locations()).to_plotly_json())
        assert "% active open" in serialized
        assert "avg age" in serialized or "avg_age" in serialized

    def test_treemap_graph_present(self) -> None:
        serialized = json.dumps(heatmap_section(_locations()).to_plotly_json())
        assert "heatmap-treemap" in serialized

    def test_empty_locations_renders(self) -> None:
        assert heatmap_section([]) is not None
