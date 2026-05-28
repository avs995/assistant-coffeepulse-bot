from pathlib import Path
import sqlite3


CREATE_LEADS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    company TEXT NOT NULL,
    city TEXT,
    niche TEXT,
    source TEXT,

    contacts TEXT,
    website TEXT,
    telegram TEXT,
    vk TEXT,

    fit_reason TEXT,
    score TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'new',

    notes TEXT,

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def init_db(database_path: str) -> sqlite3.Connection:
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute(CREATE_LEADS_TABLE_SQL)
    connection.commit()
    return connection
