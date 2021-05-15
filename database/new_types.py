from dataclasses import dataclass
import datetime as dt

# see create_tables.sql for type info


@dataclass
class User:
    id:   int = None
    name: str = None


@dataclass
class Event:
    token: str = None
    name:  str = None


@dataclass
class Expense:
    id:          int = None
    name:        str = None
    sum:         int = None
    lender_id:   int = None
    event_token: str = None
    datetime:    dt.datetime = None


@dataclass
class Debt:
    expense_id: int = None
    lender_id:  int = None
    debtor_id:  int = None
    sum:        int = None
