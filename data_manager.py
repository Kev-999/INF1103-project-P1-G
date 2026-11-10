"""
Spending tracker, SQLite version.

Tables:
  expenses     (id, date, description, amount, budget, ai_response)
  time_targets (target_id, name, target_amount, start_date, end_date)
"""

import json
import os
import sqlite3
from dataclasses import dataclass, asdict
from typing import Optional

DB_FILE = os.path.join("data", "spending.db")
JSON_FILE = os.path.join("data", "spending.json")   # old file, only used for import
SORT_OPTIONS = ("date", "amount", "description", "id")

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,
    description TEXT NOT NULL,
    amount      REAL NOT NULL,
    budget      REAL NOT NULL,
    ai_response TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS time_targets (
    target_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    target_amount REAL NOT NULL,
    start_date    TEXT NOT NULL,
    end_date      TEXT NOT NULL
);
"""


# ---------- small helpers ----------

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


# ---------- data classes (unchanged) ----------

@dataclass
class Expense:
    id: int
    date: str
    description: str
    amount: float
    budget: float
    ai_response: str = ""

    @classmethod
    def from_raw(cls, raw) -> Optional["Expense"]:
        """Build a valid Expense from a dict, or return None if it's unusable."""
        try:
            expense = cls(
                id=int(raw["id"]),
                date=str(raw["date"]).strip(),
                description=str(raw["description"]).strip(),
                amount=to_money(raw["amount"]),
                budget=to_money(raw["budget"]),
                ai_response=str(raw.get("ai_response") or "").strip(),
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            return None
        if not expense.description or expense.amount <= 0:
            return None
        if not is_valid_date(expense.date):
            return None
        return expense

    @property
    def over_budget(self) -> bool:
        return self.amount > self.budget

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TimeTarget:
    target_id: int
    name: str
    target_amount: float
    start_date: str
    end_date: str

    @classmethod
    def from_raw(cls, raw) -> Optional["TimeTarget"]:
        try:
            target = cls(
                target_id=int(raw["target_id"]),
                name=str(raw["name"]).strip(),
                target_amount=to_money(raw["target_amount"]),
                start_date=str(raw["start_date"]).strip(),
                end_date=str(raw["end_date"]).strip(),
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            return None
        if not (is_valid_date(target.start_date) and is_valid_date(target.end_date)):
            return None
        if target.start_date > target.end_date:
            return None
        return target

    def contains(self, date: str) -> bool:
        return self.start_date <= date <= self.end_date

    def spent(self, expenses) -> float:
        """Total spending from `expenses` that falls inside this target's range."""
        return round(sum(e.amount for e in expenses if self.contains(e.date)), 2)

    def remaining(self, expenses) -> float:
        return round(self.target_amount - self.spent(expenses), 2)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------- the tracker: owns the data and the database connection ----------

class ExpenseTracker:
    def __init__(self, filename=DB_FILE):
        self.filename = filename
        self.expenses: list[Expense] = []
        self.time_targets: list[TimeTarget] = []
        self._conn: Optional[sqlite3.Connection] = None

    # ----- connection / loading -----

    def _connect(self):
        if self._conn is None:
            os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)
            conn = sqlite3.connect(self.filename)
            conn.row_factory = sqlite3.Row
            conn.executescript(SCHEMA)     # creates the tables on first run
            self._conn = conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def load(self):
        """Read everything from the database. Returns a list of warning strings."""
        self.expenses.clear()
        self.time_targets.clear()
        try:
            self._connect()
            expense_rows = self._conn.execute("SELECT * FROM expenses ORDER BY id").fetchall()
            target_rows = self._conn.execute("SELECT * FROM time_targets ORDER BY target_id").fetchall()
        except sqlite3.Error as error:
            return [f"Could not open database {self.filename}: {error}"]

        skipped = 0
        for row in expense_rows:
            expense = Expense.from_raw(dict(row))
            if expense is None:
                skipped += 1
            else:
                self.expenses.append(expense)

        skipped_targets = 0
        for row in target_rows:
            target = TimeTarget.from_raw(dict(row))
            if target is None:
                skipped_targets += 1
            else:
                self.time_targets.append(target)

        warnings = []
        if skipped:
            warnings.append(f"Skipped {skipped} bad record(s) in {self.filename}.")
        if skipped_targets:
            warnings.append(f"Skipped {skipped_targets} bad target(s) in {self.filename}.")
        return warnings

    # ----- one-time import from the old JSON file -----

    def import_from_json(self, json_path=JSON_FILE):
        """Copy records and targets from the old JSON file into the database.
        Keeps the original ids. Safe to run twice: rows that already exist are skipped.
        Returns a list of warning strings."""
        try:
            self._connect()
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return [f"{json_path} not found, nothing to import."]
        except (OSError, ValueError, sqlite3.Error) as error:
            return [f"Could not import {json_path}: {error}"]

        if isinstance(data, list):                       # very old format
            raw_rows, raw_targets = data, []
        elif isinstance(data, dict):
            raw_rows = data.get("records", [])
            raw_targets = data.get("time_targets", [])
        else:
            return [f"{json_path} has an unexpected format."]

        skipped = 0
        with self._conn:                                 # one transaction
            for raw in raw_rows:
                e = Expense.from_raw(raw)
                if e is None:
                    skipped += 1
                    continue
                self._conn.execute(
                    "INSERT OR IGNORE INTO expenses "
                    "(id, date, description, amount, budget, ai_response) VALUES (?,?,?,?,?,?)",
                    (e.id, e.date, e.description, e.amount, e.budget, e.ai_response),
                )
            for raw in raw_targets:
                t = TimeTarget.from_raw(raw)
                if t is None:
                    skipped += 1
                    continue
                self._conn.execute(
                    "INSERT OR IGNORE INTO time_targets "
                    "(target_id, name, target_amount, start_date, end_date) VALUES (?,?,?,?,?)",
                    (t.target_id, t.name, t.target_amount, t.start_date, t.end_date),
                )

        warnings = self.load()                           # refresh the in-memory lists
        if skipped:
            warnings.append(f"Skipped {skipped} bad row(s) while importing.")
        return warnings

    # ----- expenses -----

    def add_expense(self, entry) -> Optional[Expense]:
        """Validate `entry` (a dict), save it to the database, and return the Expense.
        Returns None if the data is invalid or the database write fails."""
        if not isinstance(entry, dict):
            return None
        expense = Expense.from_raw({
            "id": 0,                                     # placeholder; the database assigns the real id
            "date": entry.get("date"),
            "description": entry.get("description"),
            "amount": entry.get("amount"),
            "budget": entry.get("budget"),
            "ai_response": entry.get("ai_response"),
        })
        if expense is None:
            return None
        try:
            with self._conn:                             # commits on success, rolls back on error
                cursor = self._conn.execute(
                    "INSERT INTO expenses (date, description, amount, budget, ai_response) "
                    "VALUES (?,?,?,?,?)",
                    (expense.date, expense.description, expense.amount,
                     expense.budget, expense.ai_response),
                )
        except sqlite3.Error:
            return None
        expense.id = cursor.lastrowid
        self.expenses.append(expense)
        return expense

    def add_expenses(self, entries):
        """Returns (list_of_added_expenses, number_rejected)."""
        added, rejected = [], 0
        for entry in entries:
            expense = self.add_expense(entry)
            if expense:
                added.append(expense)
            else:
                rejected += 1
        return added, rejected

    def find_by_id(self, expense_id) -> Optional[Expense]:
        return next((e for e in self.expenses if e.id == expense_id), None)

    def query(self, description=None, category=None, date_from=None, date_to=None,
              min_amount=None, max_amount=None, over_budget=None, record_id=None,
              sort_by="date", descending=False):
        """Combine any filters; None means 'skip this filter'."""
        result = self.expenses
        if record_id is not None:
            match = self.find_by_id(record_id)
            result = [match] if match else []
        if description:
            text = description.lower()
            result = [e for e in result if text in e.description.lower()]
        if category:
            category = category.lower()
            result = [e for e in result if e.ai_response.lower() == category]
        if date_from is not None:
            result = [e for e in result if e.date >= date_from]
        if date_to is not None:
            result = [e for e in result if e.date <= date_to]
        if min_amount is not None:
            result = [e for e in result if e.amount >= min_amount]
        if max_amount is not None:
            result = [e for e in result if e.amount <= max_amount]
        if over_budget is not None:
            result = [e for e in result if e.over_budget == over_budget]
        return self._sort(result, sort_by, descending)

    @staticmethod
    def _sort(expenses, sort_by="date", descending=False):
        """Ties are broken by id so the order is stable."""
        if sort_by not in SORT_OPTIONS:
            sort_by = "date"
        if sort_by == "description":
            key = lambda e: (e.description.lower(), e.id)
        else:
            key = lambda e: (getattr(e, sort_by), e.id)
        return sorted(expenses, key=key, reverse=descending)

    # ----- time targets -----

    def add_time_target(self, name, target_amount, start_date, end_date) -> Optional[TimeTarget]:
        """Validate, save to the database, and return the TimeTarget (or None on failure)."""
        target = TimeTarget.from_raw({
            "target_id": 0,                              # placeholder; the database assigns the real id
            "name": name,
            "target_amount": target_amount,
            "start_date": start_date,
            "end_date": end_date,
        })
        if target is None:
            return None
        try:
            with self._conn:
                cursor = self._conn.execute(
                    "INSERT INTO time_targets (name, target_amount, start_date, end_date) "
                    "VALUES (?,?,?,?)",
                    (target.name, target.target_amount, target.start_date, target.end_date),
                )
        except sqlite3.Error:
            return None
        target.target_id = cursor.lastrowid
        self.time_targets.append(target)
        return target

    def target_progress(self, target: TimeTarget):
        """Returns (spent, remaining) for a target using this tracker's expenses."""
        return target.spent(self.expenses), target.remaining(self.expenses)