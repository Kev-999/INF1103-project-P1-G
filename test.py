import json
import os
import tempfile
import unittest

import data_manager as dm
from logic_manager import validate_amount, validate_description, analyse_spending

CATEGORIES = ["Food", "Drinks", "Transport", "Entertainment", "Education Materials", "Other"]


def rec(amount, budget, category="Food", description="Item", date="2026-10-02"):
    """Build a sample expense record (category mimics the AI response)."""
    return {"date": date, "description": description, "amount": amount,
            "budget": budget, "ai_response": category}


class TestValidateAmount(unittest.TestCase):
    def check(self, cases):
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(validate_amount(value), expected)

    def test_valid(self):
        self.check({"12.50": 12.5, "100": 100.0, " 7 ": 7.0, "0": 0.0, "1e2": 100.0})

    def test_negative(self):
        self.check({"-5": "Negative", "-0.01": "Negative"})

    def test_invalid(self):
        self.check({v: "Invalid" for v in ["abc", "", "   ", "12,50", "$10", "1 2", "5kg", "--5"]})

    def test_quit(self):
        self.check({v: "quit" for v in ["quit", "QUIT", "Quit"]})


class TestValidateDescription(unittest.TestCase):
    def test_all_cases(self):
        cases = {
            "Coffee": "Coffee", "  Lunch  ": "Lunch", "TV": "TV",
            "Lunch at McDonald's": "Lunch at McDonald's",
            "": "Empty", "    ": "Empty",
            "a": "Short", "  a  ": "Short",
            "quit": "quit", "  QUIT ": "quit",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(validate_description(value), expected)


class TestAnalyseSpending(unittest.TestCase):
    # Hardcoded sample AI categories (None / "" = AI failed or returned nothing)
    SAMPLE = [
        rec(4.50, 5.00, "Food"), rec(8.20, 7.00, "Food"), rec(6.50, 5.00, "Drinks"),
        rec(20.00, 15.00, "Transport"), rec(15.00, 20.00, "Entertainment"),
        rec(40.00, 50.00, "Education Materials"), rec(12.00, 12.00, "Other"),
        rec(3.30, 5.00, None), rec(1.00, 5.00, ""),
    ]

    def test_full_summary(self):
        before = [dict(r) for r in self.SAMPLE]
        result = analyse_spending(self.SAMPLE)
        self.assertEqual(result["Number of expenses"], 9)
        self.assertEqual(result["Total spent"], 110.50)
        self.assertEqual(result["Average per expense"], 12.28)
        self.assertEqual(result["Over budget count"], 3)
        self.assertEqual(result["Spending by category"], {
            "Food": 12.7, "Drinks": 6.5, "Transport": 20.0, "Entertainment": 15.0,
            "Education Materials": 40.0, "Other": 12.0, "Uncategorised": 4.3})
        self.assertEqual(self.SAMPLE, before)  # input not modified

    def test_every_category_grouped(self):
        result = analyse_spending([rec(1.0, 5.0, c) for c in CATEGORIES])
        self.assertEqual(set(result["Spending by category"]), set(CATEGORIES))

    def test_empty(self):
        self.assertEqual(analyse_spending([]), {
            "Number of expenses": 0, "Total spent": 0, "Average per expense": 0,
            "Over budget count": 0, "Spending by category": {}})

    def test_single_record(self):
        result = analyse_spending([rec(9.99, 10.0)])
        self.assertEqual((result["Total spent"], result["Average per expense"]), (9.99, 9.99))

    def test_missing_ai_response_key(self):
        result = analyse_spending([{"amount": 4.0, "budget": 10.0}])
        self.assertEqual(result["Spending by category"], {"Uncategorised": 4.0})

    def test_budget_boundary(self):
        self.assertEqual(analyse_spending([rec(10.0, 10.0)])["Over budget count"], 0)
        self.assertEqual(analyse_spending([rec(10.01, 10.0)])["Over budget count"], 1)

    def test_float_rounding(self):
        result = analyse_spending([rec(0.1, 1, "Other"), rec(0.2, 1, "Other")])
        self.assertEqual(result["Total spent"], 0.3)
        self.assertEqual(result["Spending by category"], {"Other": 0.3})


class TestDataCleaning(unittest.TestCase):
    GOOD = {"id": 1, "date": "2026-10-02", "description": " Lunch ",
            "amount": "12.504", "budget": 20, "ai_response": "Food"}

    def test_dates(self):
        for ok in ["2026-10-02", "2024-02-29", "2000-02-29"]:
            self.assertTrue(dm.is_valid_date(ok), ok)
        for bad in ["2026-13-01", "2026-02-30", "2023-02-29", "1900-02-29",
                    "2026/10/02", "2026-1-02", "", None, 20261002]:
            self.assertFalse(dm.is_valid_date(bad), bad)

    def test_to_money(self):
        self.assertEqual(dm.to_money("12.504"), 12.5)
        for bad in [-1, "abc", "nan", "inf", 1e12]:
            with self.assertRaises(ValueError, msg=bad):
                dm.to_money(bad)

    def test_clean_record_normalises(self):
        record = dm.clean_record(self.GOOD)
        self.assertEqual((record["description"], record["amount"]), ("Lunch", 12.5))
        no_ai = {k: v for k, v in self.GOOD.items() if k != "ai_response"}
        self.assertEqual(dm.clean_record(no_ai)["ai_response"], "")

    def test_clean_record_rejects_bad_data(self):
        bad_rows = [{**self.GOOD, "amount": 0}, {**self.GOOD, "amount": -3},
                    {**self.GOOD, "description": "  "}, {**self.GOOD, "date": "2026-02-30"},
                    {**self.GOOD, "budget": "abc"}, {"id": 1}, None]
        for row in bad_rows:
            self.assertIsNone(dm.clean_record(row), row)


class TestDataRecords(unittest.TestCase):
    def test_ids(self):
        history = []
        for _ in range(2):
            dm.add_record(history, rec(4.5, 5.0))
        self.assertEqual([r["id"] for r in history], [1, 2])
        self.assertEqual(dm.get_next_id([{"id": 7}, {"id": 3}]), 8)

    def test_rejects_invalid(self):
        history = []
        self.assertIsNone(dm.add_record(history, rec(-1, 5)))
        self.assertIsNone(dm.add_record(history, "not a dict"))
        added, rejected = dm.add_records(history, [rec(4, 5), rec(0, 5), rec(4, 5, description="")])
        self.assertEqual((len(added), rejected, len(history)), (1, 2, 1))

    def test_query(self):
        h = []
        dm.add_records(h, [rec(4.5, 5, "Food", "Chicken rice", "2026-10-01"),
                           rec(6.5, 5, "Drinks", "Bubble tea", "2026-10-02"),
                           rec(20, 15, "Transport", "MRT top-up", "2026-10-03")])
        counts = {
            len(dm.query(h, description="TEA")): 1,
            len(dm.query(h, date_from="2026-10-02")): 2,
            len(dm.query(h, date_to="2026-10-01")): 1,
            len(dm.query(h, min_amount=5, max_amount=10)): 1,
            len(dm.query(h, over_budget=True)): 2,
            len(dm.query(h, over_budget=False)): 1,
            len(dm.query(h)): 3,
            len(dm.query(h, over_budget=True, date_from="2026-10-03")): 1,
            len(dm.query(h, record_id=99)): 0,
        }
        self.assertTrue(all(k == v for k, v in counts.items()), counts)
        self.assertEqual(dm.query(h, record_id=3)[0]["description"], "MRT top-up")


class TestDataStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "data", "spending.json")

    def tearDown(self):
        dm.full_history.clear()
        self.tmp.cleanup()

    def write(self, content):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            f.write(content)

    def test_round_trip(self):
        history = []
        dm.add_record(history, rec(8.5, 10, description="Lunch"))
        self.assertIsNone(dm.save_history(history, self.path))
        self.assertEqual(dm.load_history(self.path), (history, []))

    def test_missing_file(self):
        self.assertEqual(dm.load_history(self.path), ([], []))

    def test_corrupted_file_backed_up(self):
        for content in ["{ not json", json.dumps({"not": "a list"})]:
            self.write(content)
            loaded, warnings = dm.load_history(self.path)
            self.assertEqual(loaded, [])
            self.assertIn("corrupted", warnings[0])
            self.assertTrue(os.path.exists(self.path + ".corrupted"))

    def test_bad_records_skipped(self):
        good = {"id": 1, "date": "2026-10-02", "description": "Lunch", "amount": 5, "budget": 10}
        self.write(json.dumps([good, {**good, "id": 2, "date": "bad"}, {"id": 3}]))
        loaded, warnings = dm.load_history(self.path)
        self.assertEqual(len(loaded), 1)
        self.assertIn("Skipped 2", warnings[0])


