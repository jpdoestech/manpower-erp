import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import Select, select, text, update
from sqlalchemy.orm import Session

from app.identity.models import User
from app.identity.security import normalize_username
from app.organizations.models import Company, CompanyEvent, CompanyGrant


def validated_company(code: str, legal_name: str) -> tuple[str, str]:
    code, legal_name = code.strip().upper(), legal_name.strip()
    if (
        not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,31}", code)
        or not 1 <= len(legal_name) <= 200
    ):
        raise ValueError("Invalid company code or legal name")
    if any(ord(char) < 32 for char in legal_name):
        raise ValueError("Invalid company code or legal name")
    return code, legal_name


def set_actor(db: Session, user_id: UUID) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT set_config('erp.user_id', :actor, true)"),
            {"actor": str(user_id)},
        )


def authorized_company_ids(user_id: UUID) -> Select[UUID]:
    return select(CompanyGrant.company_id).where(
        CompanyGrant.user_id == user_id, CompanyGrant.is_active.is_(True)
    )


def company_for_user(db: Session, user_id: UUID, company_id: UUID) -> Company:
    company = db.scalar(
        select(Company).where(
            Company.id == company_id, Company.id.in_(authorized_company_ids(user_id))
        )
    )
    if company is None:
        raise HTTPException(404)
    return company


def edit_company(
    db: Session,
    user_id: UUID,
    company_id: UUID,
    name: str,
    active: bool,
    version: int,
    request_id: UUID,
) -> Company:
    before = company_for_user(db, user_id, company_id)
    _, name = validated_company(before.code, name)
    before_name, before_active = before.legal_name, before.is_active
    changed = db.scalar(
        update(Company)
        .where(
            Company.id == company_id,
            Company.version == version,
            Company.id.in_(authorized_company_ids(user_id)),
        )
        .values(
            legal_name=name,
            is_active=active,
            version=version + 1,
            updated_at=datetime.now(UTC),
        )
        .returning(Company.id)
    )
    if changed is None:
        raise HTTPException(409)
    db.add(
        CompanyEvent(
            company_id=company_id,
            actor_id=user_id,
            kind="company_updated",
            before_name=before_name,
            after_name=name,
            before_active=before_active,
            after_active=active,
            request_id=request_id,
        )
    )
    db.commit()
    set_actor(db, user_id)
    return company_for_user(db, user_id, company_id)


def provision_company(
    db: Session, code: str, legal_name: str, username: str
) -> Company:
    code, legal_name = validated_company(code, legal_name)
    user = db.scalar(
        select(User).where(
            User.username == normalize_username(username), User.is_active.is_(True)
        )
    )
    if user is None:
        raise ValueError("Active user required")
    company = Company(code=code, legal_name=legal_name)
    db.add(company)
    db.flush()
    db.add(CompanyGrant(company_id=company.id, user_id=user.id))
    db.add(
        CompanyEvent(
            company_id=company.id,
            subject_id=user.id,
            kind="operator_company_created",
            after_name=legal_name,
            after_active=True,
            request_id=uuid4(),
        )
    )
    db.commit()
    return company


def set_grant(db: Session, company_id: UUID, username: str, active: bool) -> None:
    user = db.scalar(
        select(User).where(
            User.username == normalize_username(username), User.is_active.is_(True)
        )
    )
    if user is None or db.get(Company, company_id) is None:
        raise ValueError("Company and active user required")
    grant = db.get(CompanyGrant, (company_id, user.id))
    if grant is None:
        grant = CompanyGrant(company_id=company_id, user_id=user.id)
        db.add(grant)
    grant.is_active = active
    db.add(
        CompanyEvent(
            company_id=company_id,
            subject_id=user.id,
            kind="operator_grant" if active else "operator_revoke",
            request_id=uuid4(),
        )
    )
    db.commit()
