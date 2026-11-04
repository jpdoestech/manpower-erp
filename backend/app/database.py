import os
from collections.abc import Generator

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def database_url() -> URL:
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
        return url.set(drivername="postgresql+psycopg")
    except (KeyError, ValueError, SQLAlchemyError):
        raise RuntimeError(
            "Valid PostgreSQL database configuration is required"
        ) from None


def create_database_engine() -> Engine:
    return create_engine(
        database_url(),
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
