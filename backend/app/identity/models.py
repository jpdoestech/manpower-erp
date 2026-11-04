from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "auth_users"
    __table_args__ = (
        CheckConstraint(
            "username ~ '^[a-z][a-z0-9_.-]{2,63}$'", name="ck_auth_username"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    is_super_admin: Mapped[bool] = mapped_column(Boolean, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LoginLimit(Base):
    __tablename__ = "auth_login_limits"
    __table_args__ = (CheckConstraint("attempts > 0", name="ck_auth_attempts"),)

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    window_started: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer)


class AuthEvent(Base):
    __tablename__ = "auth_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("auth_users.id"))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("auth_users.id"))
    change_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("auth_account_changes.id")
    )
    kind: Mapped[str] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(16))
    request_id: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AccountChange(Base):
    __tablename__ = "auth_account_changes"
    __table_args__ = (
        CheckConstraint(
            "action IN ('activate', 'deactivate', 'reset_password', 'unlock')",
            name="ck_auth_change_action",
        ),
        CheckConstraint(
            "approved_by IS NULL OR "
            "(approved_by <> requested_by AND approved_by <> user_id)",
            name="ck_auth_change_separation",
        ),
        CheckConstraint(
            "(approved_by IS NULL) = (approved_at IS NULL)",
            name="ck_auth_change_approval",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id"))
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id"))
    action: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("auth_users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordReset(Base):
    __tablename__ = "auth_password_resets"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
