import logging
import unittest

logging.disable(logging.CRITICAL)   

import data_manager as dm
from ai_manager import (CATEGORIES, AIManager, AIUnavailableError, FallbackProvider,
                        GeminiProvider, MockProvider)
from logic_manager import InputValidator, LogicManager


def rec(amount, budget, category="Food", description="Item", date="2026-10-02"):
    """A sample expense entry; `category` mimics the AI response."""
    return {"date": date, "description": description, "amount": amount,
            "budget": budget, "ai_response": category}


def expense(amount, budget, category="Food", description="Item", date="2026-10-02"):
    return dm.Expense.from_raw({"id": 1, **rec(amount, budget, category, description, date)})


class TestInputValidator(unittest.TestCase):
    def setUp(self):
        self.v = InputValidator()

    def test_amount(self):
        cases = {"12.50": 12.5, "100": 100.0, " 7 ": 7.0, "0": 0.0,
                 "-5": "Negative", "abc": "Invalid", "": "Invalid", "$10": "Invalid",
                 "quit": "quit", "QUIT": "quit"}
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(self.v.validate_amount(value), expected)

    def test_description(self):
        cases = {"Coffee": "Coffee", "  Lunch  ": "Lunch", "TV": "TV",
                 "": "Empty", "   ": "Empty", "a": "Short", "  QUIT ": "quit"}
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(self.v.validate_description(value), expected)

    def test_category_choice(self):
        self.assertEqual(self.v.validate_category_choice("1", CATEGORIES), "Food")
        self.assertEqual(self.v.validate_category_choice(" 6 ", CATEGORIES), "Other")
        for bad in ["0", "7", "x", ""]:
            self.assertEqual(self.v.validate_category_choice(bad, CATEGORIES), "Invalid")


class TestLogicManager(unittest.TestCase):
    def setUp(self):
        self.logic = LogicManager(confidence_threshold=0.6)

    def test_needs_manual_category(self):
        ai = AIManager(MockProvider('{"category": "Food", "confidence": 0.9}'))
        self.assertFalse(self.logic.needs_manual_category(ai.categorize("Lunch", 5)))
        ai = AIManager(MockProvider('{"category": "Food", "confidence": 0.3}'))
        self.assertTrue(self.logic.needs_manual_category(ai.categorize("Lunch", 5)))
        self.assertTrue(self.logic.needs_manual_category(None))

    def test_full_summary(self):
        sample = [expense(4.50, 5.00, "Food"), expense(8.20, 7.00, "Food"),
                  expense(6.50, 5.00, "Drinks"), expense(20.00, 15.00, "Transport"),
                  expense(15.00, 20.00, "Entertainment"),
                  expense(40.00, 50.00, "Education Materials"),
                  expense(12.00, 12.00, "Other"), expense(3.30, 5.00, None),
                  expense(1.00, 5.00, "")]
        result = self.logic.analyse_spending(sample)
        self.assertEqual(result["Number of expenses"], 9)
        self.assertEqual(result["Total spent(all time)"], 110.50)
        self.assertEqual(result["Average per expense"], 12.28)
        self.assertEqual(result["Over budget count"], 3)
        self.assertEqual(result["Spending by category"], {
            "Food": 12.7, "Drinks": 6.5, "Transport": 20.0, "Entertainment": 15.0,
            "Education Materials": 40.0, "Other": 12.0, "Uncategorised": 4.3})

    def test_empty(self):
        self.assertEqual(self.logic.analyse_spending([]), {
            "Number of expenses": 0, "Total spent(all time)": 0, "Average per expense": 0,
            "Over budget count": 0, "Spending by category": {}, "Time-Limited Targets": []})

    def test_budget_boundary(self):
        self.assertEqual(self.logic.analyse_spending([expense(10.0, 10.0)])["Over budget count"], 0)
        self.assertEqual(self.logic.analyse_spending([expense(10.01, 10.0)])["Over budget count"], 1)

    def test_float_rounding(self):
        result = self.logic.analyse_spending([expense(0.1, 1, "Other"), expense(0.2, 1, "Other")])
        self.assertEqual(result["Total spent(all time)"], 0.3)
        self.assertEqual(result["Spending by category"], {"Other": 0.3})

    def test_time_targets(self):
        target = dm.TimeTarget(1, "Week", 20.0, "2026-10-01", "2026-10-07")
        records = [expense(15.0, 20.0, date="2026-10-02"), expense(10.0, 20.0, date="2026-10-05"),
                   expense(99.0, 20.0, date="2026-11-01")]  # outside the range
        [summary] = self.logic.analyse_spending(records, [target])["Time-Limited Targets"]
        self.assertEqual((summary["spent"], summary["remaining"], summary["is_over"]),
                         (25.0, -5.0, True))


