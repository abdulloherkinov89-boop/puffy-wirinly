import os
from pathlib import Path

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    func,
    select,
    update,
) 
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool


DATABASE_PATH = Path(__file__).resolve().with_name("puffy_test.db")
metadata = MetaData()
users = Table(
    "users",
    metadata,
    Column("tg_id", BigInteger, primary_key=True),
    Column("full_name", String, nullable=False),
    Column("first_name", String, nullable=False),
    Column("username", String),
    Column("phone_number", String),
    Column("created_at", Text, nullable=False, server_default=func.current_timestamp()),
    Column("updated_at", Text, nullable=False, server_default=func.current_timestamp()),
)
categories = Table(
    "categories",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("created_at", Text, nullable=False, server_default=func.current_timestamp()),
    UniqueConstraint("name", name="uq_categories_name"),
)
Index("uq_categories_name_lower", func.lower(categories.c.name), unique=True)
products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("price", Integer, nullable=False),
    Column("image_url", Text, nullable=False),
    Column("category_id", ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
    Column("about", Text, nullable=False),
    Column("created_at", Text, nullable=False, server_default=func.current_timestamp()),
)

_engine: Engine | None = None


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{DATABASE_PATH.as_posix()}"
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def _get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database hali ishga tushirilmagan")
    return _engine


def initialize_database() -> None:
    """Connect to DATABASE_URL and create application tables at startup."""
    global _engine
    if _engine is not None:
        return

    database_url = _database_url()
    engine_options = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if database_url.endswith(":memory:"):
            engine_options["poolclass"] = StaticPool

    engine = create_engine(database_url, **engine_options)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    try:
        metadata.create_all(engine)
    except Exception:
        engine.dispose()
        raise
    _engine = engine


def save_user(
    *,
    tg_id: int,
    full_name: str,
    first_name: str,
    username: str | None,
    phone_number: str | None = None,
) -> None:
    """Insert a Telegram user or refresh their details without losing a saved phone."""
    engine = _get_engine()
    with engine.begin() as connection:
        existing_user = connection.execute(
            select(users.c.phone_number).where(users.c.tg_id == tg_id)
        ).first()
        values = {
            "full_name": full_name,
            "first_name": first_name,
            "username": username,
            "phone_number": phone_number or (existing_user.phone_number if existing_user else None),
            "updated_at": func.current_timestamp(),
        }
        if existing_user:
            connection.execute(update(users).where(users.c.tg_id == tg_id).values(**values))
        else:
            connection.execute(users.insert().values(tg_id=tg_id, **values))


def get_user(tg_id: int) -> dict[str, int | str | None] | None:
    """Return the saved profile for a Telegram user, if it exists."""
    with _get_engine().connect() as connection:
        row = connection.execute(
            select(
                users.c.tg_id,
                users.c.full_name,
                users.c.first_name,
                users.c.username,
                users.c.phone_number,
            ).where(users.c.tg_id == tg_id)
        ).mappings().first()
    return dict(row) if row else None


def list_categories() -> list[dict[str, int | str]]:
    """Return categories in the order they were added."""
    with _get_engine().connect() as connection:
        rows = connection.execute(
            select(categories.c.id, categories.c.name).order_by(categories.c.id)
        ).mappings().all()
    return [dict(row) for row in rows]


def add_category(name: str) -> int:
    """Create a category and return its database ID."""
    with _get_engine().begin() as connection:
        result = connection.execute(categories.insert().values(name=name.strip()))
        return int(result.inserted_primary_key[0])


def add_product(
    *, name: str, price: int, image_url: str, category_id: int, about: str
) -> int:
    """Create a product linked to an existing category and return its ID."""
    with _get_engine().begin() as connection:
        result = connection.execute(
            products.insert().values(
                name=name.strip(),
                price=price,
                image_url=image_url,
                category_id=category_id,
                about=about.strip(),
            )
        )
        return int(result.inserted_primary_key[0])


def list_products() -> list[dict[str, int | str]]:
    """Return products with their category names for the web catalog."""
    statement = (
        select(
            products.c.id,
            products.c.name,
            products.c.price,
            products.c.image_url,
            products.c.category_id,
            products.c.about,
            categories.c.name.label("category_name"),
        )
        .join(categories, categories.c.id == products.c.category_id)
        .order_by(categories.c.id, products.c.id)
    )
    with _get_engine().connect() as connection:
        rows = connection.execute(statement).mappings().all()
    return [dict(row) for row in rows]