from typing import NoReturn


class Connector:
    def __init__(self):
        """
        Establishes connection to database etc.
        """
        raise NotImplementedError

    def _create_database(self) -> NoReturn:
        """
        Create database
        Maybe we need to manually apply the migration mechanism instead of this method
        """
        raise NotImplementedError

    def get_user_info(
        self,
        user_id: int,
    ) -> dict:
        """
        Returns main information about user

        :param user_id: user id
        :return: user info
        """
        raise NotImplementedError

    def __del__(self):
        """
        Closes connection etc.
        """
        raise NotImplementedError
