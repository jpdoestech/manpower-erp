import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import cast
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.database import create_database_engine
from app.identity.models import User
from app.identity.service import provision_user
from app.main import create_app
from app.organizations import cli
from app.organizations.models import Company, CompanyEvent, CompanyGrant
from app.organizations.service import (
    edit_company,
    provision_company,
    set_actor,
    set_grant,
)

pytestmark = pytest.mark.integration
PASSWORD = "synthetic company passphrase"


@pytest.fixture
def company_client(
    disposable_database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    command.upgrade(Config("alembic.ini"), "head")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_ORIGIN", "http://127.0.0.1:5173")
    app = create_app()
    with TestClient(app) as client:
        with Session(cast(FastAPI, client.app).state.engine) as db:
            for username in ("alice", "bravo", "ungranted"):
                user = provision_user(db, username, PASSWORD)
                if username == "ungranted":
                    user.is_super_admin = True
                    db.commit()
            provision_company(db, "ALPHA", "Alpha Company", "alice")
            provision_company(db, "BRAVO", "Bravo Company", "bravo")
        yield client


def signin(client: TestClient, username: str = "alice") -> dict[str, str]:
    response = client.post(
        "/api/auth/login", json={"username": username, "password": PASSWORD}
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def test_company_isolation_search_and_revocation(company_client: TestClient) -> None:
    client = company_client
    assert client.get("/api/companies").status_code == 401
    with Session(cast(FastAPI, client.app).state.engine) as db:
        other_id = db.scalar(select(Company.id).where(Company.code == "BRAVO"))
    assert other_id is not None
    headers = signin(client)
    response = client.get("/api/companies")
    assert response.headers["cache-control"] == "no-store"
    assert [row["code"] for row in response.json()] == ["ALPHA"]
    assert client.get("/api/companies?q=Bravo").json() == []
    assert client.get("/api/companies?q=%").json() == []
    assert client.get("/api/companies?active=false").json() == []
    assert client.get("/api/companies?offset=1").json() == []
    assert client.get("/api/companies?offset=-1").status_code == 422
    assert client.get(f"/api/companies/{other_id}").status_code == 404
    assert (
        client.patch(
            f"/api/companies/{other_id}",
            headers=headers,
            json={"legal_name": "Stolen", "is_active": True, "version": 1},
        ).status_code
        == 404
    )
    company_id = response.json()[0]["id"]
    with Session(cast(FastAPI, client.app).state.engine) as db:
        set_grant(db, other_id, "alice", True)
    assert len(client.get("/api/companies").json()) == 2
    with Session(cast(FastAPI, client.app).state.engine) as db:
        set_grant(db, other_id, "alice", False)
        set_grant(db, UUID(company_id), "alice", False)
    assert client.get("/api/companies").json() == []
    assert client.get(f"/api/companies/{company_id}").status_code == 404
    signin(client, "ungranted")
    assert (
        client.get(
            "/api/companies", headers={"X-Role": "admin", "X-Company-ID": company_id}
        ).json()
        == []
    )


def test_company_update_validation_conflict_and_audit(
    company_client: TestClient,
) -> None:
    client = company_client
    headers = signin(client)
    company = client.get("/api/companies").json()[0]
    url = f"/api/companies/{company['id']}"
    payload = {"legal_name": "Updated Alpha", "is_active": False, "version": 1}
    assert (
        client.patch(
            url, json={**payload, "version": True}, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.patch(
            url, json={**payload, "is_active": "false"}, headers=headers
        ).status_code
        == 422
    )
    assert client.patch(url, json=payload).status_code == 403
    assert (
        client.patch(
            url, json=payload, headers={**headers, "Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.patch(
            url, json={**payload, "legal_name": "  "}, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.patch(
            url, json={**payload, "code": "CHANGED"}, headers=headers
        ).status_code
        == 422
    )
    response = client.patch(url, json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["version"] == 2 and response.json()["is_active"] is False
    assert client.patch(url, json=payload, headers=headers).status_code == 409
    assert client.get("/api/companies?active=true").json() == []
    assert len(client.get("/api/companies?active=false").json()) == 1
    assert client.delete(url, headers=headers).status_code == 405
    with Session(cast(FastAPI, client.app).state.engine) as db:
        events = list(
            db.scalars(
                select(CompanyEvent).where(CompanyEvent.kind == "company_updated")
            )
        )
        assert len(events) == 1
        assert events[0].before_name == "Alpha Company"
        assert events[0].after_name == "Updated Alpha"
        assert events[0].actor_id is not None
        with pytest.raises(DBAPIError):
            db.execute(text("DELETE FROM org_company_events"))
        db.rollback()
        with pytest.raises(IntegrityError):
            provision_company(db, "ALPHA", "Duplicate", "bravo")
        db.rollback()
        with pytest.raises(IntegrityError):
            db.execute(text("DELETE FROM org_companies"))
        db.rollback()


def test_company_history_survives_failed_downgrade(company_client: TestClient) -> None:
    with pytest.raises(RuntimeError, match="preserve organization history"):
        command.downgrade(Config("alembic.ini"), "base")
    command.check(Config("alembic.ini"))
    with Session(cast(FastAPI, company_client.app).state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Company)) == 2
        assert db.scalar(select(func.count()).select_from(CompanyEvent)) == 2


def test_operator_cli_and_concurrent_edits(
    company_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = cast(FastAPI, company_client.app).state.engine
    monkeypatch.setattr(
        sys, "argv", ["organizations", "create", "CLI", "CLI Company", "alice"]
    )
    cli.main()
    with Session(engine) as db:
        company_id = db.scalar(select(Company.id).where(Company.code == "CLI"))
        user_id = db.scalar(select(User.id).where(User.username == "alice"))
        assert company_id is not None and user_id is not None
    monkeypatch.setattr(
        sys, "argv", ["organizations", "grant", str(company_id), "bravo"]
    )
    cli.main()
    monkeypatch.setattr(
        sys, "argv", ["organizations", "revoke", str(company_id), "bravo"]
    )
    cli.main()

    def edit(_: int) -> int:
        with Session(engine) as db:
            set_actor(db, user_id)
            try:
                edit_company(db, user_id, company_id, "Updated CLI", True, 1, uuid4())
                return 200
            except HTTPException as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(edit, range(2))) == [200, 409]
    with Session(engine) as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(CompanyEvent)
                .where(CompanyEvent.kind == "company_updated")
            )
            == 1
        )
        grant = db.scalar(
            select(CompanyGrant)
            .join(User)
            .where(User.username == "bravo", CompanyGrant.company_id == company_id)
        )
        assert grant is not None and not grant.is_active


def test_postgres_rls_default_deny_and_pool_context(company_client: TestClient) -> None:
    engine = create_database_engine()
    role = "registry_test_" + uuid4().hex
    try:
        with engine.begin() as connection:
            alice = connection.scalar(select(User.id).where(User.username == "alice"))
            bravo = connection.scalar(select(User.id).where(User.username == "bravo"))
            connection.exec_driver_sql(f'CREATE ROLE "{role}" NOLOGIN')
            schema = connection.scalar(text("SELECT current_schema()"))
            connection.exec_driver_sql(f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"')
            connection.exec_driver_sql(
                f'GRANT SELECT ON org_companies, org_company_grants TO "{role}"'
            )
            connection.exec_driver_sql(
                f'GRANT UPDATE (legal_name) ON org_companies TO "{role}"'
            )
        for actor, expected in (
            (None, []),
            (alice, ["ALPHA"]),
            (bravo, ["BRAVO"]),
            (None, []),
        ):
            with engine.begin() as connection:
                connection.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
                if actor:
                    connection.execute(
                        text("SELECT set_config('erp.user_id', :id, true)"),
                        {"id": str(actor)},
                    )
                assert list(connection.scalars(select(Company.code))) == expected
        with engine.begin() as connection:
            connection.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            connection.execute(
                text("SELECT set_config('erp.user_id', :id, true)"), {"id": str(alice)}
            )
            assert (
                connection.execute(
                    text(
                        "UPDATE org_companies SET legal_name='Denied' "
                        "WHERE code='BRAVO'"
                    )
                ).rowcount
                == 0
            )
            assert (
                connection.execute(
                    text(
                        "UPDATE org_companies SET legal_name='Alpha Updated' "
                        "WHERE code='ALPHA'"
                    )
                ).rowcount
                == 1
            )
        with engine.begin() as connection:
            connection.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            with pytest.raises(DBAPIError):
                connection.execute(text("UPDATE org_company_grants SET is_active=true"))
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP OWNED BY "{role}"')
            connection.exec_driver_sql(f'DROP ROLE "{role}"')
        engine.dispose()
