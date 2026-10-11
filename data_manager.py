"""
Entries look like:
    {"id": 1, "date": "2026-10-02", "description": "Lunch",
     "amount": 12.5, "budget": 20.0, "ai_response": "Nice, under budget."}
<<<<<<< HEAD
"""
import json
import os

DATA_FILE = os.path.join("data","spending.json")
FIELDS = ["id", "date", "description", "amount", "budget", "ai_response"]
REQUIRED_FIELDS = ["id", "date", "description", "amount", "budget"]  

full_history = []

=======

File new structure:
{
  "records": [ {...expense entries...} ],
  "time_targets": [
      {"target_id":1,"name":"xxx","target_amount":500.0,"start_date":"2026-10-01","end_date":"2026-10-07"}
  ]
}
"""
import json
import os
DATA_FILE = os.path.join("data","spending.json")
FIELDS = ["id", "date", "description", "amount", "budget", "ai_response"]
REQUIRED_FIELDS = ["id", "date", "description", "amount", "budget"]

full_history = []
time_targets = []   # 存储多个时间段目标
>>>>>>> 71743bf (target function added)

def to_money(value):
    """Convert to a non-negative amount rounded to 2 decimals, or raise ValueError."""
    number = float(value)
<<<<<<< HEAD
    if not (0 <= number < 1e12):  # also rejects nan and inf
        raise ValueError("amount out of range")
    return round(number, 2)


=======
    if not (0 <= number < 1e12):
        raise ValueError("amount out of range")
    return round(number, 2)

>>>>>>> 71743bf (target function added)
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

<<<<<<< HEAD

def clean_record(raw):
    """Return a valid record dict, or None if raw is unusable."""
=======
def clean_record(raw):
>>>>>>> 71743bf (target function added)
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

<<<<<<< HEAD

=======
>>>>>>> 71743bf (target function added)
def backup_corrupted_file(filename):
    try:
        with open(filename, "rb") as source, open(filename + ".corrupted", "wb") as target:
            target.write(source.read())
        return True
    except OSError:
        return False

<<<<<<< HEAD

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
=======
def _read_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def _load_records(filename):
    global time_targets
    try:
        raw_data = _read_json(filename)
    except FileNotFoundError:
        return [], [], []
    except ValueError:
        if backup_corrupted_file(filename):
            return [], [f"{filename} was corrupted. A copy was kept as {filename}.corrupted."], []
        return [], [f"{filename} was corrupted and could not be backed up."], []
    except OSError as error:
        return [], [f"Could not read {filename}: {error}"], []

    # 兼容旧版本文件：根节点为list
    if isinstance(raw_data, list):
        raw_rows = raw_data
        loaded_targets = []
    elif isinstance(raw_data, dict):
        raw_rows = raw_data.get("records", [])
        loaded_targets = raw_data.get("time_targets", [])
    else:
        raise ValueError("invalid json root")
>>>>>>> 71743bf (target function added)

    records = []
    skipped = 0
    for raw in raw_rows:
        record = clean_record(raw)
        if record is None:
<<<<<<< HEAD
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
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename,"w",encoding="utf-8") as file:
            json.dump(new_history,file,indent=2)
=======
            skipped +=1
        else:
            records.append(record)
    warnings = [f"Skipped {skipped} bad record(s) in {filename}."] if skipped else []
    time_targets = loaded_targets
    return records, warnings, loaded_targets

def load_history(filename=DATA_FILE):
    global full_history, time_targets
    records, warnings, targets = _load_records(filename)
    full_history.clear()
    full_history.extend(records)
    time_targets = targets
    return full_history, warnings

def save_history(new_history, filename=DATA_FILE):
    global time_targets
    try:
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        out_data = {
            "records": new_history,
            "time_targets": time_targets
        }
        with open(filename,"w",encoding="utf-8") as file:
            json.dump(out_data,file,indent=2)
>>>>>>> 71743bf (target function added)
    except OSError as error:
        return f"Could not save to {filename}: {error}"
    return None

<<<<<<< HEAD
=======
def get_next_target_id():
    if not time_targets:
        return 1
    return max(t["target_id"] for t in time_targets)+1

def add_time_target(name:str, target_amount:float, start_date:str, end_date:str):
    """add time target; return the new target dict; return None on failure"""
    global time_targets
    if not (is_valid_date(start_date) and is_valid_date(end_date)):
        return None
    if start_date > end_date:
        return None
    new_t = {
        "target_id": get_next_target_id(),
        "name": name.strip(),
        "target_amount": to_money(target_amount),
        "start_date": start_date,
        "end_date": end_date
    }
    time_targets.append(new_t)
    save_history(full_history)
    return new_t

def get_all_time_targets():
    return time_targets.copy()

def calc_target_spending(records, start_date, end_date):
    """calculate the total spending in records that fall within [start_date, end_date]"""
    filtered = [r for r in records if start_date <= r["date"] <= end_date]
    total = sum(r["amount"] for r in filtered)
    return round(total,2)
>>>>>>> 71743bf (target function added)

def get_next_id(new_history):
    if not new_history:
        return 1
    return max(record["id"] for record in new_history) + 1

<<<<<<< HEAD

=======
>>>>>>> 71743bf (target function added)
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

<<<<<<< HEAD

=======
>>>>>>> 71743bf (target function added)
def add_records(history, entries):
    added = []
    rejected = 0
    for entry in entries:
        record = add_record(history, entry)
        if record:
            added.append(record)
        else:
<<<<<<< HEAD
            rejected += 1
    return added, rejected


=======
            rejected +=1
    return added, rejected

>>>>>>> 71743bf (target function added)
def find_by_id(records, record_id):
    for record in records:
        if record["id"] == record_id:
            return record
    return None

<<<<<<< HEAD

=======
>>>>>>> 71743bf (target function added)
def filter_by_description(records, text):
    text = text.lower()
    return [r for r in records if text in r["description"].lower()]

<<<<<<< HEAD

def filter_by_date(records, start=None, end=None):
    """Dates are YYYY-MM-DD, so plain string comparison orders them correctly."""
=======
def filter_by_date(records, start=None, end=None):
>>>>>>> 71743bf (target function added)
    result = records
    if start is not None:
        result = [r for r in result if r["date"] >= start]
    if end is not None:
        result = [r for r in result if r["date"] <= end]
    return result

<<<<<<< HEAD

=======
>>>>>>> 71743bf (target function added)
def filter_by_amount(records, min_amount=None, max_amount=None):
    result = records
    if min_amount is not None:
        result = [r for r in result if r["amount"] >= min_amount]
    if max_amount is not None:
        result = [r for r in result if r["amount"] <= max_amount]
    return result

<<<<<<< HEAD

def filter_by_budget_status(records, over_budget):
    """over_budget=True -> only entries where amount > budget; False -> the rest."""
    return [r for r in records if (r["amount"] > r["budget"]) == over_budget]


def query(records, description=None, date_from=None, date_to=None,
          min_amount=None, max_amount=None, over_budget=None, record_id=None):
    """Combine any filters; None means 'skip this filter'."""
=======
def filter_by_budget_status(records, over_budget):
    return [r for r in records if (r["amount"] > r["budget"]) == over_budget]

def query(records, description=None, date_from=None, date_to=None,
          min_amount=None, max_amount=None, over_budget=None, record_id=None):
>>>>>>> 71743bf (target function added)
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