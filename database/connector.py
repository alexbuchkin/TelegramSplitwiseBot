from typing import NoReturn, Optional
import sqlite3

from datetime import datetime

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
        self.conn = sqlite3.connect('database.sqlite', check_same_thread=False)
        self._create_database()
        self.conn.commit()

    def _create_database(self) -> NoReturn:
        """
        Create database
        Maybe we need to manually apply the migration mechanism instead of this method
        """
        cursor = self.conn.cursor()
        cursor.execute('PRAGMA foreign_keys=on;')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id   INTEGER PRIMARY KEY,
                name VARCHAR
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id    VARCHAR PRIMARY KEY,
                name  VARCHAR NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user2event (
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                
                FOREIGN KEY (user_id)  REFERENCES users(id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id        INTEGER PRIMARY KEY,
                name      VARCHAR NOT NULL,
                lender_id INTEGER NOT NULL,
                event_id  INTEGER NOT NULL,
                sum       INTEGER NOT NULL,
                datetime  DATETIME NOT NULL,

                FOREIGN KEY (lender_id) REFERENCES users(id),
                FOREIGN KEY (event_id)  REFERENCES events(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debts (
                expense_id INTEGER NOT NULL,
                lender_id  INTEGER NOT NULL,
                debtor_id  INTEGER NOT NULL,
                sum        FLOAT NOT NULL,

                FOREIGN KEY (expense_id) REFERENCES expenses(id),
                FOREIGN KEY (lender_id)  REFERENCES users(id),
                FOREIGN KEY (debtor_id)  REFERENCES users(id)
            )
        ''')

    def create_event(
        self,
        event_name: str,
        event_token: str,
        user_id: int,
    ) -> NoReturn:
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO events (id, name) VALUES(?, ?);', (event_token, event_name))
            cursor.execute('INSERT INTO user2event (user_id, event_id) VALUES(?, ?);', (user_id, event_token))
            self.conn.commit()
        except sqlite3.Error:
            self.conn.rollback()
            raise

    def add_user_to_event(
        self,
        user_id: int,
        event_id: str
    ) -> NoReturn:
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO user2event (user_id, event_id) VALUES(?, ?);', (user_id, event_id))
            self.conn.commit()
        except sqlite3.Error:
            self.conn.rollback()
            raise

    def get_user_event(
        self,
        user_id: int,
        event_id: str
    ) -> list:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user2event WHERE user_id = ? AND event_id = ?;', (user_id, event_id))
        return cursor.fetchone()

    def get_event_info(
        self,
        event_id: str
    ) -> dict:
        cursor = self.conn.cursor()
        event = cursor.execute("SELECT * FROM events WHERE id = ?;", (event_id,))
        return event.fetchone()

    def save_user_info(
        self,
        user_id: int,
        user_name: str,
    ) -> NoReturn:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users VALUES(?, ?);", (user_id, user_name))
        self.conn.commit()

    def get_user_info_or_none(
        self,
        user_id: int
    ) -> Optional[dict]:
        cursor = self.conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        return None if user is None else {
            'id': user[0],
            'name': user[1],
        }

    def get_users_of_event(
            self,
            token: str) -> list:
        cursor = self.conn.cursor()
        users = cursor.execute("SELECT * "
                               "FROM users u, user2event u2e "
                               "WHERE u.id = u2e.user_id AND u2e.event_id = ?;",
                               (token,)).fetchall()
        return None if users is None else users

    def save_debt_info(
        self,
        expense_id: int,
        lender_id: int,
        debtor_id: int,
        sum_: float,
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO debts (expense_id, lender_id, debtor_id, sum) VALUES(?, ?, ?, ?);", (expense_id, lender_id, debtor_id, sum_))
        self.conn.commit()
        return cursor.lastrowid

    def get_debts_of_expense(
        self,
        expense_id: int
    ) -> dict:
        cursor = self.conn.cursor()
        debt = cursor.execute("SELECT * FROM debts WHERE expense_id = ?;", (expense_id,))
        return debt.fetchone()

    def save_expense_info(
        self,
        name: str,
        lender_id: int,
        event_id: str,
        sum_: float,
        datetime_: datetime
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO expenses (name, lender_id, event_id, sum, datetime) VALUES(?, ?, ?, ?, ?);",
                       (name, lender_id, event_id, sum_, datetime_))
        self.conn.commit()
        return cursor.lastrowid

    def get_expense_info(
        self,
        expense_id: int
    ) -> dict:
        cursor = self.conn.cursor()
        expense = cursor.execute("SELECT * FROM expenses WHERE id = ?;", (expense_id,))
        return expense.fetchone()

    def save_payments_info(
        self,
        sender: int,
        recipient: int,
        sum_of_pay: int
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO payments (sender, recipient, sum) VALUES(?, ?, ?);", (sender, recipient, sum_of_pay))
        self.conn.commit()
        return cursor.lastrowid

    def get_payments_info(
        self,
        expense_id: int
    ) -> dict:
        cursor = self.conn.cursor()
        payment = cursor.execute("SELECT * FROM payments WHERE id = ?;", (expense_id,))
        return payment.fetchone()

    def get_all_users(
        self
    ) -> list:
        cursor = self.conn.cursor()
        users = cursor.execute("SELECT * FROM users;")
        return users.fetchall()

    def get_all_events(
        self
    ) -> list:
        cursor = self.conn.cursor()
        events = cursor.execute("SELECT * FROM events;")
        return events.fetchall()

    def get_all_expenses(
        self
    ) -> list:
        cursor = self.conn.cursor()
        expense = cursor.execute("SELECT * FROM expenses;")
        return expense.fetchall()

    def get_all_debtors(
        self
    ) -> list:
        cursor = self.conn.cursor()
        debtors = cursor.execute("SELECT * FROM debtors;")
        return debtors.fetchall()

    def get_all_payments(
        self
    ) -> list:
        cursor = self.conn.cursor()
        payments = cursor.execute("SELECT * FROM payments;")
        return payments.fetchall()

    def drop_all_tables(
        self
    ):
        cursor = self.conn.cursor()
        for table_name in self.TABLES:
            cursor.execute(f'DROP TABLE IF EXISTS {table_name};')
        self.conn.commit()

    def clean_all_tables(
        self
    ):
        cursor = self.conn.cursor()
        for table_name in self.TABLES:
            cursor.execute(f'DELETE FROM {table_name};')
        self.conn.commit()

    def __del__(self):
        """
        Closes connection etc.
        """
        self.conn.close()
