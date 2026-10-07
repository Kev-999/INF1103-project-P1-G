"""
Entries look like:
    {"id": 1, "date": "2026-10-02", "description": "Lunch",
     "amount": 12.5, "budget": 20.0, "ai_response": "Nice, under budget."}
"""
import json

DATA_FILE = "spending.json" 
FIELDS = ["id", "date", "description", "amount", "budget", "ai_response"]
REQUIRED_FIELDS = ["id", "date", "description", "amount", "budget"]  # ai_response optional

full_history = []


def to_money(value):
    """Convert to a non-negative amount rounded to 2 decimals, or raise ValueError."""
    number = float(value)
    if not (0 <= number < 1e12):  # also rejects nan and inf
        raise ValueError("amount out of range")
    return round(number, 2)


def is_valid_date(text):
    """True if text is a real calendar date written as YYYY-MM-DD."""
    if not isinstance(text, str) or len(text) != 10:
        return False
    if text[4] != "-" or text[7] != "-":
        return False
    parts = (text[:4], text[5:7], text[8:])
    if not all(c in "0123456789" for part in parts for c in part):
        return False
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    if year < 1 or not 1 <= month <= 12:
        return False
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_in_month = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= day <= days_in_month[month - 1]


def clean_record(raw):
    """Return a valid record dict, or None if raw is unusable."""
    try:
        record = {
            "id": int(raw["id"]),
            "date": str(raw["date"]).strip(),
            "description": str(raw["description"]).strip(),
            "amount": to_money(raw["amount"]),
            "budget": to_money(raw["budget"]),
            "ai_response": str(raw.get("ai_response") or "").strip(),
        }
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    if not record["description"] or record["amount"] <= 0:
        return None
    if not is_valid_date(record["date"]):
        return None
    return record


def backup_corrupted_file(filename):
    try:
        with open(filename, "rb") as source, open(filename + ".corrupted", "wb") as target:
            target.write(source.read())
        return True
    except OSError:
        return False


def _read_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("JSON root must be a list")
    return data



def _load_records(filename):

    try:
        raw_rows = _read_json(filename)
    except FileNotFoundError:
        return [], []
    except (ValueError): 
        if backup_corrupted_file(filename):
            return [], [f"{filename} was corrupted. A copy was kept as {filename}.corrupted."]
        return [], [f"{filename} was corrupted and could not be backed up."]
    except OSError as error:
        return [], [f"Could not read {filename}: {error}"]

    records = []
    skipped = 0
    for raw in raw_rows:
        record = clean_record(raw)
        if record is None:
            skipped += 1
        else:
            records.append(record)
    warnings = [f"Skipped {skipped} bad record(s) in {filename}."] if skipped else []
    return records, warnings


def load_history(filename=DATA_FILE):
    """Fill full_history from disk. Returns (full_history, warnings)."""
    records, warnings = _load_records(filename)
    full_history.clear()
    full_history.extend(records)
    return full_history, warnings


def save_history(new_history, filename=DATA_FILE):
    """Save to disk. Returns None on success, or an error message string."""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(new_history, file, indent=2)
    except OSError as error:
        return f"Could not save to {filename}: {error}"
    return None


def get_next_id(new_history):
    if not new_history:
        return 1
    return max(record["id"] for record in new_history) + 1


def add_record(history, entry):
    if not isinstance(entry, dict):
        return None
    record = clean_record({
        "id": get_next_id(history),
        "date": entry.get("date"),
        "description": entry.get("description"),
        "amount": entry.get("amount"),
        "budget": entry.get("budget"),
        "ai_response": entry.get("ai_response"),
    })
    if record is not None:
        history.append(record)
    return record


def add_records(history, entries):
    added = []
    rejected = 0
    for entry in entries:
        record = add_record(history, entry)
        if record:
            added.append(record)
        else:
            rejected += 1
    return added, rejected


def find_by_id(records, record_id):
    for record in records:
        if record["id"] == record_id:
            return record
    return None


def filter_by_description(records, text):
    text = text.lower()
    return [r for r in records if text in r["description"].lower()]


def filter_by_date(records, start=None, end=None):
    """Dates are YYYY-MM-DD, so plain string comparison orders them correctly."""
    result = records
    if start is not None:
        result = [r for r in result if r["date"] >= start]
    if end is not None:
        result = [r for r in result if r["date"] <= end]
    return result


def filter_by_amount(records, min_amount=None, max_amount=None):
    result = records
    if min_amount is not None:
        result = [r for r in result if r["amount"] >= min_amount]
    if max_amount is not None:
        result = [r for r in result if r["amount"] <= max_amount]
    return result


def filter_by_budget_status(records, over_budget):
    """over_budget=True -> only entries where amount > budget; False -> the rest."""
    return [r for r in records if (r["amount"] > r["budget"]) == over_budget]


def query(records, description=None, date_from=None, date_to=None,
          min_amount=None, max_amount=None, over_budget=None, record_id=None):
    """Combine any filters; None means 'skip this filter'."""
    result = records
    if record_id is not None:
        match = find_by_id(result, record_id)
        result = [match] if match else []
    if description:
        result = filter_by_description(result, description)
    result = filter_by_date(result, date_from, date_to)
    result = filter_by_amount(result, min_amount, max_amount)
    if over_budget is not None:
        result = filter_by_budget_status(result, over_budget)
    return result