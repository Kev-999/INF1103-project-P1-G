import copy
import unittest

from logic_manager import validate_amount, validate_description, analyse_spending

# Categories the real AI Manager is allowed to return
CATEGORIES = ["Food", "Drinks", "Transport", "Entertainment", "Education Materials", "Other"]


class TestValidateAmount(unittest.TestCase):
    def test_valid_numbers(self):
        self.assertEqual(validate_amount("12.50"), 12.5)
        self.assertEqual(validate_amount("100"), 100.0)
        self.assertEqual(validate_amount(" 7 "), 7.0)   # float() tolerates spaces
        self.assertEqual(validate_amount("0"), 0.0)     # zero is allowed here
        self.assertEqual(validate_amount("1e2"), 100.0)

    def test_negative(self):
        self.assertEqual(validate_amount("-5"), "Negative")
        self.assertEqual(validate_amount("-0.01"), "Negative")

    def test_invalid(self):
        for bad in ["abc", "", "   ", "12,50", "$10", "1 2", "5kg", "--5"]:
            with self.subTest(value=bad):
                self.assertEqual(validate_amount(bad), "Invalid")

    def test_quit_case_insensitive(self):
        for q in ["quit", "QUIT", "Quit"]:
            with self.subTest(value=q):
                self.assertEqual(validate_amount(q), "quit")


class TestValidateDescription(unittest.TestCase):
    def test_valid_and_stripped(self):
        self.assertEqual(validate_description("Coffee"), "Coffee")
        self.assertEqual(validate_description("  Lunch  "), "Lunch")
        self.assertEqual(validate_description("TV"), "TV")  # exactly 2 chars is OK
        self.assertEqual(validate_description("Lunch at McDonald's"), "Lunch at McDonald's")

    def test_empty(self):
        self.assertEqual(validate_description(""), "Empty")
        self.assertEqual(validate_description("    "), "Empty")

    def test_short(self):
        self.assertEqual(validate_description("a"), "Short")
        self.assertEqual(validate_description("  a  "), "Short")

    def test_quit(self):
        self.assertEqual(validate_description("quit"), "quit")
        self.assertEqual(validate_description("  QUIT "), "quit")


class TestAnalyseSpending(unittest.TestCase):
    # Hardcoded sample records. "ai_response" mimics the category the AI
    # Manager would have returned (None / "" = AI failed or gave nothing).
    SAMPLE = [
        {"description": "Chicken rice",    "amount": 4.50,  "budget": 5.00,  "ai_response": "Food"},
        {"description": "McDonald's",      "amount": 8.20,  "budget": 7.00,  "ai_response": "Food"},
        {"description": "Bubble tea",      "amount": 6.50,  "budget": 5.00,  "ai_response": "Drinks"},
        {"description": "MRT top-up",      "amount": 20.00, "budget": 15.00, "ai_response": "Transport"},
        {"description": "Netflix",         "amount": 15.00, "budget": 20.00, "ai_response": "Entertainment"},
        {"description": "Textbook",        "amount": 40.00, "budget": 50.00, "ai_response": "Education Materials"},
        {"description": "Haircut",         "amount": 12.00, "budget": 12.00, "ai_response": "Other"},
        {"description": "Mystery charge",  "amount": 3.30,  "budget": 5.00,  "ai_response": None},
        {"description": "Blank response",  "amount": 1.00,  "budget": 5.00,  "ai_response": ""},
    ]

    def test_full_summary(self):
        result = analyse_spending(self.SAMPLE)
        self.assertEqual(result["Number of expenses"], 9)
        self.assertEqual(result["Total spent"], 110.50)
        self.assertEqual(result["Average per expense"], 12.28)
        self.assertEqual(result["Over budget count"], 3)  # McDonald's, Bubble tea, MRT
        self.assertEqual(
            result["Spending by category"],
            {
                "Food": 12.70,
                "Drinks": 6.50,
                "Transport": 20.00,
                "Entertainment": 15.00,
                "Education Materials": 40.00,
                "Other": 12.00,
                "Uncategorised": 4.30,
            },
        )

    def test_every_predefined_category_is_grouped(self):
        records = [
            {"amount": 1.0, "budget": 5.0, "ai_response": c} for c in CATEGORIES
        ]
        result = analyse_spending(records)
        self.assertEqual(set(result["Spending by category"]), set(CATEGORIES))
        self.assertEqual(result["Total spent"], 6.0)

    def test_empty_records(self):
        result = analyse_spending([])
        self.assertEqual(result["Number of expenses"], 0)
        self.assertEqual(result["Total spent"], 0)
        self.assertEqual(result["Average per expense"], 0)   # no ZeroDivisionError
        self.assertEqual(result["Over budget count"], 0)
        self.assertEqual(result["Spending by category"], {})

    def test_single_record(self):
        result = analyse_spending([{"amount": 9.99, "budget": 10.0, "ai_response": "Food"}])
        self.assertEqual(result["Number of expenses"], 1)
        self.assertEqual(result["Total spent"], 9.99)
        self.assertEqual(result["Average per expense"], 9.99)
        self.assertEqual(result["Over budget count"], 0)

    def test_missing_ai_response_key(self):
        records = [{"amount": 4.0, "budget": 10.0}]  # key absent entirely
        result = analyse_spending(records)
        self.assertEqual(result["Spending by category"], {"Uncategorised": 4.0})

    def test_equal_to_budget_is_not_over(self):
        records = [{"amount": 10.0, "budget": 10.0, "ai_response": "Food"}]
        self.assertEqual(analyse_spending(records)["Over budget count"], 0)

    def test_just_over_budget_is_over(self):
        records = [{"amount": 10.01, "budget": 10.0, "ai_response": "Food"}]
        self.assertEqual(analyse_spending(records)["Over budget count"], 1)

    def test_float_rounding(self):
        records = [
            {"amount": 0.1, "budget": 1, "ai_response": "Other"},
            {"amount": 0.2, "budget": 1, "ai_response": "Other"},
        ]
        result = analyse_spending(records)
        self.assertEqual(result["Total spent"], 0.3)
        self.assertEqual(result["Spending by category"], {"Other": 0.3})

    def test_does_not_modify_input(self):
        before = copy.deepcopy(self.SAMPLE)
        analyse_spending(self.SAMPLE)
        self.assertEqual(self.SAMPLE, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)