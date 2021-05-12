import pytest

from app.splitwise import SplitwiseApp
from database.types import (
    User,
    Event,
    Expense,
    Debt,
)


@pytest.fixture(scope='function')
def db_name(tmpdir):
    return str(tmpdir / 'db.sqlite')


def test_storing_users(db_name):
    app = SplitwiseApp(db_name)

    usernames = ['Car', 'Major', 'Khokhma']
    for id_, name in enumerate(usernames, start=1):
        app.add_new_user(User(id=id_, name=name))

    for id_ in range(1, len(usernames) + 1):
        assert app.user_exists(id_)
    assert not app.user_exists(0)
    for id_ in range(len(usernames) + 1, len(usernames) + 10):
        assert not app.user_exists(id_)

    for id_, name in enumerate(usernames, start=1):
        user = app.get_user_info(id_)
        assert user.id == id_
        assert user.name == name

    stored_users = sorted(app.get_all_users(), key=lambda user: user.id)
    assert stored_users == [User(id=id_, name=name) for id_, name in enumerate(usernames, start=1)]
