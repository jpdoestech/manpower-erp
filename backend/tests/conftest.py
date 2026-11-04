import os
from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from app.database import database_url


@pytest.fixture
def disposable_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Only generated test databases are created/dropped; never migrate the input DB.
    assert os.environ["DATABASE_URL"]
    monkeypatch.setenv("DATABASE_MODE", "postgres")
    source = database_url().set(drivername="postgresql")
    name = f"p0_02_{uuid4().hex}"
    with psycopg.connect(
        source.render_as_string(hide_password=False), autocommit=True, connect_timeout=5
    ) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        try:
            monkeypatch.setenv(
                "DATABASE_URL",
                source.set(database=name).render_as_string(hide_password=False),
            )
            yield
        finally:
            admin.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
            )
