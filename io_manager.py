from logic_manager import validate_amount
from logic_manager import validate_description

"""
Input/output helpers for the expense tracker.

MENU_OPTIONS = {
    "1": "Add expense",
    "2": "View expenses",
    "3": "View spending analysis",
    "4": "Exit",
}
"""

# ---------- INPUT: EXPENSE ----------


def get_expense_amount() -> float | None:
    """Ask for an amount. Returns a positive float, or None if the user types quit."""
    while True:
        raw = input("Expense amount: ").strip()
        validatedAmount = validate_amount(raw)

        if validatedAmount == "quit":
            break

        if validatedAmount == "Negative":
            print("Number Cannot be Negative")
            continue

        if validatedAmount == "Invalid":
            print("Cannot have characters or spaces")
            continue

        return validatedAmount


def get_budget() -> float | None:
    """Ask for the budget for this expense. Returns a float, or None on quit."""
    while True:
        raw = input("Budget for this expense: ").strip()
        validatedAmount = validate_amount(raw)

        if validatedAmount == "quit":
            break

        if validatedAmount == "Negative":
            print("Number Cannot be Negative")
            continue

        if validatedAmount == "Invalid":
            print("Cannot have characters or spaces")
            continue

        return validatedAmount


def get_description() -> str | None:
    """Ask for expense description. Returns a non-blank string, or None on quit."""
    while True:
        description = input("Description: ").strip()
        finaldescription = validate_description(description)

        if finaldescription == "quit":
            break

        if finaldescription == "Empty":
            print("your input is empty please type in")
            continue

        if finaldescription == "Short":
            print("your description is too short please be specific")
            continue

        return finaldescription


def get_expense_entry() -> dict | None:
    """Ask for a complete expense entry. Returns a dict, or None if the user quits."""
    print("\n--- Add Expense --- (type 'quit' to cancel)")
    
    amount = get_expense_amount()
    if amount is None:
        return None
    
    budget = get_budget()
    if budget is None:
        return None
    
    description = get_description()
    if description is None:
        return None
    
    return {"amount": amount, "budget": budget, "description": description}


def confirm(prompt: str) -> bool:
    """Ask a yes/no question. Returns True for yes, False for no."""
    while True:
        answer = input(f"{prompt} (y/n): ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        display_error("Please enter y or n.")

# ---------- OUTPUT: DISPLAY LISTS ----------


def display_expenses(entries: list[dict]) -> None:
    """Display a list of expense entries in a table."""
    print("\n--- Expense History ---")
    if not entries:
        print("No expenses found.")
        return

    print(f"{'ID':<5} {'Date':<12} {'Amount':>10} {'Budget':>10} {'Category':<20} Description")
    print("-" * 85)

    for entry in entries:
        print(
            f"{str(entry.get('id', '')):<5} "
            f"{str(entry.get('date', '')):<12} "
            f"{float(entry.get('amount', 0)):>10.2f} "
            f"{float(entry.get('budget', 0)):>10.2f} "
            f"{str(entry.get('ai_response') or 'Uncategorised'):<20} "
            f"{entry.get('description', '')}"
        )


def display_analysis(analysis: dict) -> None:
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


def display_error(message: str) -> None:
    """Display an error message."""
    print(f"ERROR: {message}")


def display_success(message: str) -> None:
    """Display a success message."""
    print(f"SUCCESS: {message}")


def display_info(message: str) -> None:
    """Display an informational message."""
    print(message)
