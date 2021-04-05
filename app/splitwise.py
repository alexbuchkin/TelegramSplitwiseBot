from typing import NoReturn, List, Tuple

from database.connector import Connector


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

    def user_exists(
        self,
        user_id: int,
    ):
        return self.conn.get_user_info_or_none(user_id) is not None

    def add_expense(
        self,
        group_id: int,
        lender_id: int,
        lent_sum: int,
        debtors: List[Tuple[int, int]],
        expense_name: str,
        ts: int,
    ) -> NoReturn:
        """
        Adds a simple expense

        :param group_id: group id
        :param lender_id: id of a person who paid
        :param lent_sum: sum that lender paid
        :param debtors: list of tuples (debtor id, sum of debt)
        :param expense_name: some notes about the expense
        :param ts: time of expense adding in unix timestamp format
        """
        raise NotImplementedError

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

    def show_debts(
        self,
        group_id: int,
    ) -> str:
        """
        Returns full information about debts for chosen group
        :param group_id: group id
        :return: debts info
        """
        raise NotImplementedError
