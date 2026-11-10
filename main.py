from datetime import date
from data_manager import ExpenseTracker
import io_manager
from logic_manager import analyse_spending, needs_manual_category
from ai_manager import build_default_manager, CATEGORIES

SORT_DESCENDING = {"date": False, "amount": True, "description": False}


def show_menu():
    print("\n--- Student Expense Tracker ---")
    print("1. Add expense")
    print("2. View expenses")
    print("3. View spending analysis")
    print("4. Create time-limited spending target")
    print("5. Exit")


def add_expense(tracker, ai_manager):
    entry = io_manager.get_expense_entry()
    if entry is None:
        io_manager.display_info("Cancelled.")
        return

    entry["date"] = date.today().isoformat()

    io_manager.display_info("Categorising with AI...")
    result = ai_manager.categorize(entry["description"], entry["amount"])

    # Business rule (in logic_manager): AI failed or low confidence -> user picks
    if needs_manual_category(result):
        entry["ai_response"] = io_manager.get_category_selection(entry["description"], CATEGORIES)
    else:
        entry["ai_response"] = result.category

    record = tracker.add_expense(entry)
    if record is None:
        io_manager.display_error("Expense could not be added (invalid data or database error).")
        return

    io_manager.display_success(f"Added expense #{record.id} ({record.ai_response}).")

    # check which time targets this new record falls into, and whether any is over its limit
    for t in tracker.time_targets:
        if t.contains(record.date):
            spent = t.spent(tracker.expenses)
            if spent > t.target_amount:
                io_manager.display_error(
                    f" ALERT! Target [{t.name}] ({t.start_date}~{t.end_date}) OVER LIMIT! "
                    f"target:{t.target_amount:.2f}, spent:{spent:.2f}"
                )


def view_summary(tracker):
    options = io_manager.get_summary_options(CATEGORIES)
    sort_by = "date"   # oldest first by default

    while True:
        ordered = tracker.query(**options, sort_by=sort_by, descending=SORT_DESCENDING[sort_by])
        if not ordered:
            io_manager.display_info("No expenses match those filters.")
            return

        io_manager.display_expenses(ordered)
        io_manager.display_analysis(analyse_spending(ordered, tracker.time_targets))

        sort_by = io_manager.get_sort_choice()
        if sort_by is None:   # user chose Quit
            return


def create_time_target(tracker):
    print("\n--- New Time-Limited Target ---")
    target_input = io_manager.get_time_target_input()
    if target_input is None:
        io_manager.display_info("Target creation cancelled.")
        return

    new_t = tracker.add_time_target(
        name=target_input["name"],
        target_amount=target_input["amount"],
        start_date=target_input["start"],
        end_date=target_input["end"],
    )
    if new_t is None:
        io_manager.display_error("Failed to create target, invalid input.")
    else:
        io_manager.display_success(
            f"Created target #{new_t.target_id} [{new_t.name}] "
            f"{new_t.start_date} ~ {new_t.end_date}, limit {new_t.target_amount:.2f}"
        )


def main():
    tracker = ExpenseTracker()
    ai_manager = build_default_manager()

    for warning in tracker.load():
        io_manager.display_error(warning)

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_expense(tracker, ai_manager)
        elif choice == "2":
            io_manager.display_expenses(tracker.expenses)
        elif choice == "3":
            view_summary(tracker)
        elif choice == "4":
            create_time_target(tracker)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            io_manager.display_error("Invalid option, try again")


if __name__ == "__main__":
    main()