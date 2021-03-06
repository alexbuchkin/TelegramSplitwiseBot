from enum import auto, Enum, unique
from typing import NoReturn, Optional

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

from bot import buttons, menu_items
from app.splitwise import SplitwiseApp
from database.model_types import (
    Expense,
    Debt,
    User,
)


@unique
class States(Enum):
    CURRENT_EVENT_TOKEN = auto()
    EXPENSE = auto()
    DEBT = auto()
    EVENT_NAME_STATE = auto()
    EVENT_TOKEN_STATE = auto()
    ASKING_FOR_ACTION = auto()
    EVENT_ACTIONS = auto()
    EXPENSE_NAME = auto()
    EXPENSE_SUM = auto()
    DEBTOR_NAME = auto()
    DEBT_SUM = auto()


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
            update.effective_chat.send_message(f'Привет, {name}! Ты уже был(а) здесь!')
        else:
            self._splitwise.add_new_user(User(id_, name))
            update.effective_chat.send_message(f'Привет, {name}! Ты здесь впервые!')
        update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())

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
        update.effective_chat.send_message('Выберите пункт меню:')
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
        if data == menu_items.CREATE_EVENT:
            update.callback_query.edit_message_text('Введи название мероприятия или нажми кнопку \'Отмена\'')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_cancel_button())
            update.callback_query.answer()
            return States.EVENT_NAME_STATE
        elif data == menu_items.JOIN_EVENT:
            update.callback_query.edit_message_text('Введи токен мероприятия или нажми кнопку \'Отмена\'',
                                                    reply_markup=buttons.get_cancel_button())
            update.callback_query.answer()
            return States.EVENT_TOKEN_STATE
        elif data == menu_items.SELECT_EVENT:
            user_id = update.effective_user.id
            events = self._splitwise.get_user_events(user_id)
            update.callback_query.edit_message_text('Выбери мероприятие')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_event_buttons(events))
            update.callback_query.answer()
            return States.ASKING_FOR_ACTION

    def fallback_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Ошибка, но мы не знаем что произошло')

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.callback_query_handler), ],
            states={
                States.EVENT_NAME_STATE: [CreateEventConversation().get_conversation_handler()],
                States.ASKING_FOR_ACTION: [SelectEventConversation().get_conversation_handler()],
                States.EVENT_TOKEN_STATE: [JoinEventConversation().get_conversation_handler()],
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
        return ConversationHandler.END

    def callback_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        if update.callback_query.data == menu_items.CANCEL:
            update.callback_query.answer('Создание мероприятия отменено')
            update.callback_query.edit_message_text('Меню:')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_menu_keyboard())
            return ConversationHandler.END
        else:
            update.callback_query.answer('Не на ту кнопку жмешь')

    def fallbacks_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Мимо кассы. Нужно имя.')

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.text, self.event_name_handler),
                          CallbackQueryHandler(self.callback_handler), ],
            states={},
            fallbacks=[MessageHandler(Filters.all, self.fallbacks_handler)],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END,
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
            update.effective_chat.send_message('Мероприятия с таким токеном не существует. '
                                               'Введи корректный токен или нажми кнопку \'Отмена\'',
                                               reply_markup=buttons.get_cancel_button())
            return None
        if self._splitwise.user_participates_in_event(user_id, event_token):
            update.effective_chat.send_message('Не прокатит! Ты уже зарегистрирован в этом мероприятии')
            update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())
            return ConversationHandler.END
        self._splitwise.add_user_to_event(user_id, event_token)
        update.effective_chat.send_message('Ты успешно присоединился к мероприятию')
        update.effective_chat.send_message('Меню:', reply_markup=buttons.get_menu_keyboard())
        return ConversationHandler.END

    def callback_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        if update.callback_query.data == menu_items.CANCEL:
            update.callback_query.edit_message_text('Меню:')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_menu_keyboard())
            return ConversationHandler.END
        else:
            update.callback_query.answer('Не на ту кнопку жмешь',)

    def fallbacks_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Давай токен говори')

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.text, self.event_token_handler),
                          CallbackQueryHandler(self.callback_handler), ],
            states={},
            fallbacks=[MessageHandler(Filters.all, self.fallbacks_handler)],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END,
            }
        )
        return conv_handler


