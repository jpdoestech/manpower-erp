"""Technical identity administration only; no organizational grants."""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.identity.models import AccountChange, LoginLimit, PasswordReset, User
from app.identity.security import (
    hash_password,
    normalize_username,
    token_hash,
    verify_password,
)
from app.identity.service import (
    Principal,
    account_lock,
    audit,
    authenticate,
    consume_limit,
    revoke_sessions,
)


def bootstrap(
    db: Session, first: str, first_password: str, second: str, second_password: str
) -> None:
    names = [normalize_username(first), normalize_username(second)]
    if names[0] == names[1]:
        raise ValueError("Distinct administrators required")
    hashes = [hash_password(first_password), hash_password(second_password)]
    account_lock(db)
    if db.scalar(select(User.id).where(User.is_super_admin.is_(True)).limit(1)):
        raise ValueError("Bootstrap already completed")
    for name, encoded in zip(names, hashes, strict=True):
        user = User(username=name, password_hash=encoded, is_super_admin=True)
        db.add(user)
        db.flush()
        audit(
            db, "admin_bootstrapped", user.id, uuid4(), "operator_cli", actor_id=user.id
        )
    db.commit()


def require_admin(db: Session, current: Principal) -> Principal:
    current = authenticate(db, current.token)
    if not current.user.is_super_admin:
        raise HTTPException(403)
    return current


def reauthenticate(
    db: Session, current: Principal, password: str, request_id: UUID
) -> Principal:
    require_admin(db, current)
    name, token = current.user.username, current.token
    consume_limit(db, name, request_id)
    account_lock(db)
    current = require_admin(db, authenticate(db, token))
    if not verify_password(password, current.user.password_hash):
        audit(
            db,
            "admin_reauth_failed",
            current.user.id,
            request_id,
            actor_id=current.user.id,
        )
        db.commit()
        raise HTTPException(401)
    return current


def request_change(
    db: Session,
    current: Principal,
    username: str,
    action: str,
    password: str,
    request_id: UUID,
) -> AccountChange:
    current = reauthenticate(db, current, password, request_id)
    user = db.scalar(select(User).where(User.username == username).with_for_update())
    if action == "register":
        if user is not None:
            raise HTTPException(409)
        user = User(
            username=username,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            is_active=False,
        )
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409) from None
        action = "activate"
        audit(db, "user_registered", user.id, request_id, actor_id=current.user.id)
    if user is None:
        raise HTTPException(404)
    change = AccountChange(
        user_id=user.id,
        requested_by=current.user.id,
        action=action,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(change)
    db.flush()
    audit(
        db,
        "account_change_requested",
        user.id,
        request_id,
        actor_id=current.user.id,
        change_id=change.id,
    )
    db.commit()
    return change


def approve_change(
    db: Session,
    current: Principal,
    change_id: UUID,
    password: str,
    request_id: UUID,
) -> str | None:
    current = reauthenticate(db, current, password, request_id)
    change = db.get(
        AccountChange, change_id, populate_existing=True, with_for_update=True
    )
    if change is None:
        raise HTTPException(404)
    if current.user.id in (change.requested_by, change.user_id):
        audit(
            db,
            "account_approval_denied",
            change.user_id,
            request_id,
            actor_id=current.user.id,
            change_id=change.id,
        )
        db.commit()
        raise HTTPException(403)
    requester = db.get(User, change.requested_by, populate_existing=True)
    if requester is None or not requester.is_active or not requester.is_super_admin:
        raise HTTPException(403)
    now = datetime.now(UTC)
    if change.approved_at is not None or change.expires_at <= now:
        raise HTTPException(409)
    user = db.get(User, change.user_id, populate_existing=True, with_for_update=True)
    assert user is not None
    token = None
    if change.action == "activate":
        if user.is_active:
            raise HTTPException(409)
        user.is_active = True
        # Reactivation requires recovery; disabled credentials may be compromised.
        user.password_hash = hash_password(secrets.token_urlsafe(32))
    elif change.action == "deactivate":
        if user.is_super_admin and user.is_active:
            count = db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_super_admin.is_(True), User.is_active.is_(True))
            )
            if count is None or count <= 2:
                raise HTTPException(409)
        user.is_active = False
    elif not user.is_active:
        raise HTTPException(409)
    if change.action == "unlock":
        db.execute(
            delete(LoginLimit).where(
                LoginLimit.key == "name:" + token_hash(user.username)
            )
        )
    else:
        revoke_sessions(db, user.id)
        if change.action in ("activate", "reset_password"):
            token = secrets.token_urlsafe(32)
            db.add(
                PasswordReset(
                    token_hash=token_hash(token),
                    user_id=user.id,
                    expires_at=now + timedelta(minutes=15),
                )
            )
    change.approved_by, change.approved_at = current.user.id, now
    audit(
        db,
        "account_change_approved",
        user.id,
        request_id,
        actor_id=current.user.id,
        change_id=change.id,
    )
    db.commit()
    return token


def reset_password(db: Session, token: str, password: str, request_id: UUID) -> None:
    # Tokens never become name-throttle keys, so known/unknown recovery is uniform.
    consume_limit(db, "", request_id, bucket="recovery")
    account_lock(db)
    reset = db.get(
        PasswordReset, token_hash(token), populate_existing=True, with_for_update=True
    )
    now = datetime.now(UTC)
    user = (
        db.get(User, reset.user_id, populate_existing=True, with_for_update=True)
        if reset
        else None
    )
    if (
        reset is None
        or reset.used_at is not None
        or reset.expires_at <= now
        or user is None
        or not user.is_active
    ):
        audit(db, "password_recovery_failed", None, request_id)
        db.commit()
        raise HTTPException(400)
    user.password_hash = hash_password(password)
    revoke_sessions(db, user.id)
    audit(db, "password_recovered", user.id, request_id, actor_id=user.id)
    db.commit()
