"""Regression tests for generic affidavit template registration and date fields."""
import unittest

from templates import TEMPLATES


class GenericAffidavitTemplateTests(unittest.TestCase):
    def test_four_generic_affidavits_are_registered(self):
        expected = {
            "Anna Suraksha Eligibility Affidavit",
            "No Kerosene License or Fuel Pump Affidavit",
            "No Essential Commodities Act Action Affidavit",
            "No Employment or Private Company Membership Affidavit",
        }
        self.assertTrue(expected.issubset(TEMPLATES.keys()))

    def test_every_generic_affidavit_has_date_field_and_placeholder(self):
        names = [
            "Anna Suraksha Eligibility Affidavit",
            "No Kerosene License or Fuel Pump Affidavit",
            "No Essential Commodities Act Action Affidavit",
            "No Employment or Private Company Membership Affidavit",
        ]
        for name in names:
            with self.subTest(template=name):
                item = TEMPLATES[name]
                self.assertIn("affidavit_date", item["fields"])
                self.assertIn("{affidavit_date}", item["template"])
                self.assertIn("gender", item["fields"])


if __name__ == "__main__":
    unittest.main()