class TestAIPipeline(unittest.TestCase):
    """Hardcoded raw AI JSON flows through data_manager into the analysis."""
    AI_RESPONSES = [("Chicken rice", 4.5, 5, '{"category": "Food"}'),
                    ("Bubble tea", 6.5, 5, '{"category": "Drinks"}'),
                    ("Grab to school", 12, 10, '{"category": "Transport"}'),
                    ("Calculator", 25, 30, '{"category": "Education Materials"}'),
                    ("Haircut", 15, 15, '{"category": "Other"}')]

    def test_ai_categories_reach_analysis(self):
        history = []
        for description, amount, budget, ai_json in self.AI_RESPONSES:
            category = json.loads(ai_json)["category"]
            self.assertIn(category, CATEGORIES)
            self.assertIsNotNone(dm.add_record(history, rec(amount, budget, category, description)))
        result = analyse_spending(history)
        self.assertEqual((result["Number of expenses"], result["Total spent"],
                          result["Over budget count"]), (5, 63.0, 2))
        self.assertEqual(result["Spending by category"], {
            "Food": 4.5, "Drinks": 6.5, "Transport": 12.0, "Education Materials": 25.0, "Other": 15.0})

    def test_failed_ai_call_is_uncategorised(self):
        history = []
        dm.add_record(history, rec(3.0, 5.0, "Uncategorised", "Mystery"))
        self.assertEqual(analyse_spending(history)["Spending by category"], {"Uncategorised": 3.0})


if __name__ == "__main__":
    unittest.main(verbosity=2)