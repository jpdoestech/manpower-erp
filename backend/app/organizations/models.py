from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.types import UTCDateTime


class Company(Base):
    __tablename__ = "org_companies"
    __table_args__ = (
        CheckConstraint("length(code) BETWEEN 2 AND 32", name="ck_company_code"),
        CheckConstraint("length(legal_name) BETWEEN 1 AND 200", name="ck_company_name"),
        CheckConstraint("version > 0", name="ck_company_version"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    legal_name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("auth_users.id"))


class CompanyGrant(Base):
    __tablename__ = "org_company_grants"

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("org_companies.id"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id"), primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    manage_hierarchy: Mapped[bool] = mapped_column(Boolean, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )


class CompanyEvent(Base):
    __tablename__ = "org_company_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("org_companies.id"), index=True)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("auth_users.id"))
    subject_id: Mapped[UUID | None] = mapped_column(ForeignKey("auth_users.id"))
    kind: Mapped[str] = mapped_column(String(32))
    before_name: Mapped[str | None] = mapped_column(String(200))
    after_name: Mapped[str | None] = mapped_column(String(200))
    before_active: Mapped[bool | None] = mapped_column(Boolean)
    after_active: Mapped[bool | None] = mapped_column(Boolean)
    request_id: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )


class HeadOffice(Base):
    __tablename__ = "org_head_offices"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_head_office_code"),
        UniqueConstraint("company_id", "id", name="uq_head_office_company_id"),
        CheckConstraint("length(code) BETWEEN 2 AND 32", name="ck_head_office_code"),
        CheckConstraint("length(name) BETWEEN 1 AND 200", name="ck_head_office_name"),
        CheckConstraint(
            "valid_to IS NULL OR valid_to >= valid_from", name="ck_head_office_dates"
        ),
        CheckConstraint("version > 0", name="ck_head_office_version"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("org_companies.id"))
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(200))
    valid_from: Mapped[date] = mapped_column(Date())
    valid_to: Mapped[date | None] = mapped_column(Date())
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id"))
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )


class Branch(Base):
    __tablename__ = "org_branches"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_branch_code"),
        UniqueConstraint("company_id", "id", name="uq_branch_company_id"),
        ForeignKeyConstraint(
            ["company_id", "head_office_id"],
            ["org_head_offices.company_id", "org_head_offices.id"],
        ),
        CheckConstraint("length(code) BETWEEN 2 AND 32", name="ck_branch_code"),
        CheckConstraint("length(name) BETWEEN 1 AND 200", name="ck_branch_name"),
        CheckConstraint(
            "valid_to IS NULL OR valid_to >= valid_from", name="ck_branch_dates"
        ),
        CheckConstraint("version > 0", name="ck_branch_version"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("org_companies.id"))
    head_office_id: Mapped[UUID] = mapped_column()
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(200))
    valid_from: Mapped[date] = mapped_column(Date())
    valid_to: Mapped[date | None] = mapped_column(Date())
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id"))
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )
    head_office: Mapped[HeadOffice] = relationship(viewonly=True, lazy="joined")

    @property
    def head_office_name(self) -> str:
        return self.head_office.name


class HierarchyEvent(Base):
    __tablename__ = "org_hierarchy_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "head_office_id"],
            ["org_head_offices.company_id", "org_head_offices.id"],
        ),
        ForeignKeyConstraint(
            ["company_id", "branch_id"], ["org_branches.company_id", "org_branches.id"]
        ),
        CheckConstraint(
            "(head_office_id IS NULL) <> (branch_id IS NULL)",
            name="ck_hierarchy_event_subject",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("org_companies.id"), index=True)
    head_office_id: Mapped[UUID | None] = mapped_column()
    branch_id: Mapped[UUID | None] = mapped_column()
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id"))
    kind: Mapped[str] = mapped_column(String(32))
    before_state: Mapped[dict[str, str | int | bool | None] | None] = mapped_column(
        JSON()
    )
    after_state: Mapped[dict[str, str | int | bool | None]] = mapped_column(JSON())
    request_id: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )
