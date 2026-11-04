import hmac
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    Security,
)
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.identity import administration, service
from app.identity.models import AccountChange, User
from app.identity.security import (
    COOKIE,
    SESSION_SECONDS,
    AuthSettings,
    csrf_token,
    normalize_username,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
Db = Annotated[Session, Depends(get_session)]
cookie = APIKeyCookie(name=COOKIE, auto_error=False)


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=64)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        return normalize_username(value)


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=15, max_length=128)


class SessionView(BaseModel):
    id: UUID
    username: str
    csrf_token: str


def principal(
    db: Db, token: Annotated[str | None, Security(cookie)]
) -> service.Principal:
    return service.authenticate(db, token)


Current = Annotated[service.Principal, Depends(principal)]


def check_origin(request: Request) -> None:
    settings: AuthSettings = request.app.state.auth_settings
    origins = request.headers.getlist("origin")
    if origins and origins != [settings.origin]:
        raise HTTPException(403)


def check_csrf(request: Request, current: service.Principal) -> None:
    values = request.headers.getlist("x-csrf-token")
    if len(values) != 1 or not hmac.compare_digest(
        values[0].encode(), csrf_token(current.token).encode()
    ):
        raise HTTPException(403)


def view(current: service.Principal) -> SessionView:
    return SessionView(
        id=current.user.id,
        username=current.user.username,
        csrf_token=csrf_token(current.token),
    )


@router.post("/login", response_model=SessionView, dependencies=[Depends(check_origin)])
def login(
    body: Credentials, request: Request, response: Response, db: Db
) -> SessionView:
    current = service.login(
        db,
        body.username,
        body.password.get_secret_value(),
        request.cookies.get(COOKIE),
        UUID(request.state.request_id),
    )
    settings: AuthSettings = request.app.state.auth_settings
    response.set_cookie(
        COOKIE,
        current.token,
        max_age=SESSION_SECONDS,
        secure=settings.cookie_secure,
        httponly=True,
        samesite="strict",
        path="/api",
    )
    response.headers["Cache-Control"] = "no-store"
    return view(current)


@router.get("/me", response_model=SessionView)
def me(current: Current, response: Response) -> SessionView:
    response.headers["Cache-Control"] = "no-store"
    return view(current)


def clear_cookie(request: Request, response: Response) -> None:
    settings: AuthSettings = request.app.state.auth_settings
    response.delete_cookie(
        COOKIE,
        path="/api",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"


@router.post("/logout", status_code=204, dependencies=[Depends(check_origin)])
def logout(current: Current, request: Request, response: Response, db: Db) -> None:
    check_csrf(request, current)
    service.logout(db, current, UUID(request.state.request_id))
    clear_cookie(request, response)


@router.post("/password", status_code=204, dependencies=[Depends(check_origin)])
def password(
    body: PasswordChange, current: Current, request: Request, response: Response, db: Db
) -> None:
    check_csrf(request, current)
    service.change_password(
        db,
        current,
        body.current_password.get_secret_value(),
        body.new_password.get_secret_value(),
        UUID(request.state.request_id),
    )
    clear_cookie(request, response)


class ResetPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: SecretStr = Field(min_length=43, max_length=43)
    new_password: SecretStr = Field(min_length=15, max_length=128)


class AdminProof(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: SecretStr = Field(min_length=1, max_length=128)


class ChangeRequest(AdminProof):
    username: str = Field(min_length=3, max_length=64)
    action: Literal["register", "activate", "deactivate", "reset_password", "unlock"]

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        return normalize_username(value)


class ChangeView(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    requested_by: UUID
    action: str
    expires_at: datetime


def change_view(change: AccountChange, username: str) -> ChangeView:
    return ChangeView(
        id=change.id,
        user_id=change.user_id,
        username=username,
        requested_by=change.requested_by,
        action=change.action,
        expires_at=change.expires_at,
    )


class ApprovalView(BaseModel):
    reset_token: str | None


@router.post("/reset-password", status_code=204, dependencies=[Depends(check_origin)])
def reset_password(
    body: ResetPassword, request: Request, response: Response, db: Db
) -> None:
    administration.reset_password(
        db,
        body.token.get_secret_value(),
        body.new_password.get_secret_value(),
        UUID(request.state.request_id),
    )
    clear_cookie(request, response)


@router.get("/admin/requests", response_model=list[ChangeView])
def pending_changes(
    current: Current,
    response: Response,
    db: Db,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> list[ChangeView]:
    administration.require_admin(db, current)
    response.headers["Cache-Control"] = "no-store"
    return [
        change_view(change, username)
        for change, username in db.execute(
            select(AccountChange, User.username)
            .join(User, User.id == AccountChange.user_id)
            .where(
                AccountChange.approved_at.is_(None),
                AccountChange.expires_at > datetime.now(UTC),
            )
            .order_by(AccountChange.created_at, AccountChange.id)
            .offset(offset)
            .limit(50)
        )
    ]


@router.post(
    "/admin/requests",
    response_model=ChangeView,
    status_code=201,
    dependencies=[Depends(check_origin)],
)
def request_change(
    body: ChangeRequest, current: Current, request: Request, response: Response, db: Db
) -> ChangeView:
    check_csrf(request, current)
    response.headers["Cache-Control"] = "no-store"
    change = administration.request_change(
        db,
        current,
        body.username,
        body.action,
        body.current_password.get_secret_value(),
        UUID(request.state.request_id),
    )
    return change_view(change, body.username)


@router.post(
    "/admin/requests/{change_id}/approve",
    response_model=ApprovalView,
    dependencies=[Depends(check_origin)],
)
def approve_change(
    change_id: UUID,
    body: AdminProof,
    current: Current,
    request: Request,
    response: Response,
    db: Db,
) -> ApprovalView:
    check_csrf(request, current)
    token = administration.approve_change(
        db,
        current,
        change_id,
        body.current_password.get_secret_value(),
        UUID(request.state.request_id),
    )
    response.headers["Cache-Control"] = "no-store"
    return ApprovalView(reset_token=token)
