from datetime import date

import data_manager
import io_manager
from logic_manager import analyse_spending
from ai_manager import categorize_expense


def show_menu():
    print("\n--- Student Expense Tracker ---")
    print("1. Add expense")
    print("2. View expenses")
    print("3. View spending analysis")
    print("4. Exit")


def add_expense(history):
    entry = io_manager.get_expense_entry()
    if entry is None:
        io_manager.display_info("Cancelled.")
        return

    entry["date"] = date.today().isoformat()

    entry["ai_response"] = "Uncategorised"
    if categorize_expense is not None:
        io_manager.display_info("Categorising with AI...")
        result = categorize_expense(entry)
        if result and result.get("category"):
            entry["ai_response"] = result["category"]

    record = data_manager.add_record(history, entry)
    if record is None:
        io_manager.display_error("Expense could not be added (invalid data).")
        return

    error = data_manager.save_history(history)
    if error:
        io_manager.display_error(error)
    else:
        io_manager.display_success(f"Added expense #{record['id']} ({record['ai_response']}).")


def main():
    history, warnings = data_manager.load_history()
    for warning in warnings:
        io_manager.display_error(warning)

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_expense(history)
        elif choice == "2":
            io_manager.display_expenses(history)
        elif choice == "3":
            io_manager.display_analysis(analyse_spending(history))
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            io_manager.display_error("Invalid option, try again.")


if __name__ == "__main__":
    main()
