def show_menu():
    print("\n--- Student Expense Tracker ---")
    print("1. Add expense")
    print("2. View summary")
    print("3. Exit")

def main():
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            print("Add expense")
            # later call io_manager.get_expense_input()
        elif choice == "2":
            print("View summary")
            # later call io_manager.print_summary()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    main()