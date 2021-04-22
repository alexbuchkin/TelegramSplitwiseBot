import logging
import uuid
import sys
from typing import NoReturn, List, Tuple, Optional

import sqlite3

from datetime import datetime

from database.connector import Connector


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class SplitwiseApp:
    def __init__(self):
        """
        Creates database connector etc.
        """
        self.conn = Connector()

    def add_new_group(
        self,
        group_id: int,
        group_name: str,
        users: List[int],
    ) -> NoReturn:
        """
        Creates new user group

        :param group_id: group id (must be unique)
        :param group_name: group name
        :param users: list of user ids of participants
        """
        raise NotImplementedError

    def add_new_user(
        self,
        user_id: int,
        name: str,
    ) -> NoReturn:
        self.conn.save_user_info(user_id, name)

    def get_user_info(
        self,
        user_id: str,
    ) -> dict:
        user_info = self.conn.get_user_info_or_none(user_id)
        if user_info is None:
            raise KeyError(f'User with id = {user_id} does not exist')
        return user_info

    def get_users_of_event(
        self,
        token: str,
    ) -> list:
        users = self.conn.get_users_of_event(token)
        if users is None or len(users) == 0:
            raise KeyError(f'There are no users in event with id = {token}')
        res = list()
        for user in users:
            user_dict = {'id': user[0], 'name': user[1]}
            res.append(user_dict)
        return res

    def get_event_info(
        self,
        token: str,
    ) -> dict:
        users = self.conn.get_event_info(token)
        return users

    def user_exists(
        self,
        user_id: int,
    ):
        return self.conn.get_user_info_or_none(user_id) is not None

    def create_event(
        self,
        user_id: int,
        event_name: str,
    ) -> Optional[str]:
        event_token = str(uuid.uuid4())
        try:
            self.conn.create_event(
                event_name=event_name,
                event_token=event_token,
                user_id=user_id,
            )
            log.info(f'User {user_id} created event "{event_name}" with token {event_token}')
            return event_token
        except sqlite3.Error as err:
            return None

    def add_expense(
        self,
        name: str,
        lender_id: int,
        event_id: str,
        sum_: float
    ) -> int:
        time = datetime.now()
        id_ = self.conn.save_expense_info(name, lender_id, event_id, sum_, time)
        return id_

    def add_user_to_event(
        self,
        user_id: int,
        event_id: str
    ) -> NoReturn:
        self.conn.add_user_to_event(user_id, event_id)

    def get_user_event(
        self,
        user_id: int,
        event_id: str
    ) -> list:
        return self.conn.get_user_event(user_id, event_id)

    def get_expense(
        self,
        expense_id: int
    ) -> dict:
        expense = self.conn.get_expense_info(expense_id)
        return expense

    def add_equal_expense(
        self,
        group_id: int,
        lender_id: int,
        lent_sum: int,
        debtors: List[int],
        expense_name: str,
        ts: int,
    ) -> NoReturn:
        """
        Adds an expense where all participants paid equally

        :param group_id: group id
        :param lender_id: id of a person who paid
        :param lent_sum: sum that lender paid
        :param debtors: list of debtor ids
        :param expense_name: some notes about the expense
        :param ts: time of expense adding in unix timestamp format
        """
        raise NotImplementedError

    def add_debt(
            self,
            expense_id: int,
            lender_id: int,
            debtor_id: int,
            sum_: float,
    ) -> int:
        return self.conn.save_debt_info(expense_id, lender_id, debtor_id, sum_)

    def get_debts_of_expense(
            self,
            expense_id: int,
    ) -> dict:
        return self.conn.get_debts_of_expense(expense_id)

    def show_debts(
        self,
        token: str,
    ) -> dict:
        users = self.get_users_of_event(token)
        users_balance = dict()
        for user in users:
            users_balance[user['id']] = 0.

        users_expenses = self.conn.get_event_expenses(token)
        expenses_id = list()
        for ue in users_expenses:
            expenses_id.append(ue[0])
            users_balance[ue[1]] -= ue[2]

        debts = self.conn.get_debts_of_expenses(expenses_id)
        for debt in debts:
            users_balance[debt[0]] += debt[1]

        return users_balance
