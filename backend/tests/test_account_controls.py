import io
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session
from test_identity import PASSWORD, signin
from test_identity import api as api
from test_identity import client as client
from test_identity import log_output as log_output
from test_identity import migrated as migrated

from alembic import command
from app.database import create_database_engine
from app.identity import administration, cli, service
from app.identity.models import (
    AccountChange,
    AuthEvent,
    AuthSession,
    LoginLimit,
    PasswordReset,
    User,
)
from app.identity.security import COOKIE, token_hash

pytestmark = pytest.mark.integration
NEW_PASSWORD = "another synthetic recovery passphrase"


@pytest.fixture
def admins(api: FastAPI, client: TestClient) -> tuple[dict[str, str], dict[str, str]]:
    with Session(api.state.engine) as db:
        administration.bootstrap(db, "rootone", PASSWORD, "roottwo", PASSWORD)
    result = []
    for name in ("rootone", "roottwo"):
        client.cookies.clear()
        current = signin(client, name)
        current["cookie"] = str(client.cookies.get(COOKIE))
        result.append(current)
    client.cookies.clear()
    return result[0], result[1]


def post(
    client: TestClient, actor: dict[str, str], path: str, body: dict[str, str]
) -> Response:
    return client.post(
        "/api/auth/admin/requests" + path,
        json={"current_password": PASSWORD, **body},
        headers={
            "Cookie": f"{COOKIE}={actor['cookie']}",
            "X-CSRF-Token": actor["csrf_token"],
        },
    )


def request(
    client: TestClient, actor: dict[str, str], action: str, username: str = "alice"
) -> str:
    response = post(client, actor, "", {"username": username, "action": action})
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def approve(client: TestClient, actor: dict[str, str], change: str) -> Response:
    return post(client, actor, f"/{change}/approve", {})


def issue(
    client: TestClient,
    admins: tuple[dict[str, str], dict[str, str]],
    username: str = "alice",
) -> str:
    response = approve(
        client, admins[1], request(client, admins[0], "reset_password", username)
    )
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return str(response.json()["reset_token"])


def recover(client: TestClient, token: str) -> Response:
    return client.post(
        "/api/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
    )


def test_registration_requires_admin_and_distinct_approval(
    client: TestClient, api: FastAPI, admins: tuple[dict[str, str], dict[str, str]]
) -> None:
    change = request(client, admins[0], "register", "newuser")
    pending = client.get(
        "/api/auth/admin/requests",
        headers={"Cookie": f"{COOKIE}={admins[1]['cookie']}"},
    )
    assert pending.status_code == 200 and pending.headers["cache-control"] == "no-store"
    assert pending.json()[0]["username"] == "newuser"
    assert "password" not in pending.text
    assert approve(client, admins[0], change).status_code == 403
    assert (
        client.post(
            "/api/auth/login", json={"username": "newuser", "password": PASSWORD}
        ).status_code
        == 401
    )
    response = approve(client, admins[1], change)
    assert response.status_code == 200
    token = response.json()["reset_token"]
    assert recover(client, token).status_code == 204
    assert signin(client, "newuser", NEW_PASSWORD)["username"] == "newuser"
    assert approve(client, admins[1], change).status_code == 409
    with Session(api.state.engine) as db:
        user = db.scalar(select(User).where(User.username == "newuser"))
        assert user is not None and user.is_active and not user.is_super_admin
        record = db.get(AccountChange, UUID(change))
        assert (
            record
            and str(record.requested_by) == admins[0]["id"]
            and str(record.approved_by) == admins[1]["id"]
        )
        event = db.scalar(
            select(AuthEvent).where(
                AuthEvent.kind == "account_change_approved",
                AuthEvent.change_id == UUID(change),
            )
        )
        assert (
            event
            and str(event.actor_id) == admins[1]["id"]
            and event.user_id == user.id
        )


