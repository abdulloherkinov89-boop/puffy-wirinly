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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL CHECK (price > 0),
                    image_url TEXT NOT NULL,
                    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                    about TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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


def list_categories() -> list[dict[str, int | str]]:
    """Return categories in the order they were added."""
    initialize_database()
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def add_category(name: str) -> int:
    """Create a category and return its database ID."""
    initialize_database()
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO categories (name) VALUES (?)", (name.strip(),)
            )
            return int(cursor.lastrowid)


def add_product(
    *, name: str, price: int, image_url: str, category_id: int, about: str
) -> int:
    """Create a product linked to an existing category and return its ID."""
    initialize_database()
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO products (name, price, image_url, category_id, about)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name.strip(), price, image_url, category_id, about.strip()),
            )
            return int(cursor.lastrowid)


def list_products() -> list[dict[str, int | str]]:
    """Return products with their category names for the web catalog."""
    initialize_database()
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT p.id, p.name, p.price, p.image_url, p.category_id,
                   p.about, c.name AS category_name
            FROM products AS p
            JOIN categories AS c ON c.id = p.category_id
            ORDER BY c.id, p.id
            """
        ).fetchall()
    return [dict(row) for row in rows]