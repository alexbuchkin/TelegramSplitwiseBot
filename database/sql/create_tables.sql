PRAGMA foreign_keys=on;

CREATE TABLE IF NOT EXISTS users (
    id   INTEGER PRIMARY KEY,
    name VARCHAR
);

CREATE TABLE IF NOT EXISTS events (
    token VARCHAR PRIMARY KEY,
    name  VARCHAR NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user2event (
    user_id     INTEGER NOT NULL,
    event_token VARCHAR NOT NULL,

    FOREIGN KEY (user_id)     REFERENCES users(id),
    FOREIGN KEY (event_token) REFERENCES events(token)
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR NOT NULL,
    sum         INTEGER NOT NULL,
    lender_id   INTEGER NOT NULL,
    event_token VARCHAR NOT NULL,
    datetime    DATETIME NOT NULL,

    FOREIGN KEY (lender_id)   REFERENCES users(id),
    FOREIGN KEY (event_token) REFERENCES events(token)
);

CREATE TABLE IF NOT EXISTS debts (
    expense_id INTEGER NOT NULL,
    lender_id  INTEGER NOT NULL,
    debtor_id  INTEGER NOT NULL,
    sum        INTEGER NOT NULL,

    FOREIGN KEY (expense_id) REFERENCES expenses(id),
    FOREIGN KEY (lender_id)  REFERENCES users(id),
    FOREIGN KEY (debtor_id)  REFERENCES users(id)
);
