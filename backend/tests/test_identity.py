import io
import logging
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.database import create_database_engine
from app.identity import cli, service
from app.identity.models import AuthEvent, AuthSession, LoginLimit, User
from app.identity.security import (
    COOKIE,
    AuthSettings,
    csrf_token,
    token_hash,
    verify_password,
)
from app.main import create_app
from app.observability import logger

pytestmark = pytest.mark.integration
PASSWORD = "a synthetic password phrase"


@pytest.fixture
def migrated(disposable_database: None) -> Config:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    return config


@pytest.fixture
def api() -> FastAPI:
    return create_app()


@pytest.fixture
def log_output() -> io.StringIO:
    return io.StringIO()


@pytest.fixture
def client(
    migrated: Config,
    api: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    log_output: io.StringIO,
) -> Iterator[TestClient]:
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_ORIGIN", "http://127.0.0.1:5173")
    handlers = logger.handlers[:]
    try:
        with TestClient(api) as client:
            handler = logger.handlers[0]
            assert isinstance(handler, logging.StreamHandler)
            handler.setStream(log_output)
            with Session(api.state.engine) as db:
                service.provision_user(db, "alice", PASSWORD)
                service.provision_user(db, "bravo", PASSWORD)
            yield client
    finally:
        logger.handlers = handlers


def signin(
    client: TestClient, username: str = "alice", password: str = PASSWORD
) -> dict[str, str]:
    response = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200
    data: dict[str, str] = response.json()
    return data


def test_login_cookie_self_identity_and_no_company_grants(
    api: FastAPI, client: TestClient
) -> None:
    response = client.post(
        "/api/auth/login", json={"username": "ALICE", "password": PASSWORD}
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"id", "username", "csrf_token"}
    assert data["username"] == "alice"
    cookie = client.cookies.get(COOKIE)
    assert cookie and cookie not in response.text and PASSWORD not in response.text
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    assert "Path=/api" in response.headers["set-cookie"]
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/auth/me").json() == data
    assert (
        client.get(
            "/api/companies/company-b/invoices",
            headers={"X-Role": "admin", "X-Company-ID": "company-b"},
        ).status_code
        == 404
    )
    with Session(api.state.engine) as db:
        stored = db.get(AuthSession, token_hash(cookie))
        assert stored is not None and stored.token_hash != cookie
        user = db.scalar(select(User).where(User.username == "alice"))
        assert user is not None and user.password_hash != PASSWORD


@pytest.mark.parametrize(
    "username,password", [("alice", "wrong"), ("missing", "wrong")]
)
def test_credentials_fail_generically_and_are_audited(
    api: FastAPI, client: TestClient, username: str, password: str
) -> None:
    response = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Unauthorized"
    assert COOKIE not in client.cookies
    with Session(api.state.engine) as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(AuthEvent)
                .where(AuthEvent.kind == "login_failed")
            )
            == 1
        )


def test_rotation_logout_csrf_and_replay(client: TestClient) -> None:
    signin(client)
    old = client.cookies.get(COOKIE)
    assert old is not None
    data = signin(client)
    new = client.cookies.get(COOKIE)
    assert old != new
    assert (
        client.get("/api/auth/me", headers={"Cookie": f"{COOKIE}={old}"}).status_code
        == 401
    )
    assert client.post("/api/auth/logout").status_code == 403
    assert (
        client.post(
            "/api/auth/logout", headers={"X-CSRF-Token": csrf_token(old)}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/logout", headers={"X-CSRF-Token": data["csrf_token"]}
        ).status_code
        == 204
    )
    assert (
        client.get("/api/auth/me", headers={"Cookie": f"{COOKIE}={new}"}).status_code
        == 401
    )