def test_admin_access_denies_anonymous_ordinary_forged_headers_and_csrf(
    client: TestClient, admins: tuple[dict[str, str], dict[str, str]]
) -> None:
    client.cookies.clear()
    assert client.get("/api/auth/admin/requests").status_code == 401
    normal = signin(client)
    assert (
        client.get(
            "/api/auth/admin/requests",
            headers={"X-Role": "Super Admin", "X-Company-ID": "company-b"},
        ).status_code
        == 403
    )
    assert (
        post(
            client,
            {**normal, "cookie": str(client.cookies.get(COOKIE))},
            "",
            {"username": "newuser", "action": "register"},
        ).status_code
        == 403
    )
    for headers in (
        {},
        {"X-CSRF-Token": "forged"},
        {"X-CSRF-Token": admins[0]["csrf_token"], "Origin": "https://evil.invalid"},
    ):
        assert (
            client.post(
                "/api/auth/admin/requests",
                json={
                    "username": "newuser",
                    "action": "register",
                    "current_password": PASSWORD,
                },
                headers={"Cookie": f"{COOKIE}={admins[0]['cookie']}", **headers},
            ).status_code
            == 403
        )
    assert (
        post(
            client,
            admins[0],
            "",
            {"username": "newuser", "action": "register", "is_super_admin": "true"},
        ).status_code
        == 422
    )
    assert (
        post(
            client,
            admins[0],
            "",
            {"username": "newuser", "action": "register", "current_password": "wrong"},
        ).status_code
        == 401
    )


def test_reset_hash_single_use_and_session_revocation(
    client: TestClient,
    api: FastAPI,
    admins: tuple[dict[str, str], dict[str, str]],
    log_output: io.StringIO,
) -> None:
    signin(client)
    cookie = client.cookies.get(COOKIE)
    token = issue(client, admins)
    assert len(token) == 43
    assert (
        client.get("/api/auth/me", headers={"Cookie": f"{COOKIE}={cookie}"}).status_code
        == 401
    )
    with Session(api.state.engine) as db:
        stored = db.get(PasswordReset, token_hash(token))
        assert (
            stored
            and stored.used_at is None
            and stored.expires_at <= datetime.now(UTC) + timedelta(minutes=15)
        )
        assert not db.get(PasswordReset, token)
    assert recover(client, token).status_code == 204
    assert recover(client, token).status_code == 400
    assert recover(client, "x" * 43).status_code == 400
    assert signin(client, password=NEW_PASSWORD)["username"] == "alice"
    assert (
        token not in log_output.getvalue() and NEW_PASSWORD not in log_output.getvalue()
    )


@pytest.mark.parametrize(
    "state", ["expired", "inactive", "replaced", "operator_reset", "changed"]
)
def test_invalidated_recovery_fails_generically(
    client: TestClient,
    api: FastAPI,
    admins: tuple[dict[str, str], dict[str, str]],
    state: str,
) -> None:
    token = issue(client, admins)
    with Session(api.state.engine) as db:
        if state == "expired":
            db.execute(
                update(PasswordReset).values(
                    expires_at=datetime.now(UTC) - timedelta(seconds=1)
                )
            )
        elif state == "inactive":
            service.manage_user(db, "alice")
        elif state == "operator_reset":
            service.manage_user(db, "alice", NEW_PASSWORD)
        db.commit()
    if state == "replaced":
        assert issue(client, admins) != token
    elif state == "changed":
        own = signin(client)
        assert (
            client.post(
                "/api/auth/password",
                json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
                headers={"X-CSRF-Token": own["csrf_token"]},
            ).status_code
            == 204
        )
    response = recover(client, token)
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Bad Request"


def test_target_cannot_approve_own_reset_and_actors_rechecked(
    client: TestClient, api: FastAPI, admins: tuple[dict[str, str], dict[str, str]]
) -> None:
    change = request(client, admins[0], "reset_password", "roottwo")
    assert approve(client, admins[1], change).status_code == 403
    change = request(client, admins[0], "reset_password", "alice")
    with Session(api.state.engine) as db:
        service.manage_user(db, "rootone")
    assert approve(client, admins[1], change).status_code == 403
    assert approve(client, admins[0], change).status_code == 401


