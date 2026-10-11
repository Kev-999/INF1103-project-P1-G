def validate_amount(amount):
    if amount.lower() == "quit":
        return "quit"
    try:
        validNumber = float(amount)
        if validNumber < 0:
            return "Negative"
        return validNumber
    except ValueError:
        return "Invalid"

def validate_description(description):
    description = description.strip()
    if description.lower() == "quit":
            return "quit"
    if description == "":
        return "Empty"
    if len(description) < 2:
         return "Short"
    return description

def validate_category_choice(choice, categories):
    try:
        index = int(choice.strip()) - 1
        if 0 <= index < len(categories):
            return categories[index]
        return "Invalid"
    except ValueError:
        return "Invalid"

def analyse_spending(records, time_target_list):
    total = sum(r["amount"] for r in records)
    byCategory = {}
    for r in records:
        category = r.get("ai_response")
        byCategory[category] = round(byCategory.get(category, 0) + r["amount"], 2)

    target_summary = []
    for t in time_target_list:
        spent = sum(r["amount"] for r in records if t["start_date"] <= r["date"] <= t["end_date"])
        spent = round(spent,2)
        remain = round(t["target_amount"] - spent, 2)
        over = spent > t["target_amount"]
        target_summary.append({
            "target_name": t["name"],
            "period": f"{t['start_date']} ~ {t['end_date']}",
            "target_amount": t["target_amount"],
            "spent": spent,
            "remaining": remain,
            "is_over": over
        })

    return {
        "Number of expenses": len(records),
        "Total spent(all time)": round(total, 2),
        "Average per expense": round(total / len(records), 2) if records else 0,
        "Over budget count": sum(1 for r in records if r["amount"] > r["budget"]),
        "Spending by category": byCategory,
        "Time-Limited Targets": target_summary
    }