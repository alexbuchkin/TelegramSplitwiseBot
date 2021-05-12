import pytest

from app.splitwise import SplitwiseApp
from database.types import (
    User,
    Event,
    Expense,
    Debt,
)

USERS = [
    User(id=1, name='Car'),
    User(id=2, name='Major'),
    User(id=3, name='Khokhma'),
]

EVENTS = [
    Event(token='token1', name='Pilsener'),
    Event(token='token2', name='Smoking'),
    Event(token='token3', name='Yachts'),
]


@pytest.fixture(scope='function')
def db_name(tmpdir):
    return str(tmpdir / 'db.sqlite')


def test_storing_users(db_name):
    app = SplitwiseApp(db_name)
    for user in USERS:
        app.add_new_user(user)

    for user in USERS:
        assert app.user_exists(user.id)
    for id_ in range(max((user.id for user in USERS)) + 1, max((user.id for user in USERS)) + 20):
        assert not app.user_exists(id_)

    for user in USERS:
        user_from_db = app.get_user_info(user.id)
        assert user_from_db == user

    stored_users = sorted(app.get_all_users(), key=lambda user: user.id)
    assert stored_users == USERS


def test_storing_events(db_name):
    app = SplitwiseApp(db_name)
    for user in USERS:
        app.add_new_user(user)
    for user, event in zip(USERS, EVENTS):
        app.create_event(user_id=user.id, event_name=event.name, event_token=event.token)

    for event in EVENTS:
        assert app.get_event_info(event.token) == event

    with pytest.raises(KeyError):
        app.get_event_info('no_such_token')

    stored_events = sorted(app.get_all_events(), key=lambda event: event.token)
    assert stored_events == EVENTS
