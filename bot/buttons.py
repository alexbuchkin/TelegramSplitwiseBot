from typing import List

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from database.types import User


def get_user_buttons(users: List[User]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(user.name, callback_data=user.id)]
        for user in users
    ]
    return InlineKeyboardMarkup(keyboard)