def test_origin_and_payload_privilege_injection_are_rejected(
    client: TestClient,
) -> None:
    body = {"username": "alice", "password": PASSWORD}
    assert (
        client.post(
            "/api/auth/login", json=body, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post("/api/auth/login", json={**body, "role": "admin"}).status_code
        == 422
    )
    assert client.post("/api/auth/users", json=body).status_code == 404
    data = signin(client)
    assert (
        client.post(
            "/api/auth/logout",
            headers={
                "Origin": "https://evil.example",
                "X-CSRF-Token": data["csrf_token"],
            },
        ).status_code
        == 403
    )
    assert client.get("/api/auth/me").status_code == 200


def test_expired_and_deactivated_sessions_fail_immediately(
    api: FastAPI, client: TestClient
) -> None:
    signin(client)
    with Session(api.state.engine) as db:
        db.execute(
            update(AuthSession).values(
                expires_at=datetime.now(UTC) - timedelta(seconds=1)
            )
        )
        db.commit()
    assert client.get("/api/auth/me").status_code == 401
    signin(client)
    with Session(api.state.engine) as db:
        service.manage_user(db, "alice")
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/auth/login", json={"username": "alice", "password": PASSWORD}
        ).status_code
        == 401
    )


def test_password_change_and_operator_reset_revoke_sessions(
    api: FastAPI, client: TestClient
) -> None:
    data = signin(client)
    old_token = client.cookies.get(COOKIE)
    headers = {"X-CSRF-Token": data["csrf_token"]}
    new = "a different synthetic passphrase"
    assert (
        client.post(
            "/api/auth/password",
            json={"current_password": "wrong", "new_password": new},
            headers=headers,
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/password",
            json={"current_password": PASSWORD, "new_password": new},
            headers=headers,
        ).status_code
        == 204
    )
    assert (
        client.get(
            "/api/auth/me", headers={"Cookie": f"{COOKIE}={old_token}"}
        ).status_code
        == 401
    )
    signin(client, password=new)
    with Session(api.state.engine) as db:
        service.manage_user(db, "alice", PASSWORD)
    assert client.get("/api/auth/me").status_code == 401
    signin(client)


def test_per_name_attempt_limits_and_window_reset(
    api: FastAPI, client: TestClient
) -> None:
    body = {"username": "unknown", "password": "wrong"}
    assert [
        client.post("/api/auth/login", json=body).status_code for _ in range(6)
    ] == [401] * 5 + [429]
    with Session(api.state.engine) as db:
        db.execute(
            update(LoginLimit).values(
                window_started=datetime.now(UTC) - timedelta(minutes=16)
            )
        )
        db.commit()
    assert client.post("/api/auth/login", json=body).status_code == 401


def test_global_limit_and_concurrent_name_limit(
    api: FastAPI, client: TestClient
) -> None:
    with Session(api.state.engine) as db:
        db.add(LoginLimit(key="global", attempts=60, window_started=datetime.now(UTC)))
        db.commit()
    assert (
        client.post(
            "/api/auth/login", json={"username": "alice", "password": PASSWORD}
        ).status_code
        == 429
    )
    with Session(api.state.engine) as db:
        db.execute(
            update(LoginLimit).values(
                window_started=datetime.now(UTC) - timedelta(minutes=16)
            )
        )
        db.commit()

    def attempt(_: int) -> int:
        return client.post(
            "/api/auth/login", json={"username": "parallel", "password": "wrong"}
        ).status_code

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(attempt, range(8)))
    assert results.count(401) == 5 and results.count(429) == 3


