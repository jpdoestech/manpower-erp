from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

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
