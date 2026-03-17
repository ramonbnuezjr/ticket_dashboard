"""Tests for src/components/kpi_strip.py."""

from __future__ import annotations

from src.components.kpi_strip import kpi_strip
from src.data.models import KpiData


def _make_kpi(**overrides: object) -> KpiData:
    defaults: dict[str, object] = {
        "total": 1102,
        "active_open": 696,
        "active_pct": 63.2,
        "vendor_queue": 167,
        "unassigned": 515,
        "misclassified": 29,
        "auto_resolve_fail": 19,
    }
    defaults.update(overrides)
    return KpiData(**defaults)  # type: ignore[arg-type]


class TestKpiStrip:
    def test_returns_a_component(self) -> None:
        component = kpi_strip(_make_kpi())
        assert component is not None

    def test_component_has_id(self) -> None:
        component = kpi_strip(_make_kpi())
        assert component.id == "kpi-strip"

    def test_contains_six_cards(self) -> None:
        component = kpi_strip(_make_kpi())
        # Children are the 6 KPI card columns; check there are 6 by
        # inspecting the outer row's children length.
        assert len(component.children) == 6

    def test_total_value_present(self) -> None:
        import json

        component = kpi_strip(_make_kpi(total=9999))
        serialized = json.dumps(component.to_plotly_json())
        assert "9999" in serialized or "9,999" in serialized

    def test_active_pct_rendered(self) -> None:
        import json

        component = kpi_strip(_make_kpi(active_pct=63.2))
        serialized = json.dumps(component.to_plotly_json())
        assert "63.2" in serialized
