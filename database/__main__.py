from database.connector import Connector


if __name__ == '__main__':
    connector = Connector(db_name='testdb.sqlite')
    # connector.drop_all_tables()
    # connector.clean_all_tables()
    # event_id1 = connector.save_event_info("sochi")
    # event_id2 = connector.save_event_info("ochi")
    # event_id3 = connector.save_event_info("sochi")
    # user_id1 = connector.save_user_info("boris", event_id1)
    # user_id2 = connector.save_user_info("boris", event_id2)
    # user_id3 = connector.save_user_info("roman", event_id3)
    # expense_id1 = connector.save_expense_info("buy", user_id1, 12)
    # expense_id2 = connector.save_expense_info("buy1", user_id2, 32)
    # expense_id3 = connector.save_expense_info("buy2", user_id3, 123)
    # debtor_id1 = connector.save_debtor_info(expense_id1, user_id1, 12)
    # debtor_id3 = connector.save_debtor_info(expense_id2, user_id2, 1212)
    # debtor_id3 = connector.save_debtor_info(expense_id3, user_id3, 123)
    # connector.save_payments_info(user_id1, user_id2, 123)
    # connector.save_payments_info(user_id3, user_id2, 123)
    # events = connector.get_all_events()
    # users = connector.get_all_users()
    # expenses = connector.get_all_expenses()
    # debtors = connector.get_all_debtors()
    # payments = connector.get_all_payments()
    # print(events)
    # print(users)
    # print(expenses)
    # print(debtors)
    # print(payments)
    pass
