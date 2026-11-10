CONFIDENCE_THRESHOLD = 0.6

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


def analyse_spending(records, time_target_list=None):
    total = sum(r.amount for r in records)
    byCategory = {}
    for r in records:
        category = r.ai_response or "Uncategorised"
        byCategory[category] = round(byCategory.get(category, 0) + r.amount, 2)

    target_summary = []
    if time_target_list:
        for t in time_target_list:
            spent = t.spent(records)
            target_summary.append({
                "target_name": t.name,
                "period": f"{t.start_date} ~ {t.end_date}",
                "target_amount": t.target_amount,
                "spent": spent,
                "remaining": t.remaining(records),
                "is_over": spent > t.target_amount
            })

    return {
        "Number of expenses": len(records),
        "Total spent(all time)": round(total, 2),
        "Average per expense": round(total / len(records), 2) if records else 0,
        "Over budget count": sum(1 for r in records if r.over_budget),
        "Spending by category": byCategory,
        "Time-Limited Targets": target_summary
    }

    return {
        "Number of expenses": len(records),
        "Total spent(all time)": round(total, 2),
        "Average per expense": round(total / len(records), 2) if records else 0,
        "Over budget count": sum(1 for r in records if r["amount"] > r["budget"]),
        "Spending by category": byCategory,
        "Time-Limited Targets": target_summary
    }

def needs_manual_category(result):
    """True if the AI failed (None) or isn't confident enough."""
    return result is None or result.confidence < CONFIDENCE_THRESHOLD

def validate_category_choice(choice, categories):
    """Return the chosen category name, or "Invalid"."""
    try:
        index = int(choice.strip()) - 1
    except ValueError:
        return "Invalid"
    if 0 <= index < len(categories):
        return categories[index]
    return "Invalid"