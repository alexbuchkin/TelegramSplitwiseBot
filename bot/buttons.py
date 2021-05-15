from typing import List

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup
from telegram import KeyboardButton
import constants

from database.new_types import User, Event


def get_user_buttons(users: List[User]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(user.name, callback_data=user.id)]
        for user in users
    ]
    keyboard.append([InlineKeyboardButton("Закончить", callback_data=constants.CANCEL)])
    return InlineKeyboardMarkup(keyboard)


def get_event_buttons(events: List[Event]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(event.name, callback_data=event.token)]
        for event in events
    ]
    keyboard.append([InlineKeyboardButton('Назад', callback_data=constants.CANCEL)])
    return InlineKeyboardMarkup(keyboard)


def get_cancel_button() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton('Назад', callback_data='cancel')]]
    return InlineKeyboardMarkup(keyboard)


def get_menu_keyboard() -> InlineKeyboardMarkup:
    select_event = InlineKeyboardButton('Выбрать мероприятие', callback_data=constants.SELECT_EVENT)
    join_event = InlineKeyboardButton('Присоединиться к меропиятию', callback_data=constants.JOIN_EVENT)
    create_event = InlineKeyboardButton('Создать мероприятие', callback_data=constants.CREATE_EVENT)

    keyboard = InlineKeyboardMarkup([[select_event], [join_event], [create_event]])
    return keyboard


def get_menu_keyboard() -> InlineKeyboardMarkup:
    select_event = InlineKeyboardButton('Выбрать мероприятие', callback_data=constants.SELECT_EVENT)
    join_event = InlineKeyboardButton('Присоединиться к меропиятию', callback_data=constants.JOIN_EVENT)
    create_event = InlineKeyboardButton('Создать мероприятие', callback_data=constants.CREATE_EVENT)

    keyboard = InlineKeyboardMarkup([[select_event], [join_event], [create_event]])
    return keyboard


def get_empty_keyboard():
    return InlineKeyboardMarkup([])


def get_event_commands_keyboard () -> InlineKeyboardMarkup:
    add_expense = InlineKeyboardButton('Добавить трату', callback_data=constants.ADD_EXPENSE)
    sho_debts = InlineKeyboardButton('Показать мои долги', callback_data=constants.SHOW_DEBTS)
    cancel = InlineKeyboardButton('Назад', callback_data=constants.CANCEL)

    keyboard = InlineKeyboardMarkup([[add_expense], [sho_debts], [cancel]])
    return keyboard
