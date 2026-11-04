import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import case, select, text, update
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.identity.models import AuthEvent, AuthSession, LoginLimit, PasswordReset, User
from app.identity.security import (
    SESSION_SECONDS,
    hash_password,
    hasher,
    normalize_username,
    token_hash,
    verify_password,
)


@dataclass(frozen=True)
class Principal:
    user: User
    session: AuthSession
    token: str


def audit(
    db: Session,
    kind: str,
    user_id: UUID | None,
    request_id: UUID,
    source: str = "api",
    *,
    actor_id: UUID | None = None,
    change_id: UUID | None = None,
) -> None:
    db.add(
        AuthEvent(
            kind=kind,
            user_id=user_id,
            request_id=request_id,
            source=source,
            actor_id=actor_id,
            change_id=change_id,
        )
    )


def account_lock(db: Session) -> None:
    # Fixed transaction lock serializes bootstrap, administration and recovery.
    connection = db.connection()
    if connection.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(810101)"))
    # SQLite's connection begin hook already acquired BEGIN IMMEDIATE.


def consume_limit(
    db: Session,
    username: str,
    request_id: UUID,
    *,
    bucket: Literal["name", "recovery"] = "name",
) -> None:
    now = datetime.now(UTC)
    retry_after = 0
    for key, maximum, seconds in (
        ("global", 60, 60),
        (bucket + ":" + token_hash(username), 5, 900),
    ):
        expired = LoginLimit.window_started <= now - timedelta(seconds=seconds)
        insert = (
            sqlite_insert if db.get_bind().dialect.name == "sqlite" else postgres_insert
        )
        statement = insert(LoginLimit).values(key=key, attempts=1, window_started=now)
        count = db.scalar(
            statement.on_conflict_do_update(
                index_elements=[LoginLimit.key],
                set_={
                    "attempts": case((expired, 1), else_=LoginLimit.attempts + 1),
                    "window_started": case(
                        (expired, now), else_=LoginLimit.window_started
                    ),
                },
            ).returning(LoginLimit.attempts)
        )
        if count is None or count > maximum:
            retry_after = seconds
            break
    db.commit()
    if retry_after:
        audit(db, "login_throttled", None, request_id)
        db.commit()
        raise HTTPException(429, headers={"Retry-After": str(retry_after)})


def authenticate(db: Session, token: str | None) -> Principal:
    if token is None or len(token) != 43:
        raise HTTPException(401)
    row = db.execute(
        select(AuthSession, User)
        .join(User, AuthSession.user_id == User.id)
        .where(
            AuthSession.token_hash == token_hash(token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
            User.is_active.is_(True),
        )
        .execution_options(populate_existing=True)
    ).one_or_none()
    if row is None:
        raise HTTPException(401)
    return Principal(row[1], row[0], token)


def login(
    db: Session, username: str, password: str, old_token: str | None, request_id: UUID
) -> Principal:
    consume_limit(db, username, request_id)
    user = db.scalar(select(User).where(User.username == username).with_for_update())
    valid = verify_password(password, user.password_hash if user else None)
    if not valid or user is None or not user.is_active:
        audit(db, "login_failed", user.id if user else None, request_id)
        db.commit()
        raise HTTPException(401)
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    now = datetime.now(UTC)
    if old_token:
        db.execute(
            update(AuthSession)
            .where(
                AuthSession.token_hash == token_hash(old_token),
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
    token = secrets.token_urlsafe(32)
    session = AuthSession(
        token_hash=token_hash(token),
        user_id=user.id,
        expires_at=now + timedelta(seconds=SESSION_SECONDS),
    )
    db.add(session)
    audit(db, "login_succeeded", user.id, request_id)
    db.commit()
    return Principal(user, session, token)


def logout(db: Session, principal: Principal, request_id: UUID) -> None:
    db.execute(
        update(AuthSession)
        .where(
            AuthSession.token_hash == principal.session.token_hash,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    audit(db, "logout", principal.user.id, request_id)
    db.commit()


def change_password(
    db: Session, principal: Principal, current: str, new: str, request_id: UUID
) -> None:
    username = principal.user.username
    token = principal.token
    consume_limit(db, username, request_id)
    account_lock(db)
    user = db.scalar(
        select(User)
        .where(User.username == username)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    principal = authenticate(db, token)
    if user is None or not verify_password(current, user.password_hash):
        audit(db, "password_change_failed", principal.user.id, request_id)
        db.commit()
        raise HTTPException(401)
    user.password_hash = hash_password(new)
    revoke_sessions(db, user.id)
    audit(db, "password_changed", user.id, request_id)
    db.commit()


def revoke_sessions(db: Session, user_id: UUID) -> None:
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.execute(
        update(PasswordReset)
        .where(PasswordReset.user_id == user_id, PasswordReset.used_at.is_(None))
        .values(used_at=datetime.now(UTC))
    )


def provision_user(db: Session, username: str, password: str) -> User:
    user = User(
        username=normalize_username(username), password_hash=hash_password(password)
    )
    db.add(user)
    db.flush()
    audit(db, "user_created", user.id, uuid4(), "operator_cli")
    db.commit()
    return user


def manage_user(db: Session, username: str, password: str | None = None) -> None:
    account_lock(db)
    user = db.scalar(
        select(User)
        .where(User.username == normalize_username(username))
        .with_for_update()
    )
    if user is None:
        raise ValueError("User not found")
    if password is None:
        user.is_active = False
        kind = "user_deactivated"
    else:
        user.password_hash = hash_password(password)
        kind = "password_reset"
    revoke_sessions(db, user.id)
    audit(db, kind, user.id, uuid4(), "operator_cli")
    db.commit()