def test_requester_revoked_or_request_expired(
    client: TestClient, api: FastAPI, admins: tuple[dict[str, str], dict[str, str]]
) -> None:
    change = request(client, admins[0], "reset_password")
    with Session(api.state.engine) as db:
        db.execute(
            update(AccountChange).values(
                expires_at=datetime.now(UTC) - timedelta(seconds=1)
            )
        )
        db.commit()
    assert approve(client, admins[1], change).status_code == 409
    with Session(api.state.engine) as db:
        db.execute(
            update(User).where(User.username == "rootone").values(is_super_admin=False)
        )
        db.commit()
    assert approve(client, admins[1], change).status_code == 403


def test_deactivate_and_unlock_are_independently_approved(
    client: TestClient, api: FastAPI, admins: tuple[dict[str, str], dict[str, str]]
) -> None:
    signin(client)
    old_cookie = client.cookies.get(COOKIE)
    with Session(api.state.engine) as db:
        limit = db.get(LoginLimit, "name:" + token_hash("alice"))
        assert limit
        limit.attempts = 6
        db.commit()
    change = request(client, admins[0], "unlock")
    assert approve(client, admins[1], change).status_code == 200
    with Session(api.state.engine) as db:
        assert db.get(LoginLimit, "name:" + token_hash("alice")) is None
        assert db.get(LoginLimit, "global") is not None
    change = request(client, admins[0], "deactivate")
    assert approve(client, admins[1], change).json() == {"reset_token": None}
    assert (
        client.get(
            "/api/auth/me", headers={"Cookie": f"{COOKIE}={old_cookie}"}
        ).status_code
        == 401
    )
    change = request(client, admins[0], "activate")
    assert approve(client, admins[1], change).status_code == 200
    assert (
        client.post(
            "/api/auth/login", json={"username": "alice", "password": PASSWORD}
        ).status_code
        == 401
    )


def test_admin_throttle_and_pair_preservation(
    client: TestClient, admins: tuple[dict[str, str], dict[str, str]]
) -> None:
    change = request(client, admins[0], "deactivate", "rootone")
    assert approve(client, admins[1], change).status_code == 409
    for _ in range(3):
        assert (
            post(
                client,
                admins[0],
                "",
                {"username": "alice", "action": "unlock", "current_password": "wrong"},
            ).status_code
            == 401
        )
    assert (
        post(
            client, admins[0], "", {"username": "alice", "action": "unlock"}
        ).status_code
        == 429
    )


def test_concurrent_token_redemption_is_single_use(
    api: FastAPI, client: TestClient, admins: tuple[dict[str, str], dict[str, str]]
) -> None:
    token = issue(client, admins)

    def redeem(_: int) -> int:
        with Session(api.state.engine) as db:
            try:
                administration.reset_password(db, token, NEW_PASSWORD, uuid4())
                return 204
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(redeem, range(2))) == [204, 400]


def test_concurrent_approval_issues_only_one_token(
    api: FastAPI,
    client: TestClient,
    admins: tuple[dict[str, str], dict[str, str]],
    migrated: Config,
) -> None:
    change = request(client, admins[0], "reset_password")

    def complete(_: int) -> int:
        with Session(api.state.engine) as db:
            current = service.authenticate(db, admins[1]["cookie"])
            try:
                assert administration.approve_change(
                    db, current, UUID(change), PASSWORD, uuid4()
                )
                return 200
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(complete, range(2))) == [200, 409]
    with Session(api.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(PasswordReset)) == 1
        assert (
            db.scalar(
                select(func.count())
                .select_from(AuthEvent)
                .where(AuthEvent.kind == "account_change_approved")
            )
            == 1
        )
    with pytest.raises(RuntimeError, match="security history"):
        command.downgrade(migrated, "0002_identity")


def test_recovery_rate_limit_origin_validation_and_no_auto_login(
    client: TestClient, admins: tuple[dict[str, str], dict[str, str]]
) -> None:
    token = issue(client, admins)
    assert (
        client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": NEW_PASSWORD},
            headers={"Origin": "https://evil.invalid"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/reset-password",
            json={"token": "short", "new_password": NEW_PASSWORD},
        ).status_code
        == 422
    )
    assert recover(client, token).status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    for _ in range(4):
        assert recover(client, token).status_code == 400
    assert recover(client, token).status_code == 429


