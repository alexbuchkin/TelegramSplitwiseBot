import os

from bot import TelegramBot


if __name__ == '__main__':
    bot = TelegramBot(os.getenv('TOKEN'))
    bot.run()
