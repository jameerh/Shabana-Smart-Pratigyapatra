"""Tests for local-first workspace utilities."""
import tempfile
import unittest
from pathlib import Path

from engine.workspace_services import (
    save_applicant_profile, load_applicant_profile, snapshot_template,
    list_template_snapshots, validate_required_fields, compare_text_documents,
    export_profile_settings, load_profile_settings,
)


class WorkspaceServiceTests(unittest.TestCase):
    def test_profile_round_trip_unicode(self):
        with tempfile.TemporaryDirectory() as td:
            saved = save_applicant_profile(td, "अर्जदार राम", {
                "applicant_full_name": "राम शंकर",
                "applicant_age": 42,
            })
            values = load_applicant_profile(saved)
            self.assertEqual(values["applicant_full_name"], "राम शंकर")
            self.assertEqual(values["applicant_age"], "42")

    def test_profile_rejects_empty_name(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                save_applicant_profile(td, "  ", {"name": "test"})

    def test_template_snapshot_is_content_addressed_and_listed(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.docx"
            source.write_bytes(b"docx bytes")
            history = Path(td) / "history"
            first = snapshot_template(source, history, "Affidavit")
            second = snapshot_template(source, history, "Affidavit")
            self.assertEqual(first, second)
            self.assertIn(first, list_template_snapshots(history, "Affidavit"))
            self.assertTrue(first.with_suffix(first.suffix + ".json").exists())

    def test_required_field_validation(self):
        self.assertEqual(
            validate_required_fields({"name": "Ram", "date": " "}, ["name", "date"]),
            ["date"],
        )

    def test_document_comparison_reports_changes(self):
        result = compare_text_documents("heading\nold line", "heading\nnew line")
        self.assertLess(result["similarity_percent"], 100)
        self.assertTrue(result["added_lines"])
        self.assertTrue(result["removed_lines"])
        self.assertIn("new line", result["unified_diff"])

    def test_export_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            export_profile_settings(path, {"font": "Mangal", "page_size": "A4"})
            self.assertEqual(load_profile_settings(path)["font"], "Mangal")


if __name__ == "__main__":
    unittest.main()