def test_user_uniqueness_and_cli_prompts(
    api: FastAPI, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    with Session(api.state.engine) as db:
        with pytest.raises(IntegrityError):
            service.provision_user(db, "ALICE", PASSWORD)
        db.rollback()
    monkeypatch.setattr(sys, "argv", ["identity", "create-user", "charlie"])
    monkeypatch.setattr("getpass.getpass", lambda _: PASSWORD)
    cli.main()
    with Session(api.state.engine) as db:
        user = db.scalar(select(User).where(User.username == "charlie"))
        assert user is not None and verify_password(PASSWORD, user.password_hash)


def test_current_head_and_safe_empty_downgrade(migrated: Config) -> None:
    engine = create_database_engine()
    try:
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version",
            "auth_users",
            "auth_sessions",
            "auth_login_limits",
            "auth_events",
            "auth_account_changes",
            "auth_password_resets",
        }
        command.upgrade(migrated, "head")
        command.check(migrated)
        command.downgrade(migrated, "base")
        assert inspect(engine).get_table_names() == ["alembic_version"]
        command.upgrade(migrated, "head")
        command.check(migrated)
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE auth_events SET source='api'",
        "DELETE FROM auth_events",
        "TRUNCATE auth_events",
    ],
)
def test_authentication_events_reject_mutation(
    api: FastAPI, client: TestClient, statement: str
) -> None:
    with Session(api.state.engine) as db:
        with pytest.raises(DBAPIError, match="Authentication events are immutable"):
            db.execute(text(statement))
        db.rollback()
        assert db.scalar(select(func.count()).select_from(AuthEvent)) == 2


def test_secure_cookie_and_cross_user_csrf(api: FastAPI, client: TestClient) -> None:
    alice = signin(client)
    bravo = signin(client, "bravo")
    assert alice["id"] != bravo["id"]
    assert (
        client.post(
            "/api/auth/logout", headers={"X-CSRF-Token": alice["csrf_token"]}
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/auth/me",
            headers={"X-User-ID": alice["id"], "Authorization": "Bearer forged"},
        ).json()["id"]
        == bravo["id"]
    )
    api.state.auth_settings = AuthSettings("http://127.0.0.1:5173", True)
    response = client.post(
        "/api/auth/login", json={"username": "alice", "password": PASSWORD}
    )
    assert response.status_code == 200
    assert "; Secure" in response.headers["set-cookie"]


def test_password_change_revokes_other_sessions(client: TestClient) -> None:
    signin(client)
    first = client.cookies.get(COOKIE)
    client.cookies.clear()
    second = signin(client)
    assert (
        client.get("/api/auth/me", headers={"Cookie": f"{COOKIE}={first}"}).status_code
        == 200
    )
    response = client.post(
        "/api/auth/password",
        json={"current_password": PASSWORD, "new_password": "a new synthetic password"},
        headers={"X-CSRF-Token": second["csrf_token"]},
    )
    assert response.status_code == 204
    assert (
        client.get("/api/auth/me", headers={"Cookie": f"{COOKIE}={first}"}).status_code
        == 401
    )


def test_password_token_and_username_are_absent_from_logs(
    client: TestClient, api: FastAPI, log_output: io.StringIO
) -> None:
    data = signin(client)
    cookie = client.cookies.get(COOKIE)
    assert cookie is not None
    with Session(api.state.engine) as db:
        user = db.scalar(select(User).where(User.username == "alice"))
        assert user is not None
        encoded = user.password_hash
    output = log_output.getvalue()
    for value in (PASSWORD, cookie, data["csrf_token"], encoded, "alice"):
        assert value not in output


def test_cli_confirmation_mismatch_creates_no_user(
    client: TestClient, api: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["identity", "create-user", "charlie"])
    values = iter([PASSWORD, "different synthetic password"])
    monkeypatch.setattr("getpass.getpass", lambda _: next(values))
    with pytest.raises(SystemExit) as caught:
        cli.main()
    assert caught.value.code == 1
    with Session(api.state.engine) as db:
        assert db.scalar(select(User).where(User.username == "charlie")) is None


def test_populated_downgrade_refuses_to_destroy_identity(
    api: FastAPI, client: TestClient, migrated: Config
) -> None:
    with pytest.raises(RuntimeError, match="requires empty tables"):
        command.downgrade(migrated, "base")
    with Session(api.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 2
        assert db.scalar(select(func.count()).select_from(AuthEvent)) == 2
    assert signin(client)["username"] == "alice"
