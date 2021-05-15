from typing import NoReturn

from telegram import ParseMode
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
)

import buttons
import constants
from app.splitwise import SplitwiseApp
from database.new_types import (
    Expense,
    Debt,
)

from database.new_types import (
    User,
)

_CURRENT_EVENT_TOKEN = 'CURRENT_EVENT_TOKEN'
_EXPENSE = 'EXPENSE'
_DEBT = 'DEBT'

_CREATE_EVENT = 1
_JOIN_EVENT = 2
_SELECT_EVENT = 3
_EVENT_NAME_STATE = 4
_EVENT_TOKEN_STATE = 5
_ASKING_FOR_ACTION = 6
_EVENT_ACTIONS = 7
_EXPENSE_NAME = 8
_EXPENSE_SUM = 9
_DEBTOR_NAME = 10
_DEBT_SUM = 11
_END = ConversationHandler.END


class BeginningHandlers:
    def __init__(self):
        self._splitwise = SplitwiseApp()

    def start_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        id_ = update.effective_user.id
        name = update.effective_user.username

        if self._splitwise.user_exists(id_):
            name = self._splitwise.get_user_info(id_).name
            update.effective_chat.send_message(f'Привет, {name}! Ты уже был(а) здесь!',
                                               reply_markup=buttons.get_menu_keyboard())
        else:
            self._splitwise.add_new_user(User(id_, name))
            update.effective_chat.send_message(f'Привет, {name}! Ты здесь впервые!',
                                               reply_markup=buttons.get_menu_keyboard())

    def users_of_event_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        token = context.args[0]
        users = self._splitwise.get_users_of_event(token)
        update.effective_chat.send_message(str(users))

    def text_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Введи команду или выберете пункт меню:')
        update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())

    def get_menu(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())


class MenuButtonsConversationHandler:
    def __init__(self):
        self._splitwise = SplitwiseApp()

    def callback_query_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        data = update.callback_query.data
        update.callback_query.answer()
        if data == constants.CREATE_EVENT:
            update.callback_query.edit_message_text('Введи название мероприятия или нажмите кнопку \'Отмена\'')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_cancel_button())
            update.callback_query.answer()
            return _EVENT_NAME_STATE
        elif data == constants.JOIN_EVENT:
            update.callback_query.edit_message_text('Введи токен мероприятия или нажмите кнопку \'Отмена\'',
                                                    reply_markup=buttons.get_cancel_button())
            update.callback_query.answer()
            return _EVENT_TOKEN_STATE
        elif data == constants.SELECT_EVENT:
            user_id = update.effective_user.id
            events = self._splitwise.get_user_events(user_id)
            update.callback_query.edit_message_text('Выбери мероприятие')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_event_buttons(events))
            update.callback_query.answer()
            return _ASKING_FOR_ACTION

    def create_event(
        self,
        update: Update,
        _: CallbackContext,
    ) -> int:
        update.effective_chat.send_message('Введи название мероприятия или нажмите кнопку \'Отмена\'',
                                           reply_markup=buttons.get_cancel_button())
        return _EVENT_NAME_STATE

    def join_event(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Введи токен мероприятия или нажмите кнопку \'Отмена\'',
                                           reply_markup=buttons.get_cancel_button())
        return _EVENT_TOKEN_STATE

    def select_event(
        self,
        update: Update,
        _: CallbackContext,
    ):
        user_id = update.effective_user.id
        events = self._splitwise.get_user_events(user_id)
        update.effective_chat.send_message('Выбери мероприятие', reply_markup=buttons.get_event_buttons(events))
        return _ASKING_FOR_ACTION

    def fallback_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message("Ошибка, но мы не знаем что произошло")

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.callback_query_handler),
                          CommandHandler('create_event', self.create_event),
                          CommandHandler('join_event', self.join_event),
                          CommandHandler('select_event', self.select_event)],
            states={
                _EVENT_NAME_STATE: [CreateEventConversation().get_conversation_handler()],
                _ASKING_FOR_ACTION: [SelectEventConversation().get_conversation_handler()],
                _EVENT_TOKEN_STATE: [JoinEventConversation().get_conversation_handler()],
            },
            fallbacks=[MessageHandler(Filters.all, self.fallback_handler)],
        )
        return conv_handler


