from typing import NoReturn

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
    CallbackQueryHandler,
    ConversationHandler,
)

import buttons

import handlers

from app.splitwise import SplitwiseApp
from database.new_types import (
    User,
)


class TelegramBot:
    def __init__(
        self,
        token: str,
    ):
        self.splitwise = SplitwiseApp()
        self.updater = Updater(token)
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(handlers.MenuButtonsConversationHandler().get_conversation_handler())
        dispatcher.add_handler(handlers.CreateEventConversation().get_conversation_handler())
        dispatcher.add_handler(handlers.JoinEventConversation().get_conversation_handler())
        dispatcher.add_handler(handlers.SelectEventConversation().get_conversation_handler())
        dispatcher.add_handler(CommandHandler('users_of_event', self.users_of_event_handler))
        dispatcher.add_handler(CommandHandler('start', self.start_handler))
        dispatcher.add_handler(CommandHandler('get_menu', self.get_menu))
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
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Введи команду')

    def callback_query_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Введи команду')

    def get_menu(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())

    def users_of_event_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        token = context.args[0]
        users = self.splitwise.get_users_of_event(token)
        update.effective_chat.send_message(str(users))

    def start_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        id_ = update.effective_user.id
        name = update.effective_user.username

        if self.splitwise.user_exists(id_):
            name = self.splitwise.get_user_info(id_).name
            update.effective_chat.send_message(f'Привет, {name}! Ты уже был(а) здесь!', reply_markup=buttons.get_commands_keyboard())
        else:
            self.splitwise.add_new_user(User(id_, name))
            update.effective_chat.send_message(f'Привет, {name}! Ты здесь впервые!', reply_markup=buttons.get_commands_keyboard())



