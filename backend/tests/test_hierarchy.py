import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import cast
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from test_companies import company_client, signin

from alembic import command
from app.database import create_database_engine
from app.identity.models import User
from app.organizations import cli, hierarchy
from app.organizations.models import (
    Branch,
    Company,
    CompanyGrant,
    HeadOffice,
    HierarchyEvent,
)
from app.organizations.service import set_actor, set_hierarchy_grant

pytestmark = pytest.mark.integration
__all__ = ["company_client"]


def context(client: TestClient) -> tuple[dict[str, str], str]:
    headers = signin(client)
    company_id: str = client.get("/api/companies").json()[0]["id"]
    with Session(cast(FastAPI, client.app).state.engine) as db:
        set_hierarchy_grant(db, UUID(company_id), "alice", True)
    return headers, company_id


def office(
    client: TestClient,
    headers: dict[str, str],
    company: str,
    code: str = "HO",
    **values: object,
) -> dict[str, object]:
    response = client.post(
        f"/api/companies/{company}/head-offices",
        headers=headers,
        json={
            "code": code,
            "name": "Head Office",
            "valid_from": "2020-01-01",
            **values,
        },
    )
    assert response.status_code == 201, response.text
    result: dict[str, object] = response.json()
    return result


def test_hierarchy_authorization_and_operator_capability(
    company_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = company_client
    headers = signin(client)
    company_id = client.get("/api/companies").json()[0]["id"]
    path = f"/api/companies/{company_id}/head-offices"
    assert client.get(path).status_code == 404
    assert client.get("/api/companies?hierarchy=true").json() == []
    for action in ("grant-hierarchy", "revoke-hierarchy", "grant-hierarchy"):
        monkeypatch.setattr(sys, "argv", ["organizations", action, company_id, "alice"])
        cli.main()
    assert client.get(path).json() == []
    assert client.get("/api/companies?hierarchy=true").json()[0]["id"] == company_id
    item = office(client, headers, company_id)
    assert client.get(path).headers["cache-control"] == "no-store"
    with Session(cast(FastAPI, client.app).state.engine) as db:
        other = db.scalar(select(Company.id).where(Company.code == "BRAVO"))
    assert client.get(f"/api/companies/{other}/head-offices").status_code == 404
    assert (
        client.get(f"/api/companies/{other}/head-offices/{item['id']}").status_code
        == 404
    )
    assert client.get(f"/api/companies/{other}/branches").status_code == 404
    assert (
        client.post(
            path, json={"code": "H2", "name": "Other", "valid_from": "2020-01-01"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            path,
            headers={**headers, "Origin": "https://evil.example"},
            json={"code": "H2", "name": "Other", "valid_from": "2020-01-01"},
        ).status_code
        == 403
    )
    with Session(cast(FastAPI, client.app).state.engine) as db:
        set_hierarchy_grant(db, UUID(company_id), "alice", False)
    assert client.get(path).status_code == 404
    signin(client, "ungranted")
    assert (
        client.get(
            path, headers={"X-Role": "admin", "X-Company-ID": company_id}
        ).status_code
        == 404
    )


def test_hierarchy_dates_inactive_parents_and_immutable_fields(
    company_client: TestClient,
) -> None:
    client = company_client
    headers, company = context(client)
    parent = office(client, headers, company, valid_to="2099-12-31")
    url = f"/api/companies/{company}/branches"
    body = {
        "code": "BR",
        "name": "Branch",
        "valid_from": "2020-01-01",
        "valid_to": "2099-12-31",
        "head_office_id": parent["id"],
    }
    assert (
        client.post(
            url, headers=headers, json={**body, "valid_from": "2019-12-31"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            url, headers=headers, json={**body, "valid_to": "2019-01-01"}
        ).status_code
        == 422
    )
    assert (
        client.post(url, headers=headers, json={**body, "valid_from": 123}).status_code
        == 422
    )
    assert (
        client.post(url, headers=headers, json={**body, "valid_to": None}).status_code
        == 422
    )
    assert (
        client.post(
            url, headers=headers, json={**body, "head_office_id": str(uuid4())}
        ).status_code
        == 404
    )
    created = client.post(url, headers=headers, json=body)
    assert created.status_code == 201
    branch = created.json()
    assert client.post(url, headers=headers, json=body).status_code == 409
    assert len(client.get(url + "?q=Branch").json()) == 1
    assert client.get(url + "?q=%").json() == []
    assert client.get(url + "?active=false").json() == []
    assert client.get(url + "?offset=1").json() == []
    assert client.get(url + f"?head_office_id={uuid4()}").json() == []
    parent_url = f"/api/companies/{company}/head-offices/{parent['id']}"
    edit = {
        "name": "Closed Office",
        "is_active": False,
        "valid_to": "2099-12-31",
        "version": 1,
    }
    assert client.patch(parent_url, headers=headers, json=edit).status_code == 409
    assert (
        client.patch(
            parent_url,
            headers=headers,
            json={**edit, "is_active": True, "valid_to": "2098-12-31"},
        ).status_code
        == 409
    )
    edit_branch = {
        "name": "Closed Branch",
        "is_active": False,
        "valid_to": "2099-12-31",
        "version": 1,
    }
    branch_url = url + f"/{branch['id']}"
    assert (
        client.patch(
            branch_url,
            headers=headers,
            json={"name": "Missing end date", "is_active": False, "version": 1},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            branch_url,
            headers=headers,
            json={**edit_branch, "head_office_id": str(uuid4())},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            branch_url,
            headers=headers,
            json={**edit_branch, "valid_from": "2021-01-01"},
        ).status_code
        == 422
    )
    assert (
        client.patch(branch_url, headers=headers, json=edit_branch).status_code == 200
    )
    assert (
        client.patch(branch_url, headers=headers, json=edit_branch).status_code == 409
    )
    assert client.patch(parent_url, headers=headers, json=edit).status_code == 200
    assert (
        client.post(url, headers=headers, json={**body, "code": "NEW"}).status_code
        == 409
    )
    assert (
        client.patch(
            branch_url,
            headers=headers,
            json={**edit_branch, "version": 2, "is_active": True},
        ).status_code
        == 409
    )
    assert client.delete(branch_url, headers=headers).status_code == 405
    office(client, headers, company, "PAST", valid_to="2021-01-01", is_active=False)
    assert (
        client.post(
            f"/api/companies/{company}/head-offices",
            headers=headers,
            json={
                "code": "BAD",
                "name": "Old",
                "valid_from": "2020-01-01",
                "valid_to": "2021-01-01",
            },
        ).status_code
        == 422
    )


def test_hierarchy_fk_audit_and_migration_preservation(
    company_client: TestClient,
) -> None:
    client = company_client
    headers, company = context(client)
    parent = office(client, headers, company)
    engine = cast(FastAPI, client.app).state.engine
    with Session(engine) as db:
        other_company = db.scalar(select(Company.id).where(Company.code == "BRAVO"))
        user_id = db.scalar(select(User.id).where(User.username == "alice"))
        other_parent = HeadOffice(
            company_id=other_company,
            code="HO",
            name="Other Office",
            valid_from=date(2020, 1, 1),
            created_by=user_id,
        )
        db.add(other_parent)
        db.commit()
        other_parent_id = str(other_parent.id)
        with pytest.raises(IntegrityError):
            db.add(
                Branch(
                    company_id=other_company,
                    head_office_id=UUID(str(parent["id"])),
                    code="BAD",
                    name="Crossed",
                    valid_from=date(2020, 1, 1),
                    created_by=user_id,
                )
            )
            db.commit()
        db.rollback()
        with pytest.raises(DBAPIError):
            db.execute(text("DELETE FROM org_hierarchy_events"))
        db.rollback()
        with pytest.raises(IntegrityError):
            db.add(
                HeadOffice(
                    company_id=UUID(company),
                    code="INVALID",
                    name="Invalid",
                    valid_from=date(2020, 1, 2),
                    valid_to=date(2020, 1, 1),
                    created_by=user_id,
                )
            )
            db.commit()
        db.rollback()
        with pytest.raises(IntegrityError):
            db.execute(text("DELETE FROM org_head_offices"))
        db.rollback()
    assert (
        client.post(
            f"/api/companies/{company}/branches",
            headers=headers,
            json={
                "code": "CROSSED",
                "name": "Denied",
                "head_office_id": other_parent_id,
                "valid_from": "2020-01-01",
            },
        ).status_code
        == 404
    )
    with pytest.raises(RuntimeError, match="preserve organization history"):
        command.downgrade(Config("alembic.ini"), "0005_company_registry")
    command.check(Config("alembic.ini"))
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(HeadOffice)) == 2
        event = db.scalar(select(HierarchyEvent))
        assert (
            event and event.after_state["code"] == "HO" and event.before_state is None
        )


def test_registry_upgrade_preserves_data_without_automatic_capability(
    company_client: TestClient,
) -> None:
    engine = cast(FastAPI, company_client.app).state.engine
    with Session(engine) as db:
        before = [
            (row.id, row.code)
            for row in db.scalars(select(Company).order_by(Company.code))
        ]
    command.downgrade(Config("alembic.ini"), "0005_company_registry")
    command.upgrade(Config("alembic.ini"), "head")
    command.upgrade(Config("alembic.ini"), "head")
    command.check(Config("alembic.ini"))
    with Session(engine) as db:
        assert [
            (row.id, row.code)
            for row in db.scalars(select(Company).order_by(Company.code))
        ] == before
        assert (
            db.scalar(
                select(func.count())
                .select_from(CompanyGrant)
                .where(CompanyGrant.manage_hierarchy.is_(True))
            )
            == 0
        )


def test_hierarchy_parent_close_race_and_inactive_company(
    company_client: TestClient,
) -> None:
    headers, company = context(company_client)
    parent = office(company_client, headers, company)
    engine = cast(FastAPI, company_client.app).state.engine
    with Session(engine) as db:
        user_id = db.scalar(select(User.id).where(User.username == "alice"))
        assert user_id is not None

    def operation(close: bool) -> int:
        with Session(engine) as db:
            set_actor(db, user_id)
            try:
                if close:
                    hierarchy.edit_unit(
                        db,
                        user_id,
                        UUID(company),
                        UUID(str(parent["id"])),
                        "head_office",
                        "Closed",
                        None,
                        False,
                        1,
                        uuid4(),
                    )
                else:
                    hierarchy.create_unit(
                        db,
                        user_id,
                        UUID(company),
                        "branch",
                        "RACE",
                        "Race",
                        date(2020, 1, 1),
                        None,
                        True,
                        UUID(str(parent["id"])),
                        uuid4(),
                    )
                return 200
            except HTTPException as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(operation, (True, False))) == [200, 409]
    with Session(engine) as db:
        record = db.get(Company, UUID(company))
        assert record
        record.is_active = False
        db.commit()
    response = company_client.post(
        f"/api/companies/{company}/head-offices",
        headers=headers,
        json={"code": "NEW", "name": "Inactive Company", "valid_from": "2020-01-01"},
    )
    assert response.status_code == 409


def test_stale_session_cannot_overwrite_a_committed_edit(
    company_client: TestClient,
) -> None:
    headers, company = context(company_client)
    parent = office(company_client, headers, company)
    engine = cast(FastAPI, company_client.app).state.engine
    with Session(engine) as stale:
        user_id = stale.scalar(select(User.id).where(User.username == "alice"))
        assert user_id is not None
        set_actor(stale, user_id)
        old = hierarchy.get_unit(
            stale, UUID(company), UUID(str(parent["id"])), "head_office"
        )
        assert old.version == 1
        with Session(engine) as fresh:
            set_actor(fresh, user_id)
            hierarchy.edit_unit(
                fresh,
                user_id,
                UUID(company),
                old.id,
                "head_office",
                "Committed Name",
                None,
                True,
                1,
                uuid4(),
            )
        with pytest.raises(HTTPException) as conflict:
            hierarchy.edit_unit(
                stale,
                user_id,
                UUID(company),
                old.id,
                "head_office",
                "Stale Name",
                None,
                True,
                1,
                uuid4(),
            )
        assert conflict.value.status_code == 409
    with Session(engine) as db:
        saved = db.get(HeadOffice, UUID(str(parent["id"])))
        assert saved and saved.name == "Committed Name" and saved.version == 2


def test_hierarchy_non_owner_rls_and_context_reset(company_client: TestClient) -> None:
    headers, company = context(company_client)
    parent = office(company_client, headers, company)
    engine = create_database_engine()
    role = "hierarchy_test_" + uuid4().hex
    try:
        with engine.begin() as db:
            alice = db.scalar(select(User.id).where(User.username == "alice"))
            bravo = db.scalar(select(User.id).where(User.username == "bravo"))
            db.exec_driver_sql(f'CREATE ROLE "{role}" NOLOGIN')
            schema = db.scalar(text("SELECT current_schema()"))
            db.exec_driver_sql(f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"')
            db.exec_driver_sql(
                "GRANT SELECT ON org_head_offices, org_branches, org_company_grants "
                f'TO "{role}"'
            )
            db.exec_driver_sql(f'GRANT UPDATE(name) ON org_head_offices TO "{role}"')
        for actor, expected in ((None, []), (alice, ["HO"]), (bravo, []), (None, [])):
            with engine.begin() as db:
                db.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
                if actor:
                    db.execute(
                        text("SELECT set_config('erp.user_id', :id, true)"),
                        {"id": str(actor)},
                    )
                assert list(db.scalars(select(HeadOffice.code))) == expected
        with engine.begin() as db:
            db.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            db.execute(
                text("SELECT set_config('erp.user_id', :id, true)"), {"id": str(bravo)}
            )
            assert (
                db.execute(
                    text("UPDATE org_head_offices SET name='Denied' WHERE id=:id"),
                    {"id": UUID(str(parent["id"]))},
                ).rowcount
                == 0
            )
        with engine.begin() as db:
            db.execute(
                text(
                    "UPDATE org_company_grants SET manage_hierarchy=false "
                    "WHERE user_id=:id"
                ),
                {"id": alice},
            )
        with engine.begin() as db:
            db.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            db.execute(
                text("SELECT set_config('erp.user_id', :id, true)"), {"id": str(alice)}
            )
            assert list(db.scalars(select(HeadOffice.id))) == []
    finally:
        with engine.begin() as db:
            db.exec_driver_sql(f'DROP OWNED BY "{role}"')
            db.exec_driver_sql(f'DROP ROLE "{role}"')
        engine.dispose()