class CreateEventConversation:

    def __init__(self,):
        self._splitwise = SplitwiseApp()

    def event_name_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        event_name = update.effective_message.text
        event_token = self._splitwise.create_event(
            user_id=update.effective_user.id,
            event_name=event_name,
        )
        update.effective_chat.send_message(
            f'Мероприятие "{event_name}" создано. Токен: `{event_token}`',
            parse_mode=ParseMode.MARKDOWN
        )
        update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())
        return _END

    def callback_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        if update.callback_query.data == constants.CANCEL:
            update.callback_query.answer('Создание мероприятия отменено')
            update.callback_query.message.delete()
            return _END
        else:
            update.callback_query.answer('Не на ту кнопку жмешь')
            return None

    def fallbacks_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужно имя.')
        return None

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.text, self.event_name_handler),
                          CallbackQueryHandler(self.callback_handler), ],
            states={},
            fallbacks=[MessageHandler(Filters.all, self.fallbacks_handler)],
            map_to_parent={
                _END: _END,
            }
        )
        return conv_handler


class JoinEventConversation:

    def __init__(self,):
        self._splitwise = SplitwiseApp()

    def event_token_handler(
        self,
        update: Update,
        _: CallbackContext,
    ) -> NoReturn:
        event_token = update.effective_message.text
        user_id = update.effective_user.id
        try:
            self._splitwise.get_event_info(event_token)
        except KeyError:
            update.effective_chat.send_message('Мероприятия с таким токеном не существует. Введите корректный токен')
            update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())
            return None
        if self._splitwise.user_participates_in_event(user_id, event_token):
            update.effective_chat.send_message('Не прокатит! Ты уже зарегистрирован в этом мероприятии')
            update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())
            return _END
        self._splitwise.add_user_to_event(user_id, event_token)
        update.effective_chat.send_message('Ты успешно присоединился к мероприятию')
        update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())
        return _END

    def callback_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        if update.callback_query.data == constants.CANCEL:
            update.callback_query.edit_message_text('Меню:')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_menu_keyboard())
            return _END
        else:
            update.callback_query.answer('Не на ту кнопку жмешь',)
            return None

    def fallbacks_handler(
            self,
            update: Update,
            _: CallbackContext,
    ):
        update.effective_chat.send_message('Давай токен говори')
        return None

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.text, self.event_token_handler),
                          CallbackQueryHandler(self.callback_handler), ],
            states={},
            fallbacks=[MessageHandler(Filters.all, self.fallbacks_handler)],
            map_to_parent={
                _END: _END,
            }
        )
        return conv_handler


class SelectEventConversation:

    def __init__(self,):
        self._splitwise  = SplitwiseApp()

    def asking_for_action(
            self,
            update: Update,
            context: CallbackContext,):
        if update.callback_query.data == constants.CANCEL:
            update.callback_query.edit_message_text('Меню:')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_menu_keyboard())
            update.callback_query.answer()
            return _END
        event_token = update.callback_query.data
        context.user_data[_CURRENT_EVENT_TOKEN] = event_token
        update.effective_chat.send_message('Введите команду или выберете пункт меню:')
        update.callback_query.answer()
        return _EVENT_ACTIONS

    def fallbacks_handler(
            self,
            update: Update,
            _: CallbackContext,
    ):
        update.effective_chat.send_message('Что-то пошло не так. Попробуй еще раз')
        return None

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.asking_for_action)],
            states={
                _EVENT_ACTIONS: [ShowDebtsHandlers().get_conversation_handler(),
                                 AddExpenseHandlers().get_conversation_handler()]
            },
            fallbacks=[MessageHandler(Filters.all, self.fallbacks_handler), ],
            map_to_parent={
                _END: _END,
            }
        )
        return conv_handler


class ShowDebtsHandlers:

    def __init__(self,):
        self._splitwise = SplitwiseApp()

    def show_debts(
        self,
        update: Update,
        context: CallbackContext,
    ) -> NoReturn:
        token = context.user_data[_CURRENT_EVENT_TOKEN]
        user_id = update.effective_user.id
        lenders_info, debtors_info = self._splitwise.get_final_transactions(token)
        if user_id in debtors_info:
            update.effective_chat.send_message('Вы должны: \n' + str(debtors_info[user_id]))
        elif user_id in lenders_info:
            update.effective_chat.send_message('Вам должны: \n' + str(lenders_info[user_id]))
        else:
            update.effective_chat.send_message('Вы никому не должны и вам никто не должен')

        return _END

    def fallbacks_handler(
            self,
            update: Update,
            _: CallbackContext,
    ):
        update.effective_chat.send_message('Просто жмакни на кнопку')
        return None

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('show_debts', self.show_debts)],
            states={},
            fallbacks=[MessageHandler(Filters.all, self.fallbacks_handler)],
            map_to_parent={
                _END: _END,
            },
        )
        return conv_handler


