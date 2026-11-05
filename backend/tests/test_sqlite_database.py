import sys
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session
from test_sqlite_identity import disposable_database as disposable_database

import app.database as database
from alembic import command
from app.database import LOCAL_DIRECTORY, create_database_engine, database_url
from app.identity import cli
from app.identity.models import AuthEvent, AuthSession, User
from app.identity.security import auth_settings, verify_password


def test_unpatched_wal_runtime_is_rejected(
    disposable_database: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(database, "sqlite_version_info", (3, 50, 4))
    with pytest.raises(RuntimeError, match="WAL-reset fix"):
        create_database_engine()


def test_cli_accepts_exactly_15_characters_on_disposable_sqlite(
    disposable_database: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    command.upgrade(Config("alembic.ini"), "head")
    password = "A" * 15
    monkeypatch.setattr("getpass.getpass", lambda _: password)
    monkeypatch.setattr(sys, "argv", ["identity", "create-user", "example"])
    cli.main()
    output = capsys.readouterr()
    assert "Identity operation completed" in output.out
    assert password not in output.out + output.err
    engine = create_database_engine()
    try:
        with Session(engine) as db:
            user = db.scalar(select(User).where(User.username == "example"))
            assert user and user.is_active and not user.is_super_admin
            assert user.password_hash != password
            assert verify_password(password, user.password_hash)
    finally:
        engine.dispose()


def test_sqlite_offline_migration_is_explicitly_rejected(
    disposable_database: None,
) -> None:
    with pytest.raises(RuntimeError, match="online data verification"):
        command.upgrade(Config("alembic.ini"), "head", sql=True)


@pytest.mark.parametrize(
    "environment,raw",
    [
        ("production", "sqlite:///./.local/a.db"),
        ("staging", "sqlite:///./.local/a.db"),
        ("", "sqlite:///./.local/a.db"),
        ("local", "sqlite:///:memory:"),
        ("local", "sqlite:///../outside.db"),
        ("local", "sqlite:///./.local/../../outside.db"),
        ("local", "sqlite:////server/share/a.db"),
        ("local", "sqlite:///./.local/a.db?mode=ro"),
        ("local", "sqlite:///./.local/a.txt"),
        ("local", "postgresql://user:secret@localhost/db"),
    ],
)
def test_sqlite_configuration_rejects_unsafe_modes_and_paths(
    monkeypatch: pytest.MonkeyPatch, environment: str, raw: str
) -> None:
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("APP_ENV", environment)
    monkeypatch.setenv("DATABASE_URL", raw)
    with pytest.raises(RuntimeError, match="Valid local SQLite") as failure:
        database_url()
    assert "secret" not in str(failure.value)


def test_explicit_modes_and_unimplemented_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("DATABASE_MODE", "postgres")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./.local/a.db")
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        database_url()
    monkeypatch.setenv("DATABASE_MODE", "unknown")
    with pytest.raises(RuntimeError, match="Unsupported"):
        database_url()
    monkeypatch.setenv("DATABASE_MODE", "supabase")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:secret@host/db?sslmode=require")
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        database_url()
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://u:secret@host/db?sslmode=verify-full"
    )
    assert database_url().drivername == "postgresql+psycopg"
    monkeypatch.setenv("AUTH_PROVIDER", "supabase")
    with pytest.raises(RuntimeError, match="not implemented"):
        auth_settings()
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./.local/a.db")
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(RuntimeError, match="SQLite"):
        database_url()


def test_relative_path_is_anchored_to_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./.local/example.db")
    monkeypatch.chdir(LOCAL_DIRECTORY.parent / "backend")
    assert database_url().database == str(LOCAL_DIRECTORY / "example.db")


def test_migrations_constraints_utc_and_rollback(disposable_database: None) -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    command.check(config)
    engine = create_database_engine()
    try:
        for _ in range(2):
            with engine.connect() as connection:
                assert connection.scalar(text("PRAGMA foreign_keys")) == 1
                assert connection.scalar(text("PRAGMA recursive_triggers")) == 1
                assert connection.scalar(text("PRAGMA busy_timeout")) == 10000
                assert connection.scalar(text("PRAGMA journal_mode")) == "wal"
            engine.dispose()
        with Session(engine) as db:
            new_user = User(username="valid", password_hash="hash")
            db.add(new_user)
            db.commit()
            user_id = new_user.id
            assert new_user.created_at.tzinfo == UTC
        with Session(engine) as db:
            user = db.get(User, user_id)
            assert user
            user.is_active = False
            db.flush()
        with Session(engine) as db:
            user = db.get(User, user_id)
            assert user and user.is_active
            expiry = datetime.now(timezone(timedelta(hours=8)))
            db.add(AuthSession(token_hash="a" * 64, user_id=user_id, expires_at=expiry))
            db.commit()
            stored = db.get(AuthSession, "a" * 64)
            assert (
                stored
                and stored.expires_at == expiry
                and stored.expires_at.tzinfo == UTC
            )
            db.add(
                AuthSession(
                    token_hash="b" * 64,
                    user_id=user_id,
                    expires_at=datetime(2026, 1, 1),
                )
            )
            with pytest.raises(StatementError, match="Timezone-aware"):
                db.commit()
            db.rollback()
        for sql in (
            "UPDATE auth_users SET is_active = 2",
            "UPDATE auth_users SET is_super_admin = 2",
            "UPDATE auth_users SET id = 'invalid-uuid'",
            "UPDATE auth_users SET password_hash = '" + "a" * 513 + "'",
            "UPDATE auth_users SET username = 'BadName'",
            "UPDATE auth_users SET username = 'abc' || char(0) || 'def'",
            "DELETE FROM auth_users",
            "UPDATE auth_sessions SET user_id = '" + uuid4().hex + "'",
        ):
            with pytest.raises(IntegrityError), engine.begin() as connection:
                connection.exec_driver_sql(sql)
        with Session(engine) as db:
            event = AuthEvent(
                kind="test", source="test", request_id=uuid4(), user_id=user_id
            )
            db.add(event)
            db.commit()
        for operation in (
            "UPDATE auth_events SET kind='altered'",
            "DELETE FROM auth_events",
        ):
            with (
                pytest.raises(IntegrityError, match="immutable"),
                engine.begin() as connection,
            ):
                connection.exec_driver_sql(operation)
        with (
            pytest.raises(IntegrityError, match="immutable"),
            engine.begin() as connection,
        ):
            connection.exec_driver_sql(
                "INSERT OR REPLACE INTO auth_events SELECT * FROM auth_events"
            )
        with pytest.raises(RuntimeError, match="preserve user/audit history"):
            command.downgrade(config, "base")
        with Session(engine) as db:
            assert db.scalar(select(AuthEvent)) and db.get(User, user_id)
    finally:
        engine.dispose()


def test_populated_upgrade_preserves_history(disposable_database: None) -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "0002_identity")
    engine = create_database_engine()
    user_id, event_id = uuid4(), uuid4()
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO auth_users (id, username, password_hash) VALUES (?, ?, ?)",
                (user_id.hex, "existing", "old-hash"),
            )
            connection.exec_driver_sql(
                "INSERT INTO auth_events (id, user_id, kind, source, request_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    event_id.hex,
                    user_id.hex,
                    "user_created",
                    "operator_cli",
                    uuid4().hex,
                ),
            )
        command.upgrade(config, "head")
        command.check(config)
        with Session(engine) as db:
            user = db.get(User, user_id)
            assert user and not user.is_super_admin and user.password_hash == "old-hash"
            assert db.get(AuthEvent, event_id)
        command.downgrade(config, "0002_identity")
        command.upgrade(config, "head")
        with Session(engine) as db:
            assert db.get(User, user_id) and db.get(AuthEvent, event_id)
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        assert len(inspect(engine).get_foreign_keys("auth_events")) == 3
    finally:
        engine.dispose()


def test_invalid_existing_data_aborts_migration_atomically(
    disposable_database: None,
) -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "0003_account_controls")
    engine = create_database_engine()
    try:
        user_id = uuid4().hex
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO auth_users (id, username, password_hash) VALUES (?, ?, ?)",
                (user_id, "existing", "hash"),
            )
            connection.exec_driver_sql(
                "INSERT INTO auth_password_resets (token_hash, user_id, expires_at) "
                "VALUES (?, ?, ?)",
                ("x" * 65, user_id, "2026-11-04 00:00:00"),
            )
        with pytest.raises(RuntimeError, match="valid existing data"):
            command.upgrade(config, "head")
        with engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "0003_account_controls"
            )
            assert (
                connection.scalar(text("SELECT count(*) FROM auth_password_resets"))
                == 1
            )
            assert not connection.exec_driver_sql(
                "SELECT name FROM sqlite_master "
                "WHERE type='trigger' AND name LIKE '%_limits_%'"
            ).all()
    finally:
        engine.dispose()