class SelectEventConversation:

    def __init__(self,):
        self._splitwise = SplitwiseApp()

    def asking_for_action(
        self,
        update: Update,
        context: CallbackContext,
    ):
        if update.callback_query.data == menu_items.CANCEL:
            context.user_data.pop(States.CURRENT_EVENT_TOKEN, None)
            update.callback_query.edit_message_text('Меню:')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_menu_keyboard())
            update.callback_query.answer()
            return ConversationHandler.END
        event_token = update.callback_query.data
        context.user_data[States.CURRENT_EVENT_TOKEN] = event_token
        event = self._splitwise.get_event_info(event_token)
        update.callback_query.edit_message_text(f'{event.name}\nВыберите пункт меню:')
        update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_event_commands_keyboard())
        update.callback_query.answer()
        return States.EVENT_ACTIONS

    def fallbacks_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Что-то пошло не так. Попробуй еще раз')

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.asking_for_action)],
            states={
                States.EVENT_ACTIONS: [ActionProcessHandlers().get_conversation_handler(), ]
            },
            fallbacks=[MessageHandler(Filters.all, self.fallbacks_handler), ],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END,
            }

        )
        return conv_handler


class ActionProcessHandlers:
    def __init__(self):
        self._splitwise = SplitwiseApp()

    def callback_query_handler(
        self,
        update: Update,
        context: CallbackContext,
    ) -> NoReturn:
        data = update.callback_query.data
        event_token = context.user_data[States.CURRENT_EVENT_TOKEN]
        event = self._splitwise.get_event_info(event_token)
        user_id = update.effective_user.id
        if data == menu_items.SHOW_DEBTS:
            lenders_info, debtors_info = self._splitwise.get_final_transactions(event_token)
            if user_id in debtors_info:
                update.callback_query.edit_message_text('Вы должны: \n' + str(debtors_info[user_id]) +
                                                        f'\n\n {event.name}\nВыберите пункт меню:')
            elif user_id in lenders_info:
                update.callback_query.edit_message_text('Вам должны: \n' + str(lenders_info[user_id]) +
                                                        f'\n\n {event.name}\nВыберите пункт меню:')
            else:
                update.callback_query.edit_message_text('Вы никому не должны и вам никто не должен!!!' +
                                                        f'\n\n {event.name}\nВыберите пункт меню:')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_event_commands_keyboard())
            update.callback_query.answer()
            return States.EVENT_ACTIONS
        elif data == menu_items.ADD_EXPENSE:
            event_token = context.user_data[States.CURRENT_EVENT_TOKEN]
            try:
                self._splitwise.get_event_info(event_token)
            except KeyError:
                update.effective_chat.send_message(
                    'Мероприятия с таким токеном не существует. Повторите создание траты:')
                return ConversationHandler.END
            expense = Expense()
            expense.event_token = event_token
            expense.lender_id = user_id
            context.user_data[States.EXPENSE] = expense
            update.callback_query.edit_message_text('Введи название траты или нажми \'Отмена\'',
                                                    reply_markup=buttons.get_cancel_button())
            return States.EXPENSE_NAME
        elif data == menu_items.CANCEL:
            del context.user_data[States.CURRENT_EVENT_TOKEN]
            update.callback_query.edit_message_text('Меню:')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_menu_keyboard())
            update.callback_query.answer()
            return ConversationHandler.END

    def fallbacks_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Что-то пошло не так. Попробуй еще раз раз')

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.callback_query_handler), ],
            states={
                States.EXPENSE_NAME: [AddExpenseHandlers().get_conversation_handler()],
            },
            fallbacks=[MessageHandler(Filters.all, self.fallbacks_handler)],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END,
                States.EVENT_ACTIONS: States.EVENT_ACTIONS,
            }

        )
        return conv_handler


