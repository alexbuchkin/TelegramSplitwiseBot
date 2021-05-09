from telegram import Update
from telegram import ParseMode
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
    CallbackQueryHandler,
)
from typing import NoReturn

from app.splitwise import SplitwiseApp
from bot import buttons
from database.types import (
    User,
    Expense,
    Debt,
)


class TelegramBot:
    def __init__(
        self,
        token: str,
    ):
        self.splitwise = SplitwiseApp()
        self.updater = Updater(token)
        self.expenses = dict()
        self.debts = dict()
        self.states = dict()
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler('create_event', self.create_event_handler))
        dispatcher.add_handler(CommandHandler('add_expense', self.add_expense_handler))
        dispatcher.add_handler(CommandHandler('show_debts', self.show_debts_handler))
        dispatcher.add_handler(CommandHandler('users_of_event', self.users_of_event_handler))
        dispatcher.add_handler(CommandHandler('join_event', self.join_event_handler))
        dispatcher.add_handler(CommandHandler('start', self.start_handler))
        dispatcher.add_handler(CallbackQueryHandler(self.callback_query_handler))
        dispatcher.add_handler(MessageHandler(Filters.text, self.text_handler))

    def run(self) -> NoReturn:
        """
        Starts main cycle
        """
        self.updater.start_polling()
        self.updater.idle()

    def callback_query_handler(self, update: Update, _):
        if update.effective_user.id not in self.states:
            self.states[update.effective_user.id] = BeginningState(self)
        self.states[update.effective_user.id].callback_query_handler(update)

    def text_handler(
        self,
        update: Update,
        context: CallbackContext
    ) -> NoReturn:
        if update.effective_user.id not in self.states:
            self.states[update.effective_user.id] = BeginningState(self)
        self.states[update.effective_user.id].text_handler(update, context)

    def users_of_event_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        token = context.args[0]
        users = self.splitwise.get_users_of_event(token)
        update.effective_chat.send_message(str(users))

    def join_event_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        if update.effective_user.id not in self.states:
            self.states[update.effective_user.id] = BeginningState(self)
        self.states[update.effective_user.id].join_event_handler(update, context)

    def add_expense_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        if update.effective_user.id not in self.states:
            self.states[update.effective_user.id] = BeginningState(self)
        self.states[update.effective_user.id].add_expense_handler(update, context)

    def show_debts_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        if update.effective_user.id not in self.states:
            self.states[update.effective_user.id] = BeginningState(self)
        self.states[update.effective_user.id].show_debts_handler(update, context)

    def create_event_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        if update.effective_user.id not in self.states:
            self.states[update.effective_user.id] = BeginningState(self)
        self.states[update.effective_user.id].create_event_handler(update, context)

    def start_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        id_ = update.effective_user.id
        name = update.effective_user.full_name

        if self.splitwise.user_exists(id_):
            name = self.splitwise.get_user_info(id_).name
            update.effective_chat.send_message(
                f'Привет, {name}! Ты уже был(а) здесь!'
            )
        else:
            self.splitwise.add_new_user(User(id_, name))
            update.effective_chat.send_message(
                f'Привет, {name}! Ты здесь впервые!'
            )


class BeginningState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def text_handler(
        self,
        update: Update,
        _: CallbackContext
    ) -> NoReturn:
        update.effective_chat.send_message(
            'Введи команду а не вот это вот все.'
        )

    def callback_query_handler(self, update: Update):
        update.effective_chat.send_message('Хватит на кнопочки тыкать. Введи лучше команду')

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        self.bot_.states[update.effective_user.id] = EventNameState(self.bot_)
        update.effective_chat.send_message('Введи название мероприятия')

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        self.bot_.states[update.effective_user.id] = JoinEventTokenState(self.bot_)
        update.effective_chat.send_message('Введи токен мероприятия')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        self.bot_.states[update.effective_user.id] = ExpenseTokenState(self.bot_)
        update.effective_chat.send_message('Введи токен мероприятия')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        self.bot_.states[update.effective_user.id] = ShowDebtsTokenState(self.bot_)
        update.effective_chat.send_message('Введи токен мероприятия')


class ShowDebtsTokenState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Не то!')

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        token = update.effective_message.text
        user_id = update.effective_user.id
        lenders_info, debtors_info = self.bot_.splitwise.get_final_transactions(token)
        if user_id in debtors_info:
            update.effective_chat.send_message('Вы должны: \n' + str(debtors_info[user_id]))
        elif user_id in lenders_info:
            update.effective_chat.send_message('Вам должны: \n' + str(lenders_info[user_id]))
        else:
            update.effective_chat.send_message('Вы никому не должны и вам никто не должен')
        del self.bot_.states[update.effective_user.id]

    def callback_query_handler(self, update: Update):
        update.effective_chat.send_message("Давай токен говори")

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен.')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен.')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен.')


class JoinEventTokenState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Не то!')

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        event_token = update.effective_message.text
        user_id = update.effective_user.id
        try:
            event = self.bot_.splitwise.get_event_info(event_token)
        except KeyError:
            del self.bot_.states[update.effective_user.id]
            update.effective_chat.send_message('Мероприятия с таким токеном не существует.')
            return
        if self.bot_.splitwise.user_participates_in_event(user_id, event_token):
            del self.bot_.states[update.effective_user.id]
            update.effective_chat.send_message('Не прокатит! Ты уже зарегистрирован в мероприятии')
            return
        self.bot_.splitwise.add_user_to_event(user_id, event_token)
        del self.bot_.states[update.effective_user.id]
        update.effective_chat.send_message('Ты успешно присоединился к мероприятию')

    def callback_query_handler(self, update: Update):
        update.effective_chat.send_message('Давай токен говори')

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен.')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен.')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен.')


