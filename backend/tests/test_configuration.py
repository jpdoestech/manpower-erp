from collections.abc import Iterator
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine

import app.main as main
from alembic import command
from app.database import database_url
from app.observability import logger


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in (
        "DATABASE_URL",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_DB",
    ):
        monkeypatch.delenv(key, raising=False)
    handlers = logger.handlers[:]
    yield
    logger.handlers = handlers


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "not-a-url-secret",
        "sqlite:///secret",
        "mysql://user:secret@host/db",
        "postgresql:///secret",
        "postgresql://user:secret@host:notaport/db",
    ],
)
def test_invalid_config_does_not_disclose_values(
    monkeypatch: pytest.MonkeyPatch, raw: str | None
) -> None:
    if raw is not None:
        monkeypatch.setenv("DATABASE_URL", raw)
    with pytest.raises(RuntimeError) as caught:
        database_url()
    assert str(caught.value) == "Valid PostgreSQL database configuration is required"
    assert caught.value.__suppress_context__


def test_url_preserves_encoded_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:p%40ss%2F%25@127.0.0.1:5432/test"
    )
    url = database_url()
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss/%"
    assert "p@ss/%" not in str(url)


def test_compose_components_preserve_special_characters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key, value in {
        "POSTGRES_HOST": "db",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "p@ss/%#'",
        "POSTGRES_DB": "test",
    }.items():
        monkeypatch.setenv(key, value)
    assert database_url().password == "p@ss/%#'"
    monkeypatch.setenv("POSTGRES_PASSWORD", "")
    with pytest.raises(RuntimeError):
        database_url()


def test_pool_is_disposed_at_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = MagicMock(spec=Engine)
    monkeypatch.setattr(main, "create_database_engine", lambda: engine)
    with TestClient(main.create_app()) as client:
        assert client.get("/api/health/live").status_code == 200
        engine.connect.assert_not_called()
    engine.dispose.assert_called_once_with()


def test_startup_requires_valid_configuration() -> None:
    with pytest.raises(RuntimeError, match="Valid PostgreSQL database configuration"):
        with TestClient(main.create_app()):
            pass


def test_offline_migration_does_not_connect_or_print_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:offline-secret@127.0.0.1:1/test"
    )
    output = StringIO()
    config = Config(
        str(Path(__file__).parents[1] / "alembic.ini"), output_buffer=output
    )
    command.upgrade(config, "head", sql=True)
    assert "CREATE TABLE alembic_version" in output.getvalue()
    assert "0001_infrastructure" in output.getvalue()
    assert "offline-secret" not in output.getvalue()
