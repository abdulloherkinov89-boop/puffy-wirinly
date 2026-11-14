import sqlite3
from contextlib import closing
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().with_name("puffy_test.db")


def initialize_database() -> None:
    """Create the local puffy_test database and users table if needed."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    tg_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    username TEXT,
                    phone_number TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )


def save_user(
    *,
    tg_id: int,
    full_name: str,
    first_name: str,
    username: str | None,
    phone_number: str | None = None,
) -> None:
    """Insert a Telegram user or refresh their details without losing a saved phone."""
    initialize_database()
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO users (tg_id, full_name, first_name, username, phone_number)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(tg_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    first_name = excluded.first_name,
                    username = excluded.username,
                    phone_number = COALESCE(excluded.phone_number, users.phone_number),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (tg_id, full_name, first_name, username, phone_number),
            )