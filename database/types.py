from collections import namedtuple

# see create_tables.sql for type info
User = namedtuple('User', ['id', 'name'])
Event = namedtuple('Event', ['token', 'name'])
Expense = namedtuple('Expense', ['id', 'name', 'sum', 'lender_id', 'event_token', 'datetime'])
Debt = namedtuple('Debt', ['expense_id', 'lender_id', 'debtor_id', 'sum'])
