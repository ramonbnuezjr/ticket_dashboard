"""Tests for src/data/loader.py — mock data generation and CSV loading."""

from __future__ import annotations

import csv
import tempfile
from datetime import timedelta
from pathlib import Path

import pytest

from src.data.loader import get_tickets, load_csv, load_mock_data
from src.data.models import TicketState


class TestLoadMockData:
    def test_returns_correct_total(self) -> None:
        tickets = load_mock_data()
        assert len(tickets) == 1102

    def test_state_distribution(self) -> None:
        tickets = load_mock_data()
        by_state = {}
        for t in tickets:
            by_state[t.state.value] = by_state.get(t.state.value, 0) + 1
        assert by_state["Assigned"] == 515
        assert by_state["Closed"] == 397
        assert by_state["OnHold"] == 168
        assert by_state["WorkInProgress"] == 13
        assert by_state["Resolved"] == 7
        assert by_state["Cancelled"] == 2

    def test_active_count(self) -> None:
        tickets = load_mock_data()
        active = [t for t in tickets if t.is_active]
        assert len(active) == 696

    def test_aged_180_plus(self) -> None:
        tickets = load_mock_data()
        aged = [t for t in tickets if t.is_active and t.age_days > 180]
        assert len(aged) == 373

    def test_vendor_hold_count(self) -> None:
        tickets = load_mock_data()
        vendor = [
            t for t in tickets
            if t.state == TicketState.OnHold and t.is_vendor_hold
        ]
        assert len(vendor) == 167

    def test_unassigned_count(self) -> None:
        tickets = load_mock_data()
        unassigned = [t for t in tickets if t.is_active and t.assigned_tech is None]
        assert len(unassigned) == 515

    def test_auto_resolve_fail_count(self) -> None:
        tickets = load_mock_data()
        arf = [t for t in tickets if t.is_active and t.notification_count >= 3]
        assert len(arf) == 19

    def test_leadership_flagged_count(self) -> None:
        tickets = load_mock_data()
        flagged = [t for t in tickets if t.is_leadership_flagged]
        assert len(flagged) == 6

    def test_specific_flagged_numbers_present(self) -> None:
        tickets = load_mock_data()
        numbers = {t.number for t in tickets}
        for expected in [
            "INC1784393",
            "INC1762166",
            "INC1728030",
            "INC1755669",
            "INC1806671",
            "INC1417433",
        ]:
            assert expected in numbers

    def test_all_tickets_are_valid_pydantic(self) -> None:
        tickets = load_mock_data()
        for t in tickets:
            assert t.number.startswith("INC")
            assert t.age_days >= 0

    def test_known_building_present(self) -> None:
        tickets = load_mock_data()
        locations = {t.location for t in tickets}
        assert "109 E 16th St" in locations

    def test_misclassified_count(self) -> None:
        from src.data.models import TicketCategory

        tickets = load_mock_data()
        misc = [
            t for t in tickets
            if t.is_active and t.category in TicketCategory.misrouted_categories()
        ]
        assert len(misc) == 29


