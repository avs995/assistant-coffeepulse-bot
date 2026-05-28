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

CREATE_LEAD_STATUS_HISTORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS lead_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    lead_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,

    created_at TEXT NOT NULL,

    FOREIGN KEY (lead_id) REFERENCES leads(id)
);
"""

CREATE_LEAD_NOTES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS lead_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    lead_id INTEGER NOT NULL,
    note TEXT NOT NULL,

    created_at TEXT NOT NULL,

    FOREIGN KEY (lead_id) REFERENCES leads(id)
);
"""


def init_db(database_path: str) -> sqlite3.Connection:
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute(CREATE_LEADS_TABLE_SQL)
    connection.execute(CREATE_LEAD_STATUS_HISTORY_TABLE_SQL)
    connection.execute(CREATE_LEAD_NOTES_TABLE_SQL)
    connection.commit()
    return connection
