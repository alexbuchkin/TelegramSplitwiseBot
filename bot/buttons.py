from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


def get_user_buttons(users: list):
    keyboard = list()
    for user in users:
        line = [InlineKeyboardButton(user['name'], callback_data=user['id'])]
        keyboard.append(line)
    return InlineKeyboardMarkup(keyboard)
