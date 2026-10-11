from logic_manager import validate_amount
from logic_manager import validate_description
from datetime import date, timedelta
import data_manager

def _ask_date(prompt):
    """Ask for a YYYY-MM-DD date. Blank returns None (skip)."""
    while True:
        text = input(prompt).strip()
        if not text:
            return None
        if data_manager.is_valid_date(text):
            return text
        display_error("Use YYYY-MM-DD, or leave blank to skip.")


def _ask_amount(prompt) -> float | None:
    """Ask for an optional non-negative amount. Blank returns None (skip)."""
    while True:
        text = input(prompt).strip()
        if not text:
            return None
        try:
            return data_manager.to_money(text)
        except ValueError:
            display_error("Enter a valid non-negative number, or leave blank to skip.")

def _choose(prompt, valid):
    """Keep asking until the user enters one of the valid choices."""
    while True:
        choice = input(prompt).strip()
        if choice in valid:
            return choice
        display_error("Invalid option, try again.")


def get_summary_options(categories):
    """Ask which filter to apply. Returns keyword arguments for data_manager.query."""
    print("\n--- Filter summary ---")
    print("1. Date")
    print("2. Description")
    print("3. Category")
    print("4. Minimum / Maximum amount spent")
    print("5. Budget status")
    print("6. Default (all time, oldest to newest)")
    choice = _choose("Choose: ", {"1", "2", "3", "4", "5", "6"})

    if choice == "6":
        return {}   # no filters: query returns everything, sorted by date

    if choice == "1":
        start, end = get_report_period()
        return {"date_from": start or None, "date_to": end or None}

    if choice == "2":
        text = input("Description contains: ").strip()
        return {"description": text or None}

    if choice == "3":
        print("\nCategories:")
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category}")
        valid = {str(i) for i in range(1, len(categories) + 1)}
        picked = _choose("Choose a category: ", valid)
        return {"category": categories[int(picked) - 1]}

    if choice == "4":
        while True:
            minimum = _ask_amount("Minimum amount (blank to skip): ")
            maximum = _ask_amount("Maximum amount (blank to skip): ")
            if minimum is not None and maximum is not None and minimum > maximum:
                display_error("Minimum is higher than maximum. Try again.")
                continue
            return {"min_amount": minimum, "max_amount": maximum}

    # choice == "5"
    print("\nBudget status:")
    print("1. Over budget only")
    print("2. Within budget only")
    print("3. All")
    status = _choose("Choose: ", {"1", "2", "3"})
    return {"over_budget": {"1": True, "2": False}.get(status)}


def get_sort_choice():
    """Ask how to sort the summary on screen. Returns a sort key, or None for Quit."""
    print("\nSort by: 1. Date  2. Amount  3. Description  4. Quit")
    choice = _choose("Choose: ", {"1", "2", "3", "4"})
    return {"1": "date", "2": "amount", "3": "description"}.get(choice)

def get_report_period():
    """Ask user what time period to analyse. Returns (start_date, end_date) or (None, None)."""

    print("\n--- Select Report Period ---")
    print("1. This week")
    print("2. This month")
    print("3. Custom date range")
    print("4. All time")

    choice = input("Choose: ").strip()
    today = date.today()

    if choice == "1":
        start = today - timedelta(days=today.weekday())
        return start.isoformat(), today.isoformat()
    elif choice == "2":
        start = date(today.year, today.month, 1)
        return start.isoformat(), today.isoformat()
    elif choice == "3":
        while True:
            start = _ask_date("Start date (YYYY-MM-DD, blank to skip): ")
            end = _ask_date("End date (YYYY-MM-DD, blank to skip): ")
            if start and end and start > end:
                display_error("Start date is after the end date. Try again.")
                continue
            return start, end
    return None, None
"""
Input/output helpers for the expense tracker.

MENU_OPTIONS = {
    "1": "Add expense",
    "2": "View expenses",
    "3": "View spending analysis",
    "4": "Exit",
}
"""

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

    amount = _ask_amount("Expense amount: ")
    if amount is None:
        return None

    budget = _ask_amount("Budget amount: ")
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


def display_error(message: str) -> None:
    """Display an error message."""
    print(f"ERROR: {message}")


def display_success(message: str) -> None:
    """Display a success message."""
    print(f"SUCCESS: {message}")


def display_info(message: str) -> None:
    """Display an informational message."""
    print(message)


def get_target_input() -> float | None:
    """get expense target, return float; user input 'quit' returns None"""
    while True:
        raw = input("Please enter your overall spending target amount (type quit to cancel): ").strip()
        validated = validate_amount(raw)
        if validated == "quit":
            return None
        if validated == "Negative":
            print("Number Cannot be Negative")
            continue
        if validated == "Invalid":
            print("Cannot have characters or spaces")
            continue
        return validated

def get_target_name() -> str | None:
    while True:
        raw = input("Target name (type quit to cancel): ").strip()
        if raw.lower() == "quit":
            return None
        if len(raw) <2:
            print("Name is too short, please be specific.")
            continue
        return raw

def get_target_date(prompt_text:str) -> str | None:
    """input YYYY-MM-DD date, quit returns None, validate date legitimacy"""
    while True:
        raw = input(f"{prompt_text} (YYYY-MM-DD, quit to cancel): ").strip()
        if raw.lower() == "quit":
            return None
        if data_manager.is_valid_date(raw):
            return raw
        print("Invalid date format! Must be real date: YYYY-MM-DD")

def get_target_amount() -> float | None:
    while True:
        raw = input("Target spending amount: ").strip()
        validated = validate_amount(raw)
        if validated == "quit":
            return None
        if validated == "Negative":
            print("Number Cannot be Negative")
            continue
        if validated == "Invalid":
            print("Cannot have characters or spaces")
            continue
        return validated

def get_time_target_input():
    """collect time-limited spending target form, return dictionary; user quit returns None"""
    print("\n==== Create Time-Limited Spending Target ====")
    name = get_target_name()
    if name is None:
        return None
    start = get_target_date("Enter start date")
    if start is None:
        return None
    end = get_target_date("Enter end date")
    if end is None:
        return None
    if start > end:
        print("Error: start date cannot be later than end date!")
        return None
    amount = get_target_amount()
    if amount is None:
        return None
    return {"name":name,"start":start,"end":end,"amount":amount}
