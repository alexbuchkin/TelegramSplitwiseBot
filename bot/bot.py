from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)
from typing import NoReturn

from app.splitwise import SplitwiseApp


class TelegramBot:
    def __init__(
        self,
        token: str,
    ):
        self.splitwise = SplitwiseApp()
        self.updater = Updater(token)
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler("create_event", self.create_event_handler))
        dispatcher.add_handler(MessageHandler(Filters.text, self.text_handler))

    def run(self) -> NoReturn:
        """
        Starts main cycle
        """
        self.updater.start_polling()
        self.updater.idle()

    def text_handler(
        self,
        update: Update,
        _: CallbackContext
    ) -> NoReturn:
        id_ = update.effective_user.id
        name = update.effective_user.full_name

        if self.splitwise.user_exists(id_):
            name = self.splitwise.get_user_info(id_)['name']
            update.effective_chat.send_message(
                f'Привет, {name}! Ты уже был(а) здесь!'
            )
        else:
            self.splitwise.add_new_user(
                user_id=id_,
                name=name,
            )
            update.effective_chat.send_message(
                f'Привет, {name}! Ты здесь впервые!'
            )

    def create_event_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        event_name = ' '.join(context.args)
        event_token = self.splitwise.create_event(
            user_id=update.effective_user.id,
            event_name=event_name,
        )
        if event_token:
            update.effective_chat.send_message(
                f'Мероприятие "{event_name}" создано. Токен: {event_token}'
            )
        else:
            update.effective_chat.send_message(
                'Произошла ошибка при создании мероприятия. Попробуй ещё.'
            )
