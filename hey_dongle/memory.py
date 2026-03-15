import sqlite3
import os
from datetime import datetime

_conn: sqlite3.Connection | None = None

def init_db(db_path: str) -> None:
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = _get_conn(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            session   TEXT NOT NULL,
            role      TEXT NOT NULL,
            content   TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()

def _get_conn(db_path: str) -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(db_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn

def save_message(db_path: str, session: str, role: str, content: str) -> None:
    conn = _get_conn(db_path)
    conn.execute(
        "INSERT INTO messages (session, role, content, timestamp) "
        "VALUES (?, ?, ?, ?)",
        (session, role, content, 
         datetime.now().isoformat(timespec='seconds'))
    )
    conn.commit()

def load_session(db_path: str, session: str) -> list[dict]:
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT role, content, timestamp FROM messages "
        "WHERE session = ? ORDER BY id ASC",
        (session,)
    ).fetchall()
    return [{"role": r["role"], "content": r["content"], 
             "timestamp": r["timestamp"]} for r in rows]

def get_last_session(db_path: str) -> str | None:
    conn = _get_conn(db_path)
    row = conn.execute(
        "SELECT session FROM messages "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return row["session"] if row else None

def clear_session(db_path: str, session: str) -> int:
    conn = _get_conn(db_path)
    cursor = conn.execute(
        "DELETE FROM messages WHERE session = ?", 
        (session,)
    )
    conn.commit()
    return cursor.rowcount

def new_session_id() -> str:
    return datetime.now().strftime("session_%Y%m%d_%H%M%S")
