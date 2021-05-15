from collections import namedtuple
from dataclasses import make_dataclass

# see create_tables.sql for type info
User = make_dataclass('User', ['id', 'name'])
Event = make_dataclass('Event', ['token', 'name'])
Expense = make_dataclass('Expense', ['id', 'name', 'sum', 'lender_id', 'event_token', 'datetime'])
Debt = make_dataclass('Debt', ['expense_id', 'lender_id', 'debtor_id', 'sum'])
