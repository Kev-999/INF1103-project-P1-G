class IOManager:
    """
    Handles all user input and output.
    - Validates basic input (positive numbers, non-blank strings, valid menu choices).
    - Displays menus, results, errors, and success messages.
    - Does NOT perform any business logic, AI categorisation, or data storage.
    """

    MENU_OPTIONS = {
        "1": "Add expense",
        "2": "View expenses",
        "3": "Update expense",
        "4": "Delete expense",
        "5": "Set / view budget",
        "6": "View spending analysis",
        "7": "Exit",
    }

    # ---------- MENU ----------

    def show_main_menu(self) -> None:
        """Display the main menu."""
        print("\n===== Student Expense Tracker =====")
        for key, value in self.MENU_OPTIONS.items():
            print(f"{key}. {value}")

    def get_menu_choice(self) -> str:
        """Ask for a menu choice and validate it. Returns the chosen key."""
        while True:
            choice = input("Choose an option: ").strip()
            if choice in self.MENU_OPTIONS:
                return choice
            self.display_error("Invalid choice. Enter a number from 1 to 7.")

    # ---------- INPUT: EXPENSE ----------

    def get_expense_amount(self) -> float:
        """Ask for expense amount. Returns a positive float."""
        while True:
            raw = input("Expense amount: ").strip()
            try:
                amount = float(raw)
                if amount <= 0:
                    self.display_error("Amount must be a positive number.")
                    continue
                return amount
            except ValueError:
                self.display_error("Invalid amount. Example: 12.50")

    def get_description(self) -> str:
        """Ask for expense description. Returns a non-blank string."""
        while True:
            description = input("Description: ").strip()
            if description:
                return description
            self.display_error("Description cannot be blank.")

    def get_expense_entry(self) -> dict:
        """Ask for a complete expense entry. Returns a dict with amount and description."""
        print("\n--- Add Expense ---")
        return {
            "expense_amount": self.get_expense_amount(),
            "description": self.get_description(),
        }

    # ---------- INPUT: BUDGET ----------

    def get_budget(self) -> float:
        """Ask for allocated budget. Returns a positive float."""
        while True:
            raw = input("Allocated budget: ").strip()
            try:
                budget = float(raw)
                if budget <= 0:
                    self.display_error("Budget must be a positive number.")
                    continue
                return budget
            except ValueError:
                self.display_error("Invalid budget. Example: 500.00")

    # ---------- INPUT: ENTRY ID ----------

    def get_entry_id(self) -> str:
        """Ask for an expense ID. Returns a non-blank string."""
        while True:
            entry_id = input("Enter expense ID: ").strip()
            if entry_id:
                return entry_id
            self.display_error("ID cannot be blank.")

    # ---------- INPUT: CONFIRMATION ----------

    def confirm(self, prompt: str) -> bool:
        """Ask a yes/no question. Returns True for yes, False for no."""
        while True:
            answer = input(f"{prompt} (y/n): ").strip().lower()
            if answer in {"y", "yes"}:
                return True
            if answer in {"n", "no"}:
                return False
            self.display_error("Please enter y or n.")

    # ---------- OUTPUT: DISPLAY LISTS ----------

    def display_expenses(self, entries: list[dict]) -> None:
        """Display a list of expense entries in a table."""
        print("\n--- Expense History ---")
        if not entries:
            print("No expenses found.")
            return

        print(f"{'ID':<36} {'Date':<20} {'Amount':>10} {'Category':<15} Description")
        print("-" * 100)

        for entry in entries:
            print(
                f"{str(entry.get('id', '')):<36} "
                f"{str(entry.get('created_at', '')):<20} "
                f"{float(entry.get('expense_amount', 0)):>10.2f} "
                f"{str(entry.get('category', 'Uncategorised')):<15} "
                f"{entry.get('description', '')}"
            )

    def display_analysis(self, analysis: dict) -> None:
        """
        Display spending analysis.
        The dict is expected to contain any results the logic manager computed.
        This method only formats and prints them.
        """
        print("\n--- Spending Analysis ---")
        # Print whatever keys exist; no logic here.
        for key, value in analysis.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")

    # ---------- OUTPUT: MESSAGES ----------

    def display_error(self, message: str) -> None:
        """Display an error message."""
        print(f"ERROR: {message}")

    def display_success(self, message: str) -> None:
        """Display a success message."""
        print(f"SUCCESS: {message}")

    def display_info(self, message: str) -> None:
        """Display an informational message."""
        print(message)