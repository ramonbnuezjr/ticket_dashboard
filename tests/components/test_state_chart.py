"""Tests for src/components/state_chart.py."""

from __future__ import annotations

import json

from src.components.state_chart import state_chart


class TestStateChart:
    def _state_data(self) -> dict[str, int]:
        return {"Assigned": 515, "Closed": 397, "OnHold": 168, "WorkInProgress": 13}

    def _monthly_data(self) -> dict[str, int]:
        return {
            "2025-03": 80, "2025-04": 63, "2025-05": 67, "2025-06": 62,
            "2025-07": 58, "2025-08": 69, "2025-09": 73, "2025-10": 78,
            "2025-11": 81, "2025-12": 83, "2026-01": 81, "2026-02": 74,
        }

    def test_returns_component(self) -> None:
        component = state_chart(self._state_data(), self._monthly_data())
        assert component is not None

    def test_has_correct_id(self) -> None:
        component = state_chart(self._state_data(), self._monthly_data())
        assert component.id == "state-chart-row"

    def test_contains_two_children(self) -> None:
        component = state_chart(self._state_data(), self._monthly_data())
        assert len(component.children) == 2

    def test_state_labels_in_serialized(self) -> None:
        component = state_chart(self._state_data(), self._monthly_data())
        serialized = json.dumps(component.to_plotly_json())
        assert "Assigned" in serialized

    def test_monthly_labels_in_serialized(self) -> None:
        component = state_chart(self._state_data(), self._monthly_data())
        serialized = json.dumps(component.to_plotly_json())
        assert "2025-03" in serialized
