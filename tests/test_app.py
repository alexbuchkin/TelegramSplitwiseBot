import pytest
import sqlite3

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


@pytest.fixture(scope='function')
def app(db_name):
    return SplitwiseApp(db_name)


def test_storing_users(app):
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


def test_storing_events(app):
    for user in USERS:
        app.add_new_user(user)
    for user, event in zip(USERS, EVENTS):
        app.create_event(user_id=user.id, event_name=event.name, event_token=event.token)

    for event in EVENTS:
        assert app.get_event_info(event.token) == event

    NONEXISTENT_TOKEN = 'nonexistent_token'
    with pytest.raises(KeyError, match=f'Event with token {NONEXISTENT_TOKEN} does not exist'):
        app.get_event_info(NONEXISTENT_TOKEN)

    # trying to create event that already exists
    with pytest.raises(sqlite3.IntegrityError, match='UNIQUE constraint failed.*'):
        app.create_event(user_id=USERS[0].id, event_name=EVENTS[0].name, event_token=EVENTS[0].token)

    stored_events = sorted(app.get_all_events(), key=lambda event: event.token)
    assert stored_events == EVENTS


def test_adding_users_to_events(app):
    for user in USERS:
        app.add_new_user(user)

    app.create_event(user_id=USERS[0].id, event_name=EVENTS[0].name, event_token=EVENTS[0].token)
    assert app.user_participates_in_event(user_id=USERS[0].id, event_token=EVENTS[0].token)
    for user in USERS[1:]:
        assert not app.user_participates_in_event(user_id=user.id, event_token=EVENTS[0].token)
        app.add_user_to_event(user_id=user.id, event_token=EVENTS[0].token)
        assert app.user_participates_in_event(user_id=user.id, event_token=EVENTS[0].token)

    for user, event in zip(USERS[1:], EVENTS[1:]):
        app.create_event(user_id=user.id, event_name=event.name, event_token=event.token)
        for another_user in USERS:
            if another_user.id != user.id:
                app.add_user_to_event(user_id=another_user.id, event_token=event.token)

    for user in USERS:
        for event in EVENTS:
            assert app.user_participates_in_event(user_id=user.id, event_token=event.token)

    expected_user2event_data = [(user.id, event.token) for user in USERS for event in EVENTS]
    assert sorted(expected_user2event_data) == sorted(app.get_all_user2event())