class AddExpenseHandlers:

    def __init__(self,):
        self._splitwise = SplitwiseApp()

    @staticmethod
    def _get_sum_or_none(text) -> Optional[int]:
        try:
            sum_ = int(text)
        except ValueError:
            return None
        return sum_ if sum_ > 0 else None

    def expense_name(
        self,
        update: Update,
        context: CallbackContext,
    ) -> States:
        expense_name = update.effective_message.text
        context.user_data[States.EXPENSE].name = expense_name
        update.effective_chat.send_message('Введи потраченную сумму или нажми кнопку \'Отмена\'.',
                                           reply_markup=buttons.get_cancel_button())
        return States.EXPENSE_SUM

    def expense_sum(
        self,
        update: Update,
        context: CallbackContext,
    ) -> Optional[States]:
        # let's use integer division and forget about cents for some time
        expense_sum = self._get_sum_or_none(update.effective_message.text)
        if not expense_sum:
            update.effective_chat.send_message('Потраченная сумма вводится в формате: 123(целое число). '
                                               'Потраченная сумма должна быть больше нуля. '
                                               'Попробуй еще раз')
            return None

        context.user_data[States.EXPENSE].sum = expense_sum
        expense_id = self._splitwise.add_expense(context.user_data[States.EXPENSE])
        context.user_data[States.EXPENSE].id = expense_id
        expense = self._splitwise.get_expense(expense_id)
        update.effective_chat.send_message(f'Создана трата: {str(expense)}.')
        update.effective_chat.send_message('Приступим к записи долгов')
        users = self._splitwise.get_users_of_event(context.user_data[States.CURRENT_EVENT_TOKEN])
        update.effective_chat.send_message('Назови имя должника', reply_markup=buttons.get_user_buttons(users))
        return States.DEBTOR_NAME

    def debtor_name(
        self,
        update: Update,
        context: CallbackContext
    ):
        if update.callback_query.data == menu_items.CANCEL:
            return self.cancel_button_handler(update, context)

        user_debt = Debt()
        user_debt.lender_id = update.effective_user.id
        user_debt.debtor_id = int(update.callback_query.data)
        context.user_data[States.DEBT] = user_debt
        user = self._splitwise.get_user_info(int(update.callback_query.data))
        update.callback_query.edit_message_text(f'{user.name}\nСколько он тебе задолжал?')
        update.callback_query.answer()
        return States.DEBT_SUM

    def debt_sum(
        self,
        update: Update,
        context: CallbackContext,
    ) -> NoReturn:
        debt_sum = self._get_sum_or_none(update.effective_message.text)
        if not debt_sum:
            update.effective_chat.send_message('Долг вводится в формате: 123(целое число). '
                                               'Долг должен быть положительным. '
                                               'Попробуй еще раз')
            return None

        context.user_data[States.DEBT].sum = debt_sum
        context.user_data[States.DEBT].expense_id = context.user_data[States.EXPENSE].id
        debt = context.user_data[States.DEBT]
        self._splitwise.add_debt(debt)
        update.effective_chat.send_message('Записал!')
        users = self._splitwise.get_users_of_event(context.user_data[States.EXPENSE].event_token)
        update.effective_chat.send_message('Назови имя следующего должника или нажмите "Закончить"',
                                           reply_markup=buttons.get_user_buttons(users))
        return States.DEBTOR_NAME

    def cancel_button_handler(
        self,
        update: Update,
        context: CallbackContext,
    ):
        data = update.callback_query.data
        if data == menu_items.CANCEL:
            context.user_data.pop(States.EXPENSE, None)
            context.user_data.pop(States.DEBT, None)
            event_token = context.user_data[States.CURRENT_EVENT_TOKEN]
            event = self._splitwise.get_event_info(event_token)
            update.callback_query.edit_message_text(f'\n\n {event.name}\nВыберите пункт меню:')
            update.callback_query.edit_message_reply_markup(reply_markup=buttons.get_event_commands_keyboard())
            update.callback_query.answer('Закончили')
            return States.EVENT_ACTIONS
        return None


    def fallbacks_button_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Хватит жмакать на кнопки')

    def fallbacks_handler(
        self,
        update: Update,
        _: CallbackContext,
    ):
        update.effective_chat.send_message('Что-то пошло не так. Попробуй еще раз раз раз')

    def get_conversation_handler(self,) -> ConversationHandler:
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.text, self.expense_name),
                          CallbackQueryHandler(self.cancel_button_handler)],
            states={
                States.EXPENSE_SUM: [MessageHandler(Filters.text, self.expense_sum),
                                     CallbackQueryHandler(self.cancel_button_handler)],
                States.DEBTOR_NAME: [CallbackQueryHandler(self.debtor_name)],
                States.DEBT_SUM: [MessageHandler(Filters.text, self.debt_sum)],
            },
            fallbacks=[CallbackQueryHandler(self.fallbacks_button_handler),
                       MessageHandler(Filters.all, self.fallbacks_handler)],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END,
                States.EVENT_ACTIONS: States.EVENT_ACTIONS,
            }

        )
        return conv_handler