class AddExpenseHandlers:

    def __init__(self,):
        self._splitwise = SplitwiseApp()

    def add_expense(
        self,
        update: Update,
        context: CallbackContext,
    ) -> int:
        event_token = context.user_data[_CURRENT_EVENT_TOKEN]
        user_id = update.effective_user.id
        try:
            self._splitwise.get_event_info(event_token)
        except KeyError:
            update.effective_chat.send_message('Мероприятия с таким токеном не существует. Повторите создание траты.')
            return _END
        expense = Expense(None, None, None, None, None, None)
        expense.event_token = event_token
        expense.lender_id = user_id
        context.user_data[_EXPENSE] = expense
        update.effective_chat.send_message('Введи название траты.')
        return _EXPENSE_NAME

    def expense_name(
        self,
        update: Update,
        context: CallbackContext,
    ) -> int:
        expense_name = update.effective_message.text
        context.user_data[_EXPENSE].name = expense_name
        update.effective_chat.send_message('Введи потраченную сумму.')
        return _EXPENSE_SUM

    def expense_sum(
        self,
        update: Update,
        context: CallbackContext,
    ) -> int:
        # let's use integer division and forget about cents for some time
        expense_sum = update.effective_message.text
        try:
            expense_sum = int(expense_sum)
        except ValueError:
            update.effective_chat.send_message('Потраченная сумма вводится в формате: 123(целое число). '
                                               'Попробуй еще раз')
            return None

        context.user_data[_EXPENSE].sum = expense_sum
        expense_id = self._splitwise.add_expense(context.user_data[_EXPENSE])
        context.user_data[_EXPENSE].id = expense_id
        expense = self._splitwise.get_expense(expense_id)
        update.effective_chat.send_message(f'Создана трата: {str(expense)}.')
        update.effective_chat.send_message('Приступим к записи долгов')
        users = self._splitwise.get_users_of_event(context.user_data[_CURRENT_EVENT_TOKEN])
        update.effective_chat.send_message('Назови имя должника', reply_markup=buttons.get_user_buttons(users))
        return _DEBTOR_NAME

    def debtor_name(
            self,
            update: Update,
            context: CallbackContext
    ):
        if update.callback_query.data == 'END':
            del context.user_data[_EXPENSE]
            del context.user_data[_DEBT]
            return _END

        user_debt = Debt(None, None, None, None)
        user_debt.lender_id = update.effective_user.id
        user_debt.debtor_id = update.callback_query.data
        context.user_data[_DEBT] = user_debt
        update.effective_chat.send_message('Сколько он тебе задолжал?')
        update.callback_query.answer()
        return _DEBT_SUM

    def debt_sum(
        self,
        update: Update,
        context: CallbackContext,
    ) -> NoReturn:
        debt_sum = update.effective_message.text
        try:
            debt_sum = int(debt_sum)
        except ValueError:
            update.effective_chat.send_message('Долг вводится в формате: 123(целое число). '
                                               'Попробуй еще раз')
            return None

        context.user_data[_DEBT].sum = debt_sum
        context.user_data[_DEBT].expense_id = context.user_data[_EXPENSE].id
        debt = context.user_data[_DEBT]
        self._splitwise.add_debt(debt)
        update.effective_chat.send_message('Записал!')
        users = self._splitwise.get_users_of_event(context.user_data[_EXPENSE].event_token)
        update.effective_chat.send_message('Назови имя следующего должника или нажмите "Закончить"',
                                           reply_markup=buttons.get_user_buttons(users))
        return _DEBTOR_NAME


    def fallbacks_button_handler(
            self,
            update: Update,
            _: CallbackContext,
    ):
        update.effective_chat.send_message('Хватит жмакать на кнопки')
        return None

    def fallbacks_handler(
            self,
            update: Update,
            _: CallbackContext,
    ):
        update.effective_chat.send_message('Что-то пошло не так. Попробуй еще раз')
        return None

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("add_expense", self.add_expense)],
            states={
                _EXPENSE_NAME: [MessageHandler(Filters.text, self.expense_name)],
                _EXPENSE_SUM: [MessageHandler(Filters.text, self.expense_sum)],
                _DEBTOR_NAME: [CallbackQueryHandler(self.debtor_name)],
                _DEBT_SUM: [MessageHandler(Filters.text, self.debt_sum)],
            },
            fallbacks=[CallbackQueryHandler(self.fallbacks_button_handler),
                       MessageHandler(Filters.all, self.fallbacks_handler)],
            map_to_parent={
                _END: _END,
            },
        )
        return conv_handler
