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
    print("4. Create time-limited spending target")
    print("5. Exit")

def add_expense(history):
    entry = io_manager.get_expense_entry()
    if entry is None:
        io_manager.display_info("Cancelled.")
        return

    entry["date"] = date.today().isoformat()

    io_manager.display_info("Categorising...")
    result = categorize_expense(entry)
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
        # check this new record falls within which time target ranges, and determine if it exceeds the limit
        all_targets = data_manager.get_all_time_targets()
        expense_date = record["date"]
        for t in all_targets:
            if t["start_date"] <= expense_date <= t["end_date"]:
                spent_in_range = data_manager.calc_target_spending(history, t["start_date"], t["end_date"])
                if spent_in_range > t["target_amount"]:
                    io_manager.display_error(f"⚠️ ALERT! Target [{t['name']}] ({t['start_date']}~{t['end_date']}) OVER LIMIT! target:{t['target_amount']:.2f}, spent:{spent_in_range:.2f}")

def create_time_target():
    print("\n--- New Time-Limited Target ---")
    target_input = io_manager.get_time_target_input()
    if target_input is None:
        io_manager.display_info("Target creation cancelled.")
        return
    new_t = data_manager.add_time_target(
        name=target_input["name"],
        target_amount=target_input["amount"],
        start_date=target_input["start"],
        end_date=target_input["end"]
    )
    if new_t is None:
        io_manager.display_error("Failed to create target, invalid input.")
    else:
        io_manager.display_success(f"Created target #{new_t['target_id']} [{new_t['name']}] {new_t['start_date']} ~ {new_t['end_date']}, limit {new_t['target_amount']:.2f}")

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
            targets = data_manager.get_all_time_targets()
            analysis_result = analyse_spending(history, time_target_list=targets)
            io_manager.display_analysis(analysis_result)
        elif choice == "4":
            create_time_target()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            io_manager.display_error("Invalid option, try again.")


if __name__ == "__main__":
    main()
