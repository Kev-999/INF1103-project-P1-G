from datetime import date
from ai_manager import CATEGORIES, build_default_manager
from data_manager import ExpenseTracker
from io_manager import InputOutputManager
from logic_manager import InputValidator, LogicManager


class App:
    """Coordinates the four managers. Replaces the procedural main.py."""

    TITLE = "Student Expense Tracker"
    MENU = ["Add expense", "View expenses", "View spending analysis",
            "Create time-limited spending target", "Exit"]
    SORT_DESCENDING = {"date": False, "amount": True, "description": False}

    def __init__(self, io, logic, tracker, ai_manager):
        self._io = io
        self._logic = logic
        self._tracker = tracker
        self._ai = ai_manager

    @classmethod
    def create_default(cls):
        """Build the app with the real managers."""
        io = InputOutputManager(validators=InputValidator())
        return cls(io, LogicManager(), ExpenseTracker(), build_default_manager())

    def run(self):
        for warning in self._tracker.load():
            self._io.display_error(warning)

        handlers = {
            "1": self._add_expense,
            "2": self._view_expenses,
            "3": self._view_summary,
            "4": self._create_time_target,
        }
        valid = set(handlers) | {"5"}

        while True:
            self._io.show_menu(self.TITLE, self.MENU)
            choice = self._io.ask_choice("Choose an option: ", valid)
            if choice == "5":
                self._io.display_info("Goodbye!")
                return
            handlers[choice]()

    # ---- menu actions ----
    def _view_expenses(self):
        self._io.display_expenses(self._tracker.expenses)

    def _add_expense(self):
        entry = self._io.get_expense_entry()
        if entry is None:
            self._io.display_info("Cancelled.")
            return

        entry["date"] = date.today().isoformat()

        self._io.display_info("Categorising with AI...")
        result = self._ai.categorize(entry["description"], entry["amount"])

        # Business rule: AI failed or low confidence -> user picks
        if self._logic.needs_manual_category(result):
            entry["ai_response"] = self._io.get_category_selection(
                entry["description"], CATEGORIES
            )
        else:
            entry["ai_response"] = result.category

        record = self._tracker.add_expense(entry)
        if record is None:
            self._io.display_error(
                "Expense could not be added (invalid data or database error)."
            )
            return

        self._io.display_success(f"Added expense #{record.id} ({record.ai_response}).")
        self._check_target_alerts(record)

    def _check_target_alerts(self, record):
        """Warn if the new expense pushes any time target over its limit."""
        for t in self._tracker.time_targets:
            if t.contains(record.date):
                spent = t.spent(self._tracker.expenses)
                if spent > t.target_amount:
                    self._io.display_error(
                        f" ALERT! Target [{t.name}] ({t.start_date}~{t.end_date}) "
                        f"OVER LIMIT! target:{t.target_amount:.2f}, spent:{spent:.2f}"
                    )

    def _view_summary(self):
        options = self._io.get_summary_options(CATEGORIES)
        sort_by = "date"  # oldest first by default

        while True:
            ordered = self._tracker.query(
                **options, sort_by=sort_by, descending=self.SORT_DESCENDING[sort_by]
            )
            if not ordered:
                self._io.display_info("No expenses match those filters.")
                return

            self._io.display_expenses(ordered)
            self._io.display_analysis(
                self._logic.analyse_spending(ordered, self._tracker.time_targets)
            )

            sort_by = self._io.get_sort_choice()
            if sort_by is None:  # user chose Quit
                return

    def _create_time_target(self):
        target_input = self._io.get_time_target_input()
        if target_input is None:
            self._io.display_info("Target creation cancelled.")
            return

        new_t = self._tracker.add_time_target(
            name=target_input["name"],
            target_amount=target_input["amount"],
            start_date=target_input["start"],
            end_date=target_input["end"],
        )
        if new_t is None:
            self._io.display_error("Failed to create target, invalid input.")
        else:
            self._io.display_success(
                f"Created target #{new_t.target_id} [{new_t.name}] "
                f"{new_t.start_date} ~ {new_t.end_date}, limit {new_t.target_amount:.2f}"
            )