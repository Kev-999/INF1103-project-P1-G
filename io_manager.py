from __future__ import annotations
from datetime import date, timedelta
from typing import Callable, Iterable, Sequence
import data_manager
import logic_manager
from logic_manager import (
    validate_amount,
    validate_category_choice,
    validate_description,
)

def _console_read(prompt: str = "") -> str:
    """Default input source. Looks `input` up at call time so tests can patch it."""
    return input(prompt)


class InputOutputManager:
    """All reading and all printing for the expense tracker."""

    # -- layout constants ---------------------------------------------------
    TABLE_WIDTH = 85
    TABLE_HEADER = (
        f"{'ID':<5} {'Date':<12} {'Amount':>10} {'Budget':>10} "
        f"{'Category':<20} Description"
    )
    UNCATEGORISED = "Uncategorised"

    SORT_KEYS = {"1": "date", "2": "amount", "3": "description"}
    OVER_BUDGET = {"1": True, "2": False}

    CHOICE_HINT = "Invalid option, try again."
    DATE_HINT = "Use YYYY-MM-DD, or leave blank to skip."
    AMOUNT_HINT = "Enter a valid non-negative number, or leave blank to skip."
    YES_NO_HINT = "Please enter y or n."

    def __init__(
        self,
        data=data_manager,
        validators=logic_manager,
        today: Callable[[], date] | None = None,
        read: Callable[[str], str] | None = None,
    ) -> None:
        self._data = data
        self._validate_amount = getattr(validators, "validate_amount", validate_amount)
        self._validate_description = getattr(
            validators, "validate_description", validate_description
        )
        self._validate_category_choice = getattr(
            validators, "validate_category_choice", validate_category_choice
        )
        self._today = today or date.today
        self._read = read or _console_read

    # ===================================================================== #
    # OUTPUT -- printing only, no reading and no decisions
    # ===================================================================== #
    def display_info(self, message: str) -> None:
        """Print an informational message."""
        print(message)

    def display_error(self, message: str) -> None:
        """Print an error message."""
        print(f"ERROR: {message}")

    def display_success(self, message: str) -> None:
        """Print a success message."""
        print(f"SUCCESS: {message}")

    def show_menu(self, title: str, options: Sequence[str]) -> None:
        print(f"\n--- {title} ---")
        for index, option in enumerate(options, 1):
            print(f"{index}. {option}")

    def show_heading(self, title: str) -> None:
        print(f"\n--- {title} ---")

    def show_summary_filter_menu(self) -> None:
        print("\n--- Filter summary ---")
        print("1. Date")
        print("2. Description")
        print("3. Category")
        print("4. Minimum / Maximum amount spent")
        print("5. Budget status")
        print("6. Default (all time, oldest to newest)")

    def show_category_menu(self, categories: Sequence[str]) -> None:
        print("\nCategories:")
        for index, category in enumerate(categories, 1):
            print(f"  {index}. {category}")

    def show_budget_menu(self) -> None:
        print("\nBudget status:")
        print("1. Over budget only")
        print("2. Within budget only")
        print("3. All")

    def show_sort_menu(self) -> None:
        print("\nSort by: 1. Date  2. Amount  3. Description  4. Quit")

    def show_report_period_menu(self) -> None:
        print("\n--- Select Report Period ---")
        print("1. This week")
        print("2. This month")
        print("3. Custom date range")
        print("4. All time")

    def show_add_expense_header(self) -> None:
        print("\n--- Add Expense --- (type 'quit' to cancel)")

    def show_time_target_header(self) -> None:
        print("\n==== Create Time-Limited Spending Target ====")

    @staticmethod
    def _field(record, name: str, default=None):
        """Read a field from either a record object or a plain dict."""
        if isinstance(record, dict):
            return record.get(name, default)
        return getattr(record, name, default)

    def display_expenses(self, entries: Sequence) -> None:
        """Print the expense history table."""
        print("\n--- Expense History ---")
        if not entries:
            print("No expenses found.")
            return

        print(self.TABLE_HEADER)
        print("-" * self.TABLE_WIDTH)

        for entry in entries:
            print(
                f"{str(self._field(entry, 'id', '')):<5} "
                f"{str(self._field(entry, 'date', '')):<12} "
                f"{float(self._field(entry, 'amount', 0)):>10.2f} "
                f"{float(self._field(entry, 'budget', 0)):>10.2f} "
                f"{str(self._field(entry, 'ai_response') or self.UNCATEGORISED):<20} "
                f"{self._field(entry, 'description', '')}"
            )

    def display_analysis(self, analysis: dict) -> None:
        """Print whatever keys the logic layer computed; no logic here."""
        print("\n--- Spending Analysis ---")
        for key, value in analysis.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")

    # ===================================================================== #
    # INPUT -- reading only, with a retry loop per kind of answer
    # ===================================================================== #
    def ask_text(self, prompt: str = "") -> str:
        """Read one line and trim surrounding whitespace."""
        return self._read(prompt).strip()

    def ask_raw(self, prompt: str = "") -> str:
        """Read one line verbatim, for validators that expect untrimmed input."""
        return self._read(prompt)

    def ask_choice(self, prompt: str, valid: Iterable[str]) -> str:
        """Ask until the answer is one of `valid`."""
        allowed = set(valid)
        while True:
            choice = self.ask_text(prompt)
            if choice in allowed:
                return choice
            self.display_error(self.CHOICE_HINT)

    def ask_date(self, prompt: str) -> str | None:
        """Ask for a real YYYY-MM-DD date. Blank returns None (skip)."""
        while True:
            text = self.ask_text(prompt)
            if not text:
                return None
            if self._data.is_valid_date(text):
                return text
            self.display_error(self.DATE_HINT)

    def ask_amount(self, prompt: str) -> float | None:
        """Ask for an optional non-negative amount. Blank or 'quit' skips."""
        while True:
            text = self.ask_text(prompt)
            if not text or text.lower() == "quit":
                return None
            try:
                return self._data.to_money(text)
            except ValueError:
                self.display_error(self.AMOUNT_HINT)

    def ask_yes_no(self, prompt: str) -> bool:
        """Ask a yes/no question. True for yes, False for no."""
        while True:
            answer = self.ask_text(f"{prompt} (y/n): ").lower()
            if answer in {"y", "yes"}:
                return True
            if answer in {"n", "no"}:
                return False
            self.display_error(self.YES_NO_HINT)

    # ===================================================================== #
    # SCREENS -- the entry points main.py calls
    # ===================================================================== #
    # -- summary filters ----------------------------------------------------
    def get_summary_options(self, categories: Sequence[str]) -> dict:
        """Ask which filter to apply. Returns keyword arguments for data_manager.query."""
        self.show_summary_filter_menu()
        choice = self.ask_choice("Choose: ", {"1", "2", "3", "4", "5", "6"})

        if choice == "6":
            return {}  # no filters: everything, sorted by date

        if choice == "1":
            start, end = self.get_report_period()
            return {"date_from": start or None, "date_to": end or None}

        if choice == "2":
            text = self.ask_text("Description contains: ")
            return {"description": text or None}

        if choice == "3":
            return {"category": self._read_category(categories)}

        if choice == "4":
            return self._read_amount_range()

        return self._read_budget_status()

    def _read_category(self, categories: Sequence[str]) -> str:
        self.show_category_menu(categories)
        numbers = {str(i) for i in range(1, len(categories) + 1)}
        picked = self.ask_choice("Choose a category: ", numbers)
        return categories[int(picked) - 1]

    def _read_amount_range(self) -> dict:
        """Ask for min / max, rejecting a minimum that is above the maximum."""
        while True:
            minimum = self.ask_amount("Minimum amount (blank to skip): ")
            maximum = self.ask_amount("Maximum amount (blank to skip): ")
            if minimum is not None and maximum is not None and minimum > maximum:
                self.display_error("Minimum is higher than maximum. Try again.")
                continue
            return {"min_amount": minimum, "max_amount": maximum}

    def _read_budget_status(self) -> dict:
        self.show_budget_menu()
        status = self.ask_choice("Choose: ", {"1", "2", "3"})
        return {"over_budget": self.OVER_BUDGET.get(status)}

    def get_sort_choice(self) -> str | None:
        """Ask how to sort the summary. Returns a sort key, or None for Quit."""
        self.show_sort_menu()
        choice = self.ask_choice("Choose: ", {"1", "2", "3", "4"})
        return self.SORT_KEYS.get(choice)

    # -- report period ------------------------------------------------------
    def get_report_period(self) -> tuple[str | None, str | None]:
        """Ask what period to analyse. Returns (start, end) or (None, None) for all time."""
        self.show_report_period_menu()
        choice = self.ask_text("Choose: ")
        today = self._today()

        if choice == "1":  # this week, starting Monday
            start = today - timedelta(days=today.weekday())
            return start.isoformat(), today.isoformat()

        if choice == "2":  # this month
            start = date(today.year, today.month, 1)
            return start.isoformat(), today.isoformat()

        if choice == "3":  # custom range
            return self._read_custom_period()

        return None, None  # all time, or an unrecognised choice

    def _read_custom_period(self) -> tuple[str | None, str | None]:
        while True:
            start = self.ask_date("Start date (YYYY-MM-DD, blank to skip): ")
            end = self.ask_date("End date (YYYY-MM-DD, blank to skip): ")
            if start and end and start > end:
                self.display_error("Start date is after the end date. Try again.")
                continue
            return start, end

    # -- expenses -----------------------------------------------------------
    def get_description(self) -> str | None:
        """Ask for a description. Returns a non-blank string, or None on quit."""
        while True:
            text = self.ask_text("Description: ")
            verdict = self._validate_description(text)

            if verdict == "quit":
                return None
            if verdict == "Empty":
                self.display_info("your input is empty please type in")
                continue
            if verdict == "Short":
                self.display_info("your description is too short please be specific")
                continue

            return verdict

    def get_expense_entry(self) -> dict | None:
        """Ask for a complete expense entry. Returns a dict, or None if the user quits."""
        self.show_add_expense_header()

        amount = self.ask_amount("Expense amount: ")
        if amount is None:
            return None

        budget = self.ask_amount("Budget amount: ")
        if budget is None:
            return None

        description = self.get_description()
        if description is None:
            return None

        return {"amount": amount, "budget": budget, "description": description}

    def confirm(self, prompt: str) -> bool:
        """Ask a yes/no question. Returns True for yes, False for no."""
        return self.ask_yes_no(prompt)

    # -- spending targets ---------------------------------------------------
    def get_target_input(self) -> float | None:
        """Ask for the overall spending target. Returns None on quit."""
        while True:
            raw = self.ask_text(
                "Please enter your overall spending target amount (type quit to cancel): "
            )
            verdict = self._validate_amount(raw)

            if verdict == "quit":
                return None
            if verdict == "Negative":
                self.display_info("Number Cannot be Negative")
                continue
            if verdict == "Invalid":
                self.display_info("Cannot have characters or spaces")
                continue

            return verdict

    def get_target_name(self) -> str | None:
        """Ask for a target name of at least two characters. Returns None on quit."""
        while True:
            raw = self.ask_text("Target name (type quit to cancel): ")
            if raw.lower() == "quit":
                return None
            if len(raw) < 2:
                self.display_info("Name is too short, please be specific.")
                continue
            return raw

    def get_target_date(self, prompt_text: str) -> str | None:
        """Ask for a real YYYY-MM-DD date. Returns None on quit."""
        while True:
            raw = self.ask_text(f"{prompt_text} (YYYY-MM-DD, quit to cancel): ")
            if raw.lower() == "quit":
                return None
            if self._data.is_valid_date(raw):
                return raw
            self.display_info("Invalid date format! Must be real date: YYYY-MM-DD")

    def get_time_target_input(self) -> dict | None:
        """Collect a time-limited target. Returns a dict, or None if cancelled."""
        self.show_time_target_header()

        name = self.get_target_name()
        if name is None:
            return None

        start = self.get_target_date("Enter start date")
        if start is None:
            return None

        end = self.get_target_date("Enter end date")
        if end is None:
            return None

        if start > end:
            self.display_info("Error: start date cannot be later than end date!")
            return None

        amount = self.ask_amount("Enter amount")
        if amount is None:
            return None

        return {"name": name, "start": start, "end": end, "amount": amount}

    # -- AI fallback --------------------------------------------------------
    def get_category_selection(
        self, expense_description: str, categories: Sequence[str]
    ) -> str:
        """Let the user pick a category when the AI is not confident."""
        self.display_info(f"\nThe AI couldn't categorise this reliably: {expense_description}")
        self.display_info("Please choose a category:")
        for index, category in enumerate(categories, 1):
            self.display_info(f"   {index}. {category}")

        while True:
            # Verbatim: the validator decides what counts as a usable answer.
            choice = self.ask_raw(f"Enter number (1-{len(categories)}): ")
            result = self._validate_category_choice(choice, categories)
            if result != "Invalid":
                return result
            self.display_info(f"Invalid choice. Please enter 1-{len(categories)}.")