class TestLoadCsv:
    """Tests for load_csv() using real ServiceNow export column names."""

    # Minimal set of columns needed to produce a valid Ticket.
    _SN_FIELDNAMES = [
        "number", "opened_by", "location", "state", "hold_reason",
        "category", "subcategory", "short_description", "description",
        "opened_at", "closed_at", "assignment_group", "u_opened_by_group",
        "assigned_to", "business_service", "u_notification_counter",
        "reassignment_count", "calendar_stc", "u_self_service_issue",
        "priority", "comments_and_work_notes", "approval_history",
        "close_code", "close_notes", "u_escalation_status", "resolved_at",
        "contact_type", "impact", "urgency", "severity", "u_self_service_issue_type",
    ]

    def _write_csv(self, rows: list[dict[str, str]], path: Path, delimiter: str = ",") -> None:
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self._SN_FIELDNAMES, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)

    def _valid_row(self, number: str = "INC9999999") -> dict[str, str]:
        """Return a minimal valid ServiceNow CSV row."""
        return {
            "number": number,
            "opened_by": "testuser",
            "location": "Building A",
            "state": "Assigned",
            "hold_reason": "",
            "category": "Hardware",
            "subcategory": "",
            "short_description": "Test hardware issue",
            "description": "",
            "opened_at": "2026-01-06 09:00:00",   # ~70 days before 2026-03-16
            "closed_at": "",
            "assignment_group": "ITS Service Desk Hardware Repair",
            "u_opened_by_group": "",
            "assigned_to": "J. Smith",
            "business_service": "",
            "u_notification_counter": "0",
            "reassignment_count": "0",
            "calendar_stc": "",
            "u_self_service_issue": "",
            "priority": "3",
            "comments_and_work_notes": "",
            "approval_history": "",
            "close_code": "",
            "close_notes": "",
            "u_escalation_status": "",
            "resolved_at": "",
            "contact_type": "",
            "impact": "3",
            "urgency": "3",
            "severity": "3",
            "u_self_service_issue_type": "",
        }

    def test_loads_valid_csv(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        self._write_csv([self._valid_row("INC9000001"), self._valid_row("INC9000002")], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert len(tickets) == 2
        assert tickets[0].number == "INC9000001"
        tmp_path.unlink()

    def test_maps_assigned_to_field(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        self._write_csv([self._valid_row()], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].assigned_tech == "J. Smith"
        tmp_path.unlink()

    def test_maps_empty_assigned_to_none(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["assigned_to"] = ""
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].assigned_tech is None
        tmp_path.unlink()

    def test_maps_on_hold_state(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["state"] = "On Hold"
        self._write_csv([row], tmp_path)
        from src.data.models import TicketState
        tickets = load_csv(str(tmp_path))
        assert tickets[0].state == TicketState.OnHold
        tmp_path.unlink()

    def test_vendor_hold_detected_from_hold_reason(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["state"] = "On Hold"
        row["hold_reason"] = "Awaiting NCT vendor response"
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].is_vendor_hold is True
        tmp_path.unlink()

    def test_vendor_hold_false_when_not_on_hold(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["state"] = "Assigned"
        row["hold_reason"] = "NCT vendor"
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].is_vendor_hold is False
        tmp_path.unlink()

    def test_leadership_flagged_from_escalation_status(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["u_escalation_status"] = "Management Escalation"
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].is_leadership_flagged is True
        tmp_path.unlink()

    def test_leadership_not_flagged_when_normal(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["u_escalation_status"] = "Normal"
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].is_leadership_flagged is False
        tmp_path.unlink()

    def test_notification_counter_mapped(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["u_notification_counter"] = "3"
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].notification_count == 3
        tmp_path.unlink()

    def test_short_description_mapped(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["short_description"] = "Printer not found"
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].short_description == "Printer not found"
        tmp_path.unlink()

    def test_age_computed_from_opened_at(self) -> None:
        from datetime import date as _date
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        # Set opened_at to exactly 30 days ago
        thirty_ago = (_date.today() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        row["opened_at"] = thirty_ago
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].age_days == 30
        tmp_path.unlink()

    def test_age_fallback_to_calendar_stc(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["opened_at"] = ""
        row["calendar_stc"] = str(10 * 86400)  # 10 days in seconds
        self._write_csv([row], tmp_path)
        tickets = load_csv(str(tmp_path))
        assert tickets[0].age_days == 10
        tmp_path.unlink()

    def test_unknown_category_maps_to_other(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["category"] = "Some Unknown Category"
        self._write_csv([row], tmp_path)
        from src.data.models import TicketCategory
        tickets = load_csv(str(tmp_path))
        assert tickets[0].category == TicketCategory.Other
        tmp_path.unlink()

    def test_tab_delimited_file_loads(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".tsv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        self._write_csv([self._valid_row("INC7000001")], tmp_path, delimiter="\t")
        tickets = load_csv(str(tmp_path))
        assert len(tickets) == 1
        assert tickets[0].number == "INC7000001"
        tmp_path.unlink()

    def test_rejects_invalid_state(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
            tmp_path = Path(tf.name)
        row = self._valid_row()
        row["state"] = "INVALID_STATE_XYZ"
        self._write_csv([row], tmp_path)
        with pytest.raises(ValueError):
            load_csv(str(tmp_path))
        tmp_path.unlink()

    def test_rejects_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_csv("/nonexistent/path/data.csv")


class TestGetTickets:
    def test_uses_mock_when_path_not_set(self) -> None:
        from unittest.mock import MagicMock

        mock_settings = MagicMock()
        mock_settings.data_csv_path = None
        tickets = get_tickets(mock_settings)
        assert len(tickets) == 1102

    def test_uses_csv_when_path_set(self) -> None:
        import csv as csv_mod
        import tempfile
        from pathlib import Path
        from unittest.mock import MagicMock

        sn_fieldnames = [
            "number", "opened_by", "location", "state", "hold_reason",
            "category", "subcategory", "short_description", "description",
            "opened_at", "closed_at", "assignment_group", "u_opened_by_group",
            "assigned_to", "business_service", "u_notification_counter",
            "reassignment_count", "calendar_stc", "u_self_service_issue",
            "priority", "comments_and_work_notes", "approval_history",
            "close_code", "close_notes", "u_escalation_status", "resolved_at",
            "contact_type", "impact", "urgency", "severity",
            "u_self_service_issue_type",
        ]
        row = {f: "" for f in sn_fieldnames}
        row.update({
            "number": "INC8888888",
            "state": "Assigned",
            "category": "Hardware",
            "location": "Building Z",
            "assigned_to": "T. Test",
            "opened_at": "2026-01-01 08:00:00",
        })
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False, newline="") as tf:
            writer = csv_mod.DictWriter(tf, fieldnames=sn_fieldnames)
            writer.writeheader()
            writer.writerow(row)
            tmp_path = Path(tf.name)

        mock_settings = MagicMock()
        mock_settings.data_csv_path = str(tmp_path)
        tickets = get_tickets(mock_settings)
        assert len(tickets) == 1
        assert tickets[0].number == "INC8888888"
        assert tickets[0].assigned_tech == "T. Test"
        tmp_path.unlink()
