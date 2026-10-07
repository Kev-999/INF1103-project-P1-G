from logic_manager import validateAmount 
from logic_manager import validateDescription

class IOManager:
    """
    MENU_OPTIONS = {
        "1": "Add expense",
        "2": "View expenses",
        "4": "Delete expense",
        "6": "View spending analysis",
        "7": "Exit",
    }

    """

    # ---------- INPUT: EXPENSE ----------

    def get_expense_amount(self) -> float:
        """Ask for expense amount. Returns a positive float."""
        while True:
            raw = input("Expense amount: ").strip()
            validatedAmount = validateAmount(raw)

            if validatedAmount == "quit":
                break

            if validatedAmount == "Negative":
                print("Number Cannot be Negative")
                break

            if validatedAmount == "Invalid":
                print("Cannot have characters or spaces")
                break

            else:
                 return validatedAmount
               
    def get_description(self) -> str:
        """Ask for expense description. Returns a non-blank string."""
        while True:
            description = input("Description: ").strip()
            finaldescription = validateDescription(description)

            if finaldescription == "quit":
                break

            if finaldescription == "Empty":
                print("your input is empty please type in")
                break

            if finaldescription == "short":
                print("your description is too short please be specific")
                break

            else:
                return finaldescription
        


    def get_expense_entry(self) -> dict:
        """Ask for a complete expense entry. Returns a dict with amount and description."""
        print("\n--- Add Expense ---")
        return {
            "expense_amount": self.get_expense_amount(),
            "description": self.get_description(),
        }

    # ---------- INPUT: ENTRY ID ----------

    # def get_entry_id(self) -> str:
    #     """Ask for an expense ID. Returns a non-blank string."""
    #     while True:
    #         entry_id = input("Enter expense ID: ").strip()
    #         if entry_id:
    #             return entry_id
    #         self.display_error("ID cannot be blank.")

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