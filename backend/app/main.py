from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.database import create_database_engine, get_session
from app.identity.routes import router as identity_router
from app.identity.security import auth_settings
from app.observability import (
    RequestDiagnostics,
    configure_logging,
    error_response,
    logger,
)


class Bootstrap(BaseModel):
    name: Literal["Manpower ERP"] = "Manpower ERP"
    stage: Literal["bootstrap"] = "bootstrap"


class Health(BaseModel):
    status: Literal["live", "ready"]


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    app.state.auth_settings = auth_settings()
    engine = create_database_engine()
    app.state.engine = engine
    logger.info("application_started")
    try:
        yield
    finally:
        engine.dispose()
        logger.info("application_stopped")


def create_app() -> FastAPI:
    api = FastAPI(
        title="Manpower ERP API",
        version="0.1.0",
        lifespan=lifespan,
        responses={422: {"model": ErrorResponse}, "default": {"model": ErrorResponse}},
    )
    api.add_middleware(RequestDiagnostics)
    api.include_router(identity_router)

    @api.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {
            401: "unauthenticated",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            503: "service_unavailable",
            429: "rate_limited",
        }
        return error_response(
            request,
            exc.status_code,
            codes.get(exc.status_code, "http_error"),
            HTTPStatus(exc.status_code).phrase,
            exc.headers,
        )

    @api.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            request, 422, "validation_error", "Request validation failed"
        )

    @api.get("/api/bootstrap", response_model=Bootstrap)
    def bootstrap() -> Bootstrap:
        return Bootstrap()

    @api.get("/api/health/live", response_model=Health)
    def live() -> Health:
        return Health(status="live")

    @api.get(
        "/api/health/ready",
        response_model=Health,
        responses={503: {"model": ErrorResponse}},
    )
    def ready(session: Annotated[Session, Depends(get_session)]) -> Health:
        try:
            session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.warning("database_unavailable")
            raise HTTPException(status_code=503) from None
        return Health(status="ready")

    return api


app = create_app()