class TestAIManagerOffline(unittest.TestCase):
    """Hardcoded AI responses only; nothing here touches the network."""

    def categorize(self, raw):
        return AIManager(MockProvider(raw)).categorize("Chicken rice", 4.5)

    def test_valid_response(self):
        result = self.categorize('{"category": "Food", "confidence": 0.95}')
        self.assertEqual((result.category, result.confidence, result.model), ("Food", 0.95, "mock"))

    def test_bad_responses_return_none(self):
        for raw in ['not json', '[]', '{"category": "Pets", "confidence": 0.9}',
                    '{"category": "Food", "confidence": 1.5}',
                    '{"category": "Food", "confidence": true}', '{"category": "Food"}']:
            with self.subTest(raw=raw):
                self.assertIsNone(self.categorize(raw))

    def test_provider_failure_returns_none(self):
        ai = AIManager(MockProvider(error=AIUnavailableError("down")))
        self.assertIsNone(ai.categorize("Lunch", 5))

    def test_no_api_key_is_unavailable(self):
        with self.assertRaises(AIUnavailableError):
            GeminiProvider("gemini", api_key=None).generate("x")

    def test_fallback_uses_next_provider(self):
        fallback = FallbackProvider([MockProvider(error=AIUnavailableError("busy")),
                                     MockProvider('{"category": "Drinks", "confidence": 0.8}')])
        result = AIManager(fallback).categorize("Bubble tea", 6.5)
        self.assertEqual((result.category, result.model), ("Drinks", "mock"))

    def test_every_category_accepted(self):
        for c in CATEGORIES:
            self.assertEqual(self.categorize(f'{{"category": "{c}", "confidence": 0.7}}').category, c)


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

    def test_expense_from_raw(self):
        e = dm.Expense.from_raw(self.GOOD)
        self.assertEqual((e.description, e.amount, e.over_budget), ("Lunch", 12.5, False))
        self.assertEqual(dm.Expense.from_raw({**self.GOOD, "ai_response": None}).ai_response, "")
        for row in [{**self.GOOD, "amount": 0}, {**self.GOOD, "amount": -3},
                    {**self.GOOD, "description": "  "}, {**self.GOOD, "date": "2026-02-30"},
                    {**self.GOOD, "budget": "abc"}, {"id": 1}, None]:
            self.assertIsNone(dm.Expense.from_raw(row), row)

    def test_time_target_from_raw(self):
        raw = {"target_id": 1, "name": "Week", "target_amount": 50,
               "start_date": "2026-10-01", "end_date": "2026-10-07"}
        self.assertIsNotNone(dm.TimeTarget.from_raw(raw))
        self.assertIsNone(dm.TimeTarget.from_raw({**raw, "end_date": "2026-09-30"}))
        self.assertIsNone(dm.TimeTarget.from_raw({**raw, "start_date": "bad"}))


class TestExpenseTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = dm.ExpenseTracker(":memory:")   # fresh in-memory database
        self.assertEqual(self.tracker.load(), [])

    def tearDown(self):
        self.tracker.close()

    def test_add_and_ids(self):
        first = self.tracker.add_expense(rec(4.5, 5.0))
        second = self.tracker.add_expense(rec(6.5, 5.0, "Drinks"))
        self.assertEqual((first.id, second.id), (1, 2))
        self.assertEqual(self.tracker.find_by_id(2).ai_response, "Drinks")

    def test_rejects_invalid(self):
        self.assertIsNone(self.tracker.add_expense(rec(-1, 5)))
        self.assertIsNone(self.tracker.add_expense("not a dict"))
        added, rejected = self.tracker.add_expenses(
            [rec(4, 5), rec(0, 5), rec(4, 5, description="")])
        self.assertEqual((len(added), rejected, len(self.tracker.expenses)), (1, 2, 1))

    def test_persists_across_reload(self):
        self.tracker.add_expense(rec(8.5, 10, description="Lunch"))
        self.tracker.add_time_target("Week", 50, "2026-10-01", "2026-10-07")
        self.assertEqual(self.tracker.load(), [])
        self.assertEqual(self.tracker.expenses[0].description, "Lunch")
        self.assertEqual(self.tracker.time_targets[0].name, "Week")

    def test_query(self):
        self.tracker.add_expenses([rec(4.5, 5, "Food", "Chicken rice", "2026-10-01"),
                                   rec(6.5, 5, "Drinks", "Bubble tea", "2026-10-02"),
                                   rec(20, 15, "Transport", "MRT top-up", "2026-10-03")])
        q = self.tracker.query
        counts = {
            len(q(description="TEA")): 1,
            len(q(category="drinks")): 1,
            len(q(date_from="2026-10-02")): 2,
            len(q(date_to="2026-10-01")): 1,
            len(q(min_amount=5, max_amount=10)): 1,
            len(q(over_budget=True)): 2,
            len(q(over_budget=False)): 1,
            len(q()): 3,
            len(q(over_budget=True, date_from="2026-10-03")): 1,
            len(q(record_id=99)): 0,
        }
        self.assertTrue(all(k == v for k, v in counts.items()), counts)
        self.assertEqual(q(record_id=3)[0].description, "MRT top-up")
        self.assertEqual([e.amount for e in q(sort_by="amount", descending=True)], [20, 6.5, 4.5])

    def test_time_target_rejects_bad_input(self):
        self.assertIsNone(self.tracker.add_time_target("Week", 50, "2026-10-07", "2026-10-01"))
        self.assertIsNone(self.tracker.add_time_target("Week", -5, "2026-10-01", "2026-10-07"))


class TestAIPipeline(unittest.TestCase):
    """Hardcoded AI JSON -> AIManager -> LogicManager -> ExpenseTracker, end to end."""
    AI_RESPONSES = [("Chicken rice", 4.5, 5, '{"category": "Food", "confidence": 0.9}'),
                    ("Bubble tea", 6.5, 5, '{"category": "Drinks", "confidence": 0.9}'),
                    ("Grab to school", 12, 10, '{"category": "Transport", "confidence": 0.8}'),
                    ("Calculator", 25, 30, '{"category": "Education Materials", "confidence": 0.7}'),
                    ("Haircut", 15, 15, '{"category": "Other", "confidence": 0.6}')]

    def test_ai_categories_reach_analysis(self):
        logic, tracker = LogicManager(), dm.ExpenseTracker(":memory:")
        tracker.load()
        for description, amount, budget, ai_json in self.AI_RESPONSES:
            result = AIManager(MockProvider(ai_json)).categorize(description, amount)
            self.assertFalse(logic.needs_manual_category(result))
            self.assertIsNotNone(tracker.add_expense(rec(amount, budget, result.category, description)))
        result = logic.analyse_spending(tracker.expenses)
        self.assertEqual((result["Number of expenses"], result["Total spent(all time)"],
                          result["Over budget count"]), (5, 63.0, 2))
        self.assertEqual(result["Spending by category"], {
            "Food": 4.5, "Drinks": 6.5, "Transport": 12.0, "Education Materials": 25.0, "Other": 15.0})
        tracker.close()

    def test_failed_ai_falls_back_to_manual_choice(self):
        logic = LogicManager()
        result = AIManager(MockProvider(error=AIUnavailableError("offline"))).categorize("Mystery", 3)
        self.assertTrue(logic.needs_manual_category(result))
        chosen = InputValidator().validate_category_choice("6", CATEGORIES)   # user picks "Other"
        tracker = dm.ExpenseTracker(":memory:")
        tracker.load()
        tracker.add_expense(rec(3.0, 5.0, chosen, "Mystery"))
        self.assertEqual(logic.analyse_spending(tracker.expenses)["Spending by category"], {"Other": 3.0})
        tracker.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)