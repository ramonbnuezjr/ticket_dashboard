"""Tests for src/components/age_chart.py."""

from __future__ import annotations

import json

from src.components.age_chart import age_chart


class TestAgeChart:
    def _age_data(self) -> dict[str, int]:
        return {
            "0-30d": 101,
            "31-90d": 120,
            "91-180d": 102,
            "181-365d": 252,
            "365+d": 121,
        }

    def test_returns_component(self) -> None:
        assert age_chart(self._age_data()) is not None

    def test_has_correct_id(self) -> None:
        assert age_chart(self._age_data()).id == "age-chart"

    def test_buckets_in_serialized(self) -> None:
        serialized = json.dumps(age_chart(self._age_data()).to_plotly_json())
        assert "181-365d" in serialized

    def test_values_in_serialized(self) -> None:
        serialized = json.dumps(age_chart(self._age_data()).to_plotly_json())
        assert "252" in serialized
