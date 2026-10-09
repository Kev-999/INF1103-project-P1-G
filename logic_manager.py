def validate_amount(amount):
    if amount.lower() == "quit":
        return "quit"
    try:
        validNumber = float(amount)

        if validNumber < 0:
            return "Negative"
        #Input manager can use string "Negative" to print negative number in input error message

        return validNumber
    
    except ValueError:
        return "Invalid"
    #Input manager can use "Invalid" to print that characters or spaces are not allowed error msg

def validate_description(description):
    description = description.strip()

    if description.lower() == "quit":
            return "quit"

    if description == "":
        return "Empty"
    #Input manager can use string "Empty" to print empty error message

    if len(description) < 2:
         return "Short"
    #Input manager can use string "Short" to print description is too short error message

    return description

def analyse_spending(records):
    """Return a summary dict of the given expense records."""
    total = sum(r["amount"] for r in records)
    byCategory = {}
    for r in records:
        category = r.get("ai_response") or "Uncategorised"
        byCategory[category] = round(byCategory.get(category, 0) + r["amount"], 2)

    return {
        "Number of expenses": len(records),
        "Total spent": round(total, 2),
        "Average per expense": round(total / len(records), 2) if records else 0,
        "Over budget count": sum(1 for r in records if r["amount"] > r["budget"]),
        "Spending by category": byCategory,
    }