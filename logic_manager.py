DEFAULT_CONFIDENCE_THRESHOLD = 0.6


class InputValidator:
    MIN_DESCRIPTION_LENGTH = 2

    def validate_amount(self, amount):
        if amount.lower() == "quit":
            return "quit"
        try:
            number = float(amount)
        except ValueError:
            return "Invalid"
        if number < 0:
            return "Negative"
        return number

    def validate_description(self, description):
        description = description.strip()
        if description.lower() == "quit":
            return "quit"
        if description == "":
            return "Empty"
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            return "Short"
        return description

    def validate_category_choice(self, choice, categories):
        try:
            index = int(choice.strip()) - 1
        except ValueError:
            return "Invalid"
        if 0 <= index < len(categories):
            return categories[index]
        return "Invalid"


class LogicManager:
    UNCATEGORISED = "Uncategorised"

    def __init__(self, confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD):
        self._confidence_threshold = confidence_threshold

    def needs_manual_category(self, result):
        return result is None or result.confidence < self._confidence_threshold

    def analyse_spending(self, records, time_target_list=None):
        total = sum(r.amount for r in records)
        return {
            "Number of expenses": len(records),
            "Total spent(all time)": round(total, 2),
            "Average per expense": round(total / len(records), 2) if records else 0,
            "Over budget count": sum(1 for r in records if r.over_budget),
            "Spending by category": self._spending_by_category(records),
            "Time-Limited Targets": self._target_summary(records, time_target_list),
        }

    def _spending_by_category(self, records):
        by_category = {}
        for r in records:
            category = r.ai_response or self.UNCATEGORISED
            by_category[category] = round(by_category.get(category, 0) + r.amount, 2)
        return by_category

    def _target_summary(self, records, time_target_list):
        summary = []
        for t in time_target_list or []:
            spent = t.spent(records)
            summary.append({
                "target_name": t.name,
                "period": f"{t.start_date} ~ {t.end_date}",
                "target_amount": t.target_amount,
                "spent": spent,
                "remaining": t.remaining(records),
                "is_over": spent > t.target_amount,
            })
        return summary