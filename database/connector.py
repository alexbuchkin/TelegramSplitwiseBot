from typing import NoReturn
import sqlite3


class Connector:
    def __init__(self):
        """
        Establishes connection to database etc.
        """
        self.conn = sqlite3.connect('database.sqlite')
        self._create_database()

    def _create_database(self) -> NoReturn:
        """
        Create database
        Maybe we need to manually apply the migration mechanism instead of this method
        """
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys=on;")
        cursor.execute("CREATE TABLE IF NOT EXISTS users "
                       "(id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR, event_id INTEGER, "
                       "FOREIGN KEY (event_id) REFERENCES events(id), UNIQUE(name, event_id) ON CONFLICT REPLACE);")
        cursor.execute("CREATE TABLE IF NOT EXISTS events "
                       "(id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR);")
        cursor.execute("CREATE TABLE IF NOT EXISTS expenses "
                       "(id INTEGER PRIMARY KEY AUTOINCREMENT, description VARCHAR, payer VARCHAR, sum INTEGER, "
                       "FOREIGN KEY (payer) REFERENCES users(id));")
        cursor.execute("CREATE TABLE IF NOT EXISTS debtors "
                       "(id INTEGER PRIMARY KEY AUTOINCREMENT, expense_id INTEGER, name INTEGER, sum INTEGER, "
                       "FOREIGN KEY (expense_id) REFERENCES expenses(id), FOREIGN KEY (name) REFERENCES users(id));")
        cursor.execute("CREATE TABLE IF NOT EXISTS payments "
                       "(id INTEGER PRIMARY KEY AUTOINCREMENT, sender INTEGER, recipient INTEGER, sum INTEGER,"
                       "FOREIGN KEY (sender) REFERENCES users(id), FOREIGN KEY (recipient) REFERENCES users(id));")

    def save_event_info(
        self,
        event_name: str
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO events (name) VALUES(?);", (event_name,))
        self.conn.commit()
        return cursor.lastrowid

    def get_event_info(
        self,
        event_id: int
    ) -> dict:
        cursor = self.conn.cursor()
        event = cursor.execute("SELECT * FROM events WHERE id = ?;", (event_id,))
        return event.fetchone()

    def save_user_info(
        self,
        user_name: str,
        event_id: str
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (name, event_id) VALUES(?, ?);", (user_name, event_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_info(
        self,
        user_id: int
    ) -> dict:
        cursor = self.conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        return user.fetchone()

    def save_debtor_info(
        self,
        expense_id: str,
        debtor_name: str,
        sum_of_debt: int
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO debtors (expense_id, name, sum) VALUES(?, ?, ?);", (expense_id, debtor_name, sum_of_debt))
        self.conn.commit()
        return cursor.lastrowid

    def get_debtor_info(
        self,
        debt_id: int
    ) -> dict:
        cursor = self.conn.cursor()
        debt = cursor.execute("SELECT * FROM debts WHERE id = ?;", (debt_id,))
        return debt.fetchone()

    def save_expense_info(
        self,
        description: str,
        payer: int,
        sum_of_pay: int
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO expenses (description, payer, sum) VALUES(?, ?, ?);", (description, payer, sum_of_pay))
        self.conn.commit()
        return cursor.lastrowid

    def get_expense_info(
        self,
        expense_id: int
    ) -> dict:
        cursor = self.conn.cursor()
        expense = cursor.execute("SELECT * FROM debts WHERE id = ?;", (expense_id,))
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
        for table_name in ['payments', 'debtors', 'expenses', 'users', 'events']:
            cursor.execute(f'DROP TABLE IF EXISTS {table_name};')

    def clean_all_tables(
        self
    ):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM payments;")
        cursor.execute("DELETE FROM debtors;")
        cursor.execute("DELETE FROM expenses;")
        cursor.execute("DELETE FROM users;")
        cursor.execute("DELETE FROM events;")

    def __del__(self):
        """
        Closes connection etc.
        """
        self.conn.close()
