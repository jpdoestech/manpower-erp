import json
import logging
import sys
from collections.abc import Mapping
from contextvars import ContextVar
from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import Request
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id: ContextVar[str] = ContextVar("request_id", default="")
logger = logging.getLogger("manpower")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "request_id": request_id.get(),
        }
        for field in ("method", "route", "status", "duration_ms", "error_type"):
            if hasattr(record, field):
                event[field] = getattr(record, field)
        return json.dumps(event)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False


def error_response(
    request: Request,
    status: int,
    code: str,
    message: str,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        {
            "error": {
                "code": code,
                "message": message,
                "request_id": request.state.request_id,
            }
        },
        status_code=status,
        headers=headers,
    )


def correlation_id(scope: Scope) -> str:
    values = Headers(scope=scope).getlist("x-request-id")
    if len(values) == 1 and len(values[0]) == 36:
        try:
            value = str(UUID(values[0]))
            if value == values[0]:
                return value
        except ValueError:
            pass
    return str(uuid4())


class RequestDiagnostics:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        identifier = correlation_id(scope)
        scope.setdefault("state", {})["request_id"] = identifier
        token = request_id.set(identifier)
        started = perf_counter()
        status = 500
        response_started = False

        async def send_response(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                status = message["status"]
                response_started = True
                MutableHeaders(scope=message)["X-Request-ID"] = identifier
            await send(message)

        try:
            await self.app(scope, receive, send_response)
        except Exception as exc:
            logger.error("request_failed", extra={"error_type": type(exc).__name__})
            if response_started:
                raise RuntimeError("Response could not be completed") from None
            response = error_response(
                Request(scope), 500, "internal_error", "Internal server error"
            )
            await response(scope, receive, send_response)
        finally:
            method = scope["method"]
            logger.info(
                "request_completed",
                extra={
                    "method": method
                    if method
                    in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
                    else "OTHER",
                    "route": getattr(scope.get("route"), "path", "unmatched"),
                    "status": status,
                    "duration_ms": round((perf_counter() - started) * 1000, 3),
                },
            )
            request_id.reset(token)
