"""Tests for src/components/kpi_strip.py."""

from __future__ import annotations

import pytest

from src.components.kpi_strip import kpi_strip
from src.data.models import KpiData

_EXPECTED_CARD_IDS = [
    "kpi-card-total",
    "kpi-card-active_open",
    "kpi-card-vendor_queue",
    "kpi-card-unassigned",
    "kpi-card-misclassified",
    "kpi-card-auto_resolve_fail",
]


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
        assert len(component.children) == 6

    def test_total_value_present(self) -> None:
        component = kpi_strip(_make_kpi(total=9999))
        serialized = str(component.to_plotly_json())
        assert "9999" in serialized or "9,999" in serialized

    def test_active_pct_rendered(self) -> None:
        component = kpi_strip(_make_kpi(active_pct=63.2))
        serialized = str(component.to_plotly_json())
        assert "63.2" in serialized

    def test_all_cards_have_ids(self) -> None:
        component = kpi_strip(_make_kpi())
        card_ids = [card.id for card in component.children]
        assert card_ids == _EXPECTED_CARD_IDS

    def test_all_cards_have_n_clicks(self) -> None:
        component = kpi_strip(_make_kpi())
        for card in component.children:
            assert hasattr(card, "n_clicks"), f"Card {card.id} missing n_clicks"
            assert card.n_clicks == 0

    def test_cards_have_cursor_pointer(self) -> None:
        component = kpi_strip(_make_kpi())
        for card in component.children:
            assert card.style.get("cursor") == "pointer", f"Card {card.id} missing cursor:pointer"

    @pytest.mark.parametrize("card_id", _EXPECTED_CARD_IDS)
    def test_each_expected_card_id_present(self, card_id: str) -> None:
        component = kpi_strip(_make_kpi())
        ids = [c.id for c in component.children]
        assert card_id in ids

    def test_drill_hint_text_present(self) -> None:
        component = kpi_strip(_make_kpi())
        serialized = str(component.to_plotly_json())
        assert "click to view" in serialized
