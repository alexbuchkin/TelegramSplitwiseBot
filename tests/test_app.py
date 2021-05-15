import pytest
import sqlite3

from app.splitwise import SplitwiseApp
from database.new_types import (
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


def test_final_transactions(app):
    for user in USERS:
        app.add_new_user(user)

    event_token = app.create_event(user_id=USERS[0].id, event_name='Test event')
    expense_id = app.add_expense(Expense(
        name='first expense',
        sum=100 * len(USERS),
        lender_id=USERS[0].id,
        event_token=event_token,
    ))
    for user in USERS[1:]:
        app.add_user_to_event(user_id=user.id, event_token=event_token)
        app.add_debt(Debt(
            expense_id=expense_id,
            lender_id=USERS[0].id,
            debtor_id=user.id,
            sum=100,
        ))

    lenders_info, debtors_info = app.get_final_transactions(event_token)

    assert list(lenders_info.keys()) == [USERS[0].id]
    assert sorted(lenders_info[USERS[0].id]) == sorted([(user.name, 100) for user in USERS[1:]])

    assert sorted(list(debtors_info.keys())) == sorted([user.id for user in USERS[1:]])
    for _, debt_list in debtors_info.items():
        assert debt_list == [(USERS[0].name, 100)]


def test_no_transactions(app):
    for user in USERS:
        app.add_new_user(user)

    event_token = app.create_event(user_id=USERS[0].id, event_name='Test event')

    lenders_info, debtors_info = app.get_final_transactions(event_token)
    assert lenders_info == dict()
    assert debtors_info == dict()


def test_circular_transactions(app):
    for user in USERS:
        app.add_new_user(user)

    event_token = app.create_event(user_id=USERS[0].id, event_name='Test event')
    for user in USERS[1:]:
        app.add_user_to_event(user_id=user.id, event_token=event_token)

    for i in range(len(USERS)):
        expense_id = app.add_expense(Expense(
            name=f'expense #{i + 1}',
            sum=100,
            lender_id=USERS[i].id,
            event_token=event_token,
        ))
        app.add_debt(Debt(
            expense_id=expense_id,
            lender_id=USERS[i].id,
            debtor_id=USERS[(i + 1) % len(USERS)].id,
            sum=100,
        ))

    lenders_info, debtors_info = app.get_final_transactions(event_token)
    assert lenders_info == dict()
    assert debtors_info == dict()


def test_event_isolation(app):
    for user in USERS:
        app.add_new_user(user)

    for i in range(2):
        app.create_event(event_name=EVENTS[i].name, event_token=EVENTS[i].token, user_id=USERS[0].id)

    expense_id = app.add_expense(Expense(
        name='expense',
        sum=100 * len(USERS),
        lender_id=USERS[0].id,
        event_token=EVENTS[0].token,
    ))
    for user in USERS[1:]:
        app.add_debt(Debt(
            expense_id=expense_id,
            lender_id=USERS[0].id,
            debtor_id=user.id,
            sum=100,
        ))

    lenders_info, debtors_info = app.get_final_transactions(EVENTS[1].token)
    assert lenders_info == dict()
    assert debtors_info == dict()


def test_several_executes_rollback(app):
    """
    Test that if first sqlite3.Cursor.execute method
    with INSERT statement runs successfully and second method fails
    then no data will be stored in database.
    Testing Connector.create_event method
    """
    with pytest.raises(sqlite3.IntegrityError, match='FOREIGN KEY constraint failed'):
        app.create_event(event_name=EVENTS[0].name, user_id=USERS[0].id)  # no such user in database

    assert app.get_all_events() == []
