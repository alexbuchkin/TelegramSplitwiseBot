from app.splitwise import SplitwiseApp


if __name__ == '__main__':
    splitwise = SplitwiseApp()
    users = [
        (123, 'Ivan'),
        (456, 'Maria'),
        (789, 'San44ez'),
    ]

    for id_, name in users:
        splitwise.add_new_user(id_, name)

    for id_, _ in users:
        print(splitwise.get_user_info(id_))

    splitwise.conn.clean_all_tables()
