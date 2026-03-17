"""Tests for src/components/category_chart.py."""

from __future__ import annotations

import json

from src.components.category_chart import category_chart


class TestCategoryChart:
    def _cat_data(self) -> dict[str, int]:
        return {
            "Hardware": 638,
            "Remote Access": 22,
            "Software/App": 5,
            "Kiosk": 3,
            "Access/Security": 1,
            "Laptop": 1,
        }

    def test_returns_component(self) -> None:
        assert category_chart(self._cat_data()) is not None

    def test_has_correct_id(self) -> None:
        assert category_chart(self._cat_data()).id == "category-chart"

    def test_categories_in_serialized(self) -> None:
        serialized = json.dumps(category_chart(self._cat_data()).to_plotly_json())
        assert "Hardware" in serialized
        assert "Remote Access" in serialized

    def test_amber_flag_on_misrouted(self) -> None:
        serialized = json.dumps(category_chart(self._cat_data()).to_plotly_json())
        # Misrouted categories should use the warning/amber color
        assert "#e67e22" in serialized or "#f59e0b" in serialized
