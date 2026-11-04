import hmac
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy.orm import Session

from app.database import get_session
from app.identity import service
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