# --------------------------------------------------------------------------- #
# Module-level functions, so main.py can keep calling io_manager.get_...()
# --------------------------------------------------------------------------- #
default_io = InputOutputManager()


def get_summary_options(categories):
    return default_io.get_summary_options(categories)


def get_sort_choice():
    return default_io.get_sort_choice()


def get_report_period():
    return default_io.get_report_period()


def get_description():
    return default_io.get_description()


def get_expense_entry():
    return default_io.get_expense_entry()


def confirm(prompt):
    return default_io.confirm(prompt)


def display_expenses(entries):
    return default_io.display_expenses(entries)


def display_analysis(analysis):
    return default_io.display_analysis(analysis)


def display_error(message):
    return default_io.display_error(message)


def display_success(message):
    return default_io.display_success(message)


def display_info(message):
    return default_io.display_info(message)


def get_target_input():
    return default_io.get_target_input()


def get_target_name():
    return default_io.get_target_name()


def get_target_date(prompt_text):
    return default_io.get_target_date(prompt_text)


def get_time_target_input():
    return default_io.get_time_target_input()


def get_category_selection(expense_description, categories):
    return default_io.get_category_selection(expense_description, categories)


def show_menu(title, options):
    return default_io.show_menu(title, options)


def show_heading(title):
    return default_io.show_heading(title)


def ask_choice(prompt, valid):
    return default_io.ask_choice(prompt, valid)
