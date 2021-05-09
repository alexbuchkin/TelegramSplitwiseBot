import logging
import uuid
from collections import deque, defaultdict
from datetime import datetime
from typing import NoReturn, List, Dict, Tuple

from database.connector import Connector
from database.types import (
    User,
    Event,
    Expense,
    Debt,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class SplitwiseApp:
    def __init__(self):
        """
        Creates database connector etc.
        """
        self.conn = Connector()

    def add_new_user(
        self,
        user: User,
    ) -> NoReturn:
        self.conn.save_user_info(user)

    def get_user_info(
        self,
        user_id: int,
    ) -> User:
        user_info = self.conn.get_user_info_or_none(user_id)
        if user_info is None:
            raise KeyError(f'User with id = {user_id} does not exist')
        return user_info

    def get_users_of_event(
        self,
        event_token: str,
    ) -> List[User]:
        users = self.conn.get_users_of_event(event_token)
        if not users:
            raise KeyError(f'There are no users in event with id = {event_token}')
        return users

    def get_event_info(
        self,
        event_token: str,
    ) -> Event:
        return self.conn.get_event_info(event_token)

    def user_exists(
        self,
        user_id: int,
    ) -> bool:
        return self.conn.get_user_info_or_none(user_id) is not None

    def create_event(
        self,
        user_id: int,
        event_name: str,
    ) -> str:
        """
        @return: token of the created event
        """
        event_token = str(uuid.uuid4())
        self.conn.create_event(
            event=Event(event_token, event_name),
            user_id=user_id,
        )
        log.info(f'User {user_id} created event "{event_name}" with token {event_token}')
        return event_token

    def add_expense(
        self,
        expense: Expense,
    ) -> int:
        """
        Adds expense to database
        Fields 'name', 'sum', 'lender_id', 'event_token' are required
        Fields 'id', 'datetime' will be ignored
        """
        expense.id = None  # will be filled after expense being added to db
        expense.datetime = datetime.now()
        return self.conn.save_expense_info(expense)

    def add_user_to_event(
        self,
        user_id: int,
        event_token: str
    ) -> NoReturn:
        self.conn.add_user_to_event(user_id, event_token)

    def user_participates_in_event(
        self,
        user_id: int,
        event_token: str,
    ) -> bool:
        return self.conn.user_participates_in_event(user_id, event_token)

    def get_expense(
        self,
        expense_id: int,
    ) -> Expense:
        return self.conn.get_expense_info(expense_id)

    def add_debt(
        self,
        debt: Debt,
    ) -> int:
        return self.conn.save_debt_info(debt)

    def get_final_transactions(
        self,
        event_token: str,
    ) -> Tuple[Dict, Dict]:
        """

        @param event_token: event token
        @return: tuple (lenders_info, debtors_info)
        """
        users = self.get_users_of_event(event_token)
        usernames = {user.id: user.name for user in users}
        users_balance = defaultdict(lambda: {
            'lent': 0,
            'owed': 0,
        })

        event_expenses = self.conn.get_event_expenses(event_token)
        for expense in event_expenses:
            users_balance[expense.lender_id]['lent'] += expense.sum

        event_debts = self.conn.get_debts_by_expenses([expense.id for expense in event_expenses])
        for debt in event_debts:
            users_balance[debt.debtor_id] += debt.sum
        lenders = [
            (user_balance['lent'] - user_balance['owed'], user_id)
            for user_id, user_balance in users_balance.items()
            if user_balance['lent'] > user_balance['owed']
        ]
        debtors = [
            (user_balance['owed'] - user_balance['lent'], user_id)
            for user_id, user_balance in users_balance.items()
            if user_balance['lent'] < user_balance['owed']
        ]
        lenders.sort(reverse=True)
        debtors.sort(reverse=True)

        lenders_deque = deque(lenders)
        debtors_deque = deque(debtors)

        lenders_info = defaultdict(list)
        debtors_info = defaultdict(list)
        lender_sum, lender_id = lenders_deque.popleft()
        debtor_sum, debtor_id = debtors_deque.popleft()
        while True:
            payment_sum = min(lender_sum, debtor_sum)
            lenders_info[lender_id].append((usernames[debtor_id], payment_sum))
            debtors_info[debtor_id].append((usernames[lender_id], payment_sum))

            lender_sum -= payment_sum
            if lender_sum == 0:
                if not lenders_deque:
                    break
                else:
                    lender_sum, lender_id = lenders_deque.popleft()

            debtor_sum -= payment_sum
            if debtor_sum == 0:
                if not debtors_deque:
                    break
                else:
                    debtor_sum, debtor_id = debtors_deque.popleft()

        if lenders_deque or debtors_deque:
            raise RuntimeError('Something went wrong while calculating final transactions')
        return dict(lenders_info), dict(debtors_info)
