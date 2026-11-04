import os
from collections.abc import Generator
from pathlib import Path
from sqlite3 import Connection as SQLiteConnection
from sqlite3 import sqlite_version_info
from tempfile import gettempdir

from fastapi import Request
from sqlalchemy import Connection, Engine, create_engine, event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


LOCAL_DIRECTORY = Path(__file__).resolve().parents[2] / ".local"


def database_url() -> URL:
    mode = os.environ.get("DATABASE_MODE", "postgres")
    if mode not in {"sqlite", "postgres", "supabase"}:
        raise RuntimeError("Unsupported database mode")
    if mode == "sqlite":
        try:
            url = make_url(os.environ["DATABASE_URL"])
            if (
                os.environ.get("APP_ENV") not in {"local", "test"}
                or os.environ.get("VERCEL")
                or url.drivername != "sqlite"
                or url.host
                or url.username
                or url.password
                or url.query
                or not url.database
                or ":memory:" in url.database
                or url.database.startswith(("//", "\\\\"))
            ):
                raise ValueError
            path = Path(url.database)
            if not path.is_absolute():
                path = LOCAL_DIRECTORY.parent / path
            path = path.resolve()
            if (
                LOCAL_DIRECTORY.resolve() != LOCAL_DIRECTORY
                or not path.is_relative_to(LOCAL_DIRECTORY)
                or path.suffix not in {".db", ".sqlite", ".sqlite3"}
                or str(LOCAL_DIRECTORY).startswith(("//", "\\\\"))
                or LOCAL_DIRECTORY.is_relative_to(Path(gettempdir()).resolve())
            ):
                raise ValueError
            return url.set(database=str(path))
        except (KeyError, ValueError, OSError, SQLAlchemyError):
            raise RuntimeError("Valid local SQLite configuration is required") from None
    try:
        if raw := os.environ.get("DATABASE_URL"):
            url = make_url(raw)
        else:
            url = URL.create(
                "postgresql+psycopg",
                username=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
                host=os.environ["POSTGRES_HOST"],
                port=5432,
                database=os.environ["POSTGRES_DB"],
            )
            if not url.password:
                raise ValueError
        if (
            url.drivername not in {"postgresql", "postgresql+psycopg"}
            or not url.host
            or not url.username
            or not url.database
        ):
            raise ValueError
        if mode == "supabase" and url.query.get("sslmode") != "verify-full":
            raise ValueError
        return url.set(drivername="postgresql+psycopg")
    except (KeyError, ValueError, SQLAlchemyError):
        raise RuntimeError(
            "Valid PostgreSQL database configuration is required"
        ) from None


def create_database_engine() -> Engine:
    url = database_url()
    if url.drivername == "sqlite":
        if not (
            sqlite_version_info >= (3, 51, 3)
            or (3, 50, 7) <= sqlite_version_info < (3, 51, 0)
            or (3, 44, 6) <= sqlite_version_info < (3, 45, 0)
        ):
            raise RuntimeError(
                "SQLite runtime requires the WAL-reset fix; upgrade Python"
            )
        Path(str(url.database)).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            url, connect_args={"timeout": 10}, echo=False, hide_parameters=True
        )

        @event.listens_for(engine, "connect")
        def configure_sqlite(connection: SQLiteConnection, _: object) -> None:
            connection.isolation_level = None
            cursor = connection.cursor()
            try:
                for pragma, value in (
                    ("foreign_keys", 1),
                    ("recursive_triggers", 1),
                    ("busy_timeout", 10000),
                ):
                    cursor.execute(f"PRAGMA {pragma}={value}")
                    cursor.execute(f"PRAGMA {pragma}")
                    if cursor.fetchone() != (value,):
                        raise RuntimeError("Required SQLite connection setting failed")
                cursor.execute("PRAGMA journal_mode=WAL")
                if cursor.fetchone() != ("wal",):
                    raise RuntimeError("SQLite WAL is required")
            finally:
                cursor.close()

        @event.listens_for(engine, "begin")
        def begin_sqlite(connection: Connection) -> None:
            # SQLite ignores FOR UPDATE; serialize local identity transactions.
            connection.exec_driver_sql("BEGIN IMMEDIATE")

        return engine
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=2,
        connect_args={"connect_timeout": 2, "options": "-c statement_timeout=3000"},
        echo=False,
        hide_parameters=True,
    )


def get_session(request: Request) -> Generator[Session]:
    # Services own commit/transaction decisions; close rolls back pending writes.
    with Session(request.app.state.engine) as session:
        yield session
