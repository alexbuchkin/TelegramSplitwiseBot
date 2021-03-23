from typing import NoReturn

from app.splitwise import SplitwiseApp


class TelegramBot:
    def __init__(self):
        self.splitwise = SplitwiseApp()
        raise NotImplementedError

    def run(self) -> NoReturn:
        """
        Starts main cycle
        """
        raise NotImplementedError
