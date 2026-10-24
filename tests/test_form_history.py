"""Tests for saved-form suggestions and common field validation."""
import tempfile
import unittest
from pathlib import Path
from engine.form_history import append_form_history, history_suggestions, validate_mobile, validate_date


class FormHistoryTests(unittest.TestCase):
    def test_cross_template_name_suggestions_and_deduplication(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "history.json"
            append_form_history(path, "Affidavit A", {"applicant_full_name": "राम पाटील", "affidavit_date": "24/10/2026"})
            append_form_history(path, "Affidavit B", {"applicant_full_name": "सीता जाधव"})
            append_form_history(path, "Affidavit C", {"applicant_full_name": "राम पाटील"})
            self.assertEqual(history_suggestions(path, "applicant_full_name"), ["राम पाटील", "सीता जाधव"])

    def test_mobile_validation(self):
        self.assertTrue(validate_mobile("9876543210"))
        self.assertTrue(validate_mobile("+91 98765 43210"))
        self.assertFalse(validate_mobile("12345"))
        self.assertFalse(validate_mobile("1234567890"))
        self.assertTrue(validate_mobile(""))

    def test_date_validation(self):
        self.assertTrue(validate_date("24/10/2026"))
        self.assertTrue(validate_date("2026-10-24"))
        self.assertFalse(validate_date("31/02/2026"))
        self.assertTrue(validate_date(""))

    def test_clear_form_history_deletes_local_history(self):
        from engine.form_history import clear_form_history
        with tempfile.TemporaryDirectory() as td:
            history_file = Path(td) / "history.json"
            append_form_history(history_file, "Template", {"applicant_full_name": "राम"})
            self.assertTrue(history_file.exists())
            self.assertTrue(clear_form_history(history_file))
            self.assertFalse(history_file.exists())



if __name__ == "__main__":
    unittest.main()
