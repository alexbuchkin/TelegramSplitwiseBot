from app.splitwise import SplitwiseApp
from database.model_types import User


if __name__ == '__main__':
    splitwise = SplitwiseApp(db_name='testdb.sqlite')
    users = [
        (123, 'Ivan'),
        (456, 'Maria'),
        (789, 'San44ez'),
    ]

    for id_, name in users:
        splitwise.add_new_user(User(id=id_, name=name))

    for id_, _ in users:
        print(splitwise.get_user_info(id_))