def test_bootstrap_rolls_back_first_account_when_second_conflicts(
    client: TestClient, api: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["identity", "bootstrap-admins", "freshadmin", "alice"]
    )
    monkeypatch.setattr("getpass.getpass", lambda _: PASSWORD)
    with pytest.raises(SystemExit) as failure:
        cli.main()
    assert failure.value.code == 1
    with Session(api.state.engine) as db:
        assert db.scalar(select(User).where(User.username == "freshadmin")) is None
        assert (
            db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_super_admin.is_(True))
            )
            == 0
        )


def test_bootstrap_cli_is_atomic_one_time_and_hidden(
    client: TestClient, api: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["identity", "bootstrap-admins", "rootone", "roottwo"]
    )
    prompts: list[str] = []

    def hidden(prompt: str) -> str:
        prompts.append(prompt)
        return PASSWORD

    monkeypatch.setattr("getpass.getpass", hidden)
    cli.main()
    assert len(prompts) == 4
    with Session(api.state.engine) as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_super_admin.is_(True))
            )
            == 2
        )
        with pytest.raises(ValueError, match="already"):
            administration.bootstrap(db, "rootthree", PASSWORD, "rootfour", PASSWORD)
        db.rollback()
    with pytest.raises(SystemExit) as failure:
        cli.main()
    assert failure.value.code == 1


def test_bootstrap_duplicate_rolls_back_and_concurrency(migrated: Config) -> None:
    engine = create_database_engine()
    try:
        with Session(engine) as db:
            with pytest.raises(ValueError, match="Distinct"):
                administration.bootstrap(db, "same", PASSWORD, "SAME", PASSWORD)

        def boot(_: int) -> bool:
            with Session(engine) as db:
                try:
                    administration.bootstrap(
                        db, "rootone", PASSWORD, "roottwo", PASSWORD
                    )
                    return True
                except ValueError:
                    return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(boot, range(2))) == [False, True]
    finally:
        engine.dispose()


def test_0002_data_survives_upgrade_and_new_history_blocks_rollback(
    disposable_database: None,
) -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "0002_identity")
    engine = create_database_engine()
    user_id, event_id = uuid4(), uuid4()
    try:
        with engine.begin() as db:
            db.execute(
                text(
                    "INSERT INTO auth_users (id, username, password_hash) "
                    "VALUES (:id, 'existing', 'old-hash')"
                ),
                {"id": user_id},
            )
            db.execute(
                text(
                    "INSERT INTO auth_events (id, user_id, kind, source, request_id) "
                    "VALUES (:id, :user, 'user_created', 'operator_cli', :request)"
                ),
                {"id": event_id, "user": user_id, "request": uuid4()},
            )
            db.execute(
                text(
                    "INSERT INTO auth_sessions (token_hash, user_id, expires_at) "
                    "VALUES (:hash, :user, :expires)"
                ),
                {
                    "hash": "a" * 64,
                    "user": user_id,
                    "expires": datetime.now(UTC) + timedelta(hours=1),
                },
            )
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        command.check(config)
        with Session(engine) as db:
            user = db.get(User, user_id)
            assert (
                user
                and not user.is_super_admin
                and user.password_hash == "old-hash"
                and user.is_active
            )
            assert db.get(AuthEvent, event_id) and db.get(AuthSession, "a" * 64)
        command.downgrade(config, "0002_identity")
        command.upgrade(config, "head")
        with Session(engine) as db:
            administration.bootstrap(db, "rootone", PASSWORD, "roottwo", PASSWORD)
        with pytest.raises(RuntimeError, match="grants"):
            command.downgrade(config, "0002_identity")
        with Session(engine) as db:
            assert db.get(User, user_id) and db.get(AuthEvent, event_id)
            assert db.scalar(select(func.count()).select_from(User)) == 3
    finally:
        engine.dispose()
