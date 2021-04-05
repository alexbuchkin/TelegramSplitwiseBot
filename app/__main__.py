from app.splitwise import SplitwiseApp


if __name__ == '__main__':
    splitwise = SplitwiseApp()
    users = [
        (123, 'Ivan'),
        (456, 'Maria'),
        (789, 'San44ez'),
    ]

    for id, name in users:
        splitwise.add_new_user(id, name)

    for id, _ in users:
        print(splitwise.get_user_info(id))

    splitwise.conn.clean_all_tables()
