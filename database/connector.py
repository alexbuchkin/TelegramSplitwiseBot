from datetime import datetime
from pathlib import Path
from typing import NoReturn, Optional, List, Tuple, Dict

import sqlite3


class Connector:
    TABLES = [
        'debts',
        'user2event',
        'expenses',
        'users',
        'events',
    ]

    def __init__(self):
        """
        Establishes connection to database etc.
        """
        self.conn = sqlite3.connect('database.sqlite', isolation_level='EXCLUSIVE')
        self._create_database()
        self.conn.commit()

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
        event_name: str,
        event_token: str,
        user_id: int,
    ) -> NoReturn:
        try:
            cursor = self.conn.cursor()
            cursor.execute('BEGIN')
            cursor.execute('INSERT INTO events (token, name) VALUES(?, ?)', (event_token, event_name))
            cursor.execute('INSERT INTO user2event (user_id, event_token) VALUES(?, ?)', (user_id, event_token))
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
    ) -> Tuple:
        cursor = self.conn.cursor()
        event = cursor.execute('SELECT * FROM events WHERE id = ?', (event_token,)).fetchone()
        if not event:
            raise KeyError(f'Event with token {event_token} does not exist')
        return event

    def save_user_info(
        self,
        user_id: int,
        user_name: str,
    ) -> NoReturn:
        try:
            cursor = self.conn.cursor()
            cursor.execute('BEGIN')
            cursor.execute('INSERT INTO users VALUES(?, ?)', (user_id, user_name))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def get_user_info_or_none(
        self,
        user_id: int,
    ) -> Optional[Dict]:
        cursor = self.conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return None if user is None else {
            'id': user[0],
            'name': user[1],
        }

    def get_users_of_event(
        self,
        event_token: str,
    ) -> List:
        cursor = self.conn.cursor()
        users = cursor.execute(
            'SELECT * '
            'FROM users u, user2event u2e '
            'WHERE u.id = u2e.user_id AND u2e.event_token = ?',
            (event_token,)
        ).fetchall()
        return users or []

    def save_debt_info(
        self,
        expense_id: int,
        lender_id: int,
        debtor_id: int,
        sum_: int,
    ) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO debts (expense_id, lender_id, debtor_id, sum) VALUES(?, ?, ?, ?)',
                (expense_id, lender_id, debtor_id, sum_),
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def save_expense_info(
        self,
        name: str,
        lender_id: int,
        event_token: str,
        sum_: int,
        datetime_: datetime,
    ) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO expenses (name, lender_id, event_token, sum, datetime) VALUES(?, ?, ?, ?, ?)',
                           (name, lender_id, event_token, sum_, datetime_))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def get_expense_info(
        self,
        expense_id: int,
    ) -> tuple:
        cursor = self.conn.cursor()
        expense = cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        return expense.fetchone()

    def get_event_expenses(
        self,
        event_token: str,
    ) -> List[Tuple]:
        cursor = self.conn.cursor()
        expense = cursor.execute('SELECT * FROM expenses WHERE event_token = ?', (event_token,))
        return expense.fetchall()

    def __del__(self):
        """
        Closes connection etc.
        """
        self.conn.close()
