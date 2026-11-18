from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.organizations.models import Branch, Company, HeadOffice, HierarchyEvent
from app.organizations.service import authorized_company_ids, set_actor

Unit = HeadOffice | Branch
Kind = Literal["head_office", "branch"]


def company_access(
    db: Session, user_id: UUID, company_id: UUID, *, lock: bool = False
) -> Company:
    query = select(Company).where(
        Company.id == company_id,
        Company.id.in_(authorized_company_ids(user_id, hierarchy=True)),
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    company = db.scalar(query)
    if company is None:
        raise HTTPException(404)
    return company


def get_unit(db: Session, company_id: UUID, unit_id: UUID, kind: Kind) -> Unit:
    model = HeadOffice if kind == "head_office" else Branch
    unit = db.scalar(
        select(model)
        .where(model.company_id == company_id, model.id == unit_id)
        .execution_options(populate_existing=True)
    )
    if unit is None:
        raise HTTPException(404)
    assert isinstance(unit, (HeadOffice, Branch))
    return unit


def list_units(
    db: Session,
    company_id: UUID,
    kind: Kind,
    query: str,
    active: bool | None,
    offset: int,
    head_office_id: UUID | None = None,
) -> list[Unit]:
    model = HeadOffice if kind == "head_office" else Branch
    statement = select(model).where(model.company_id == company_id)
    if query.strip():
        statement = statement.where(
            model.name.icontains(query.strip(), autoescape=True)
            | model.code.icontains(query.strip(), autoescape=True)
        )
    if active is not None:
        statement = statement.where(model.is_active == active)
    if kind == "branch" and head_office_id:
        statement = statement.where(Branch.head_office_id == head_office_id)
    return list(db.scalars(statement.order_by(model.code).offset(offset).limit(21)))


def valid_dates(start: date, end: date | None, active: bool) -> None:
    if end is not None and (
        end < start or (active and end < datetime.now(ZoneInfo("Asia/Manila")).date())
    ):
        raise HTTPException(422)


def parent_covers(
    parent: HeadOffice, start: date, end: date | None, active: bool
) -> None:
    if start < parent.valid_from or (
        parent.valid_to is not None and (end is None or end > parent.valid_to)
    ):
        raise HTTPException(422)
    if active and (
        not parent.is_active
        or (
            parent.valid_to is not None
            and parent.valid_to < datetime.now(ZoneInfo("Asia/Manila")).date()
        )
    ):
        raise HTTPException(409)


def state(unit: Unit) -> dict[str, str | int | bool | None]:
    return {
        "id": str(unit.id),
        "code": unit.code,
        "name": unit.name,
        "valid_from": unit.valid_from.isoformat(),
        "valid_to": unit.valid_to.isoformat() if unit.valid_to else None,
        "is_active": unit.is_active,
        "version": unit.version,
        "head_office_id": str(unit.head_office_id)
        if isinstance(unit, Branch)
        else None,
    }


def record(
    db: Session,
    unit: Unit,
    actor: UUID,
    request_id: UUID,
    before: dict[str, str | int | bool | None] | None,
) -> None:
    db.add(
        HierarchyEvent(
            company_id=unit.company_id,
            actor_id=actor,
            request_id=request_id,
            head_office_id=unit.id if isinstance(unit, HeadOffice) else None,
            branch_id=unit.id if isinstance(unit, Branch) else None,
            kind=("head_office" if isinstance(unit, HeadOffice) else "branch")
            + ("_created" if before is None else "_updated"),
            before_state=before,
            after_state=state(unit),
        )
    )


def create_unit(
    db: Session,
    user_id: UUID,
    company_id: UUID,
    kind: Kind,
    code: str,
    name: str,
    start: date,
    end: date | None,
    active: bool,
    parent_id: UUID | None,
    request_id: UUID,
) -> Unit:
    # One company lock serializes parent closure, child creation and registry changes.
    company = company_access(db, user_id, company_id, lock=True)
    if not company.is_active:
        raise HTTPException(409)
    valid_dates(start, end, active)
    if kind == "branch":
        if parent_id is None:
            raise HTTPException(422)
        parent = get_unit(db, company_id, parent_id, "head_office")
        assert isinstance(parent, HeadOffice)
        parent_covers(parent, start, end, True)
        unit: Unit = Branch(
            company_id=company_id,
            head_office_id=parent_id,
            code=code,
            name=name,
            valid_from=start,
            valid_to=end,
            is_active=active,
            created_by=user_id,
            version=1,
        )
    else:
        unit = HeadOffice(
            company_id=company_id,
            code=code,
            name=name,
            valid_from=start,
            valid_to=end,
            is_active=active,
            created_by=user_id,
            version=1,
        )
    db.add(unit)
    try:
        db.flush()
        record(db, unit, user_id, request_id, None)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409) from None
    set_actor(db, user_id)
    return get_unit(db, company_id, unit.id, kind)


def edit_unit(
    db: Session,
    user_id: UUID,
    company_id: UUID,
    unit_id: UUID,
    kind: Kind,
    name: str,
    end: date | None,
    active: bool,
    version: int,
    request_id: UUID,
) -> Unit:
    company = company_access(db, user_id, company_id, lock=True)
    unit = get_unit(db, company_id, unit_id, kind)
    if unit.version != version or (active and not company.is_active):
        raise HTTPException(409)
    valid_dates(unit.valid_from, end, active)
    if isinstance(unit, HeadOffice):
        children = list(
            db.scalars(
                select(Branch).where(
                    Branch.company_id == company_id, Branch.head_office_id == unit.id
                )
            )
        )
        if any(
            (not active and child.is_active)
            or (end is not None and (child.valid_to is None or child.valid_to > end))
            for child in children
        ):
            raise HTTPException(409)
    else:
        parent = get_unit(db, company_id, unit.head_office_id, "head_office")
        assert isinstance(parent, HeadOffice)
        parent_covers(parent, unit.valid_from, end, active)
    before = state(unit)
    unit.name, unit.is_active, unit.valid_to = name, active, end
    unit.version += 1
    unit.updated_at = datetime.now(UTC)
    record(db, unit, user_id, request_id, before)
    db.commit()
    set_actor(db, user_id)
    return get_unit(db, company_id, unit_id, kind)