class EventNameState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Не то!')

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        event_name = update.effective_message.text
        event_token = self.bot_.splitwise.create_event(
            user_id=update.effective_user.id,
            event_name=event_name,
        )
        update.effective_chat.send_message(
            f'Мероприятие "{event_name}" создано. Токен: `{event_token}`',
            parse_mode=ParseMode.MARKDOWN
        )
        del self.bot_.states[update.effective_user.id]

    def callback_query_handler(self, update: Update):
        update.effective_chat.send_message('Давай имя говори')

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужно имя.')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужно имя.')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужно имя.')


class ExpenseTokenState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Не то!')

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        event_token = update.effective_message.text
        user_id = update.effective_user.id
        try:
            event = self.bot_.splitwise.get_event_info(event_token)
        except KeyError:
            del self.bot_.states[update.effective_user.id]
            update.effective_chat.send_message('Мероприятия с таким токеном не существует. Повторите создание траты.')
            return
        expense = Expense(None, None, None, None, None, None)
        expense.event_token = event_token
        expense.lender_id = user_id
        self.bot_.expenses[user_id] = expense
        self.bot_.states[update.effective_user.id] = ExpenseNameState(self.bot_)
        update.effective_chat.send_message('Введи название траты.')

    def callback_query_handler(self, update: Update):
        update.effective_chat.send_message('Нужен токен мероприятия')

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен мероприятия.')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен мероприятия.')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужен токен мероприятия.')


class ExpenseNameState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Не то!')

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        expense_name = update.effective_message.text
        user_id = update.effective_user.id
        self.bot_.expenses[user_id].name = expense_name
        self.bot_.states[update.effective_user.id] = ExpenseSumState(self.bot_)
        update.effective_chat.send_message('Введи потраченную сумму.')

    def callback_query_handler(self, update: Update):
        update.effective_chat.send_message('Название траты говори')

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Имя')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мне нужно имя')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Говори имя')


class ExpenseSumState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Не то!')

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        # let's use integer division and forget about cents for some time
        expense_sum = update.effective_message.text
        user_id = update.effective_user.id
        try:
            expense_sum = int(expense_sum)
        except ValueError:
            update.effective_chat.send_message('Потраченная сумма вводится в формате: 123(целое число). '
                                               'Попробуй еще раз')
            return

        expense_id = self.bot_.splitwise.add_expense(self.bot_.expenses[user_id])
        self.bot_.expenses[user_id].id = expense_id
        expense = self.bot_.splitwise.get_expense(expense_id)
        update.effective_chat.send_message(f'Создана трата: {str(expense)}.')
        self.bot_.states[update.effective_user.id] = DebtNameState(self.bot_)
        update.effective_chat.send_message('Приступим к записи долгов')
        users = self.bot_.splitwise.get_users_of_event(self.bot_.expenses[user_id].event_token)
        update.effective_chat.send_message('Назови имя должника', reply_markup=buttons.get_user_buttons(users))

    def callback_query_handler(self, update: Update):
        update.effective_chat.send_message('Потраченную сумму!')

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Потраченную сумму!')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Потраченную сумму!')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Потраченную сумму!')


class DebtNameState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Не то!')

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        if update.effective_message.text == 'все':
            del self.bot_.states[update.effective_user.id]
            del self.bot_.expenses[update.effective_user.id]
            del self.bot_.debts[update.effective_user.id]
            return
        update.effective_chat.send_message('Просто тыкни на  кнопку')

    def callback_query_handler(self, update: Update):
        query = update.callback_query
        user_debt = Debt(None, None, None)
        user_debt.lender_id = update.effective_user.id
        user_debt.debtor_id = query.data
        self.bot_.debts[update.effective_user.id] = user_debt
        self.bot_.states[update.effective_user.id] = DebtSumState(self.bot_)
        update.effective_chat.send_message('Сколько он тебе задолжал?')

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Просто тыкни на  кнопку')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('На кнопку жми')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('На кнопку жми!')


class DebtSumState:

    def __init__(self, bot_: TelegramBot):
        self.bot_ = bot_

    def join_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Введи сумму')

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        debt_sum = update.effective_message.text
        user_id = update.effective_user.id
        try:
            debt_sum = int(debt_sum)
        except ValueError:
            update.effective_chat.send_message('Долг вводится в формате: 123(целое число). '
                                               'Попробуй еще раз')
            return

        self.bot_.debts[user_id].sum = debt_sum
        self.bot_.debts[user_id].expense_id = self.bot_.expenses[user_id].id
        debt = self.bot_.debts[user_id]
        self.bot_.splitwise.add_debt(debt)
        update.effective_chat.send_message('Записал!')
        del self.bot_.debts[user_id]
        users = self.bot_.splitwise.get_users_of_event(self.bot_.expenses[user_id]['token'])
        self.bot_.states[update.effective_user.id] = DebtNameState(self.bot_)
        update.effective_chat.send_message('Назови имя следующего должника или напиши "все", чтобы закончить', reply_markup=buttons.get_user_buttons(users))

    def callback_query_handler(self, update: Update):
        update.effective_chat.send_message("Сколько он тебе задолжал?")

    def create_event_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Введи сумму')

    def add_expense_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Введи сумму')

    def show_debts_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Введи сумму')

