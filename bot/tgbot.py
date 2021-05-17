from typing import NoReturn

from telegram.ext import (
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from bot import handlers
from app.splitwise import SplitwiseApp


class TelegramBot:
    def __init__(
        self,
        token: str,
        db_name: str = 'database.sqlite',
    ):
        self.splitwise = SplitwiseApp(db_name=db_name)
        self.updater = Updater(token)
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(handlers.MenuButtonsConversationHandler().get_conversation_handler())
        dispatcher.add_handler(CommandHandler('users_of_event', handlers.BeginningHandlers().users_of_event_handler))
        dispatcher.add_handler(CommandHandler('start', handlers.BeginningHandlers().start_handler))
        dispatcher.add_handler(CommandHandler('get_menu', handlers.BeginningHandlers().get_menu))
        dispatcher.add_handler(MessageHandler(Filters.text, handlers.BeginningHandlers().text_handler))

    def run(self) -> NoReturn:
        """
        Starts main cycle
        """
        self.updater.start_polling()
        self.updater.idle()
