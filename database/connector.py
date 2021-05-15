from pathlib import Path
from typing import NoReturn, Optional, List

import sqlite3

from database.new_types import (
    User,
    Event,
    Expense,
    Debt,
)


class Connector:
    def __init__(self):
        """
        Establishes connection to database etc.
        """
        self.conn = sqlite3.connect(
            'database.sqlite',
            check_same_thread=False,
            isolation_level='EXCLUSIVE',
        )
        self._create_database()

    def _create_database(self) -> NoReturn:
        """
        Create database
        Maybe we need to manually apply the migration mechanism instead of this method
        """
        cursor = self.conn.cursor()
        current_dir = Path(__file__).resolve().parent
        try:
            with open(current_dir.joinpath('sql/create_tables.sql'), 'r') as file:
                cursor.executescript(file.read())
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def create_event(
        self,
        event: Event,
        user_id: int,
    ) -> NoReturn:
        """
        User with user_id creates an event and joins it
        Event token must be provided, it has to be unique
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('BEGIN')
            cursor.execute('INSERT INTO events (token, name) VALUES(?, ?)', (event.token, event.name))
            cursor.execute('INSERT INTO user2event (user_id, event_token) VALUES(?, ?)', (user_id, event.token))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def add_user_to_event(
        self,
        user_id: int,
        event_token: str,
    ) -> NoReturn:
        try:
            cursor = self.conn.cursor()
            cursor.execute('BEGIN')
            cursor.execute('INSERT INTO user2event (user_id, event_token) VALUES(?, ?)', (user_id, event_token))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def user_participates_in_event(
        self,
        user_id: int,
        event_token: str,
    ) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user2event WHERE user_id = ? AND event_token = ?', (user_id, event_token))
        return bool(cursor.fetchone())

    def get_event_info(
        self,
        event_token: str,
    ) -> Event:
        cursor = self.conn.cursor()
        event = cursor.execute('SELECT * FROM events WHERE token = ?', (event_token,)).fetchone()
        if not event:
            raise KeyError(f'Event with token {event_token} does not exist')
        return Event(*event)

    def save_user_info(
        self,
        user: User,
    ) -> NoReturn:
        try:
            cursor = self.conn.cursor()
            cursor.execute('BEGIN')
            cursor.execute('INSERT INTO users VALUES(?, ?)', (user.id, user.name))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def get_user_info_or_none(
        self,
        user_id: int,
    ) -> Optional[User]:
        cursor = self.conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return None if user is None else User(*user)

    def get_users_of_event(
        self,
        event_token: str,
    ) -> List[User]:
        cursor = self.conn.cursor()
        users = cursor.execute(
            'SELECT * '
            'FROM users u, user2event u2e '
            'WHERE u.id = u2e.user_id AND u2e.event_token = ?',
            (event_token,)
        ).fetchall()
        return [User(*user[:2]) for user in (users or [])]

    def save_debt_info(
        self,
        debt: Debt,
    ) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO debts (expense_id, lender_id, debtor_id, sum) VALUES(?, ?, ?, ?)',
                (debt.expense_id, debt.lender_id, debt.debtor_id, debt.sum),
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def save_expense_info(
        self,
        expense: Expense,
    ) -> int:
        """
        Add new expense to database
        expense.id will be ignored
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO expenses (name, sum, lender_id, event_token, datetime) VALUES(?, ?, ?, ?, ?)',
                (expense.name, expense.sum, expense.lender_id, expense.event_token, expense.datetime),
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def get_expense_info(
        self,
        expense_id: int,
    ) -> Expense:
        cursor = self.conn.cursor()
        expense = cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        return Expense(*expense.fetchone())

    def get_event_expenses(
        self,
        event_token: str,
    ) -> List[Expense]:
        cursor = self.conn.cursor()
        expenses = cursor.execute('SELECT * FROM expenses WHERE event_token = ?', (event_token,))
        return [Expense(*item) for item in expenses.fetchall()]

    def get_debts_by_expenses(
        self,
        expense_ids: List[int],
    ) -> List[Debt]:
        cursor = self.conn.cursor()
        sql_query = 'SELECT * FROM debts WHERE expense_id in ({seq})'.format(
            seq=','.join('?' * len(expense_ids))
        )
        return [Debt(*item) for item in cursor.execute(sql_query, expense_ids).fetchall()]

    def get_user_events(
            self,
            user_id: int
    ) -> List[Event]:
        cursor = self.conn.cursor()
        events = cursor.execute(
            'SELECT e.token, e.name '
            'FROM events e, user2event ev '
            'WHERE ev.user_id = ? AND ev.event_token = e.token', (user_id,))
        return [Event(*item) for item in events.fetchall()]

    def __del__(self):
        """
        Closes connection etc.
        """
        self.conn.close()
