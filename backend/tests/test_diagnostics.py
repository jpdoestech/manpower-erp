import asyncio
import json
import logging
from collections.abc import Iterator
from io import StringIO
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import httpx2
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database import get_session
from app.main import create_app
from app.observability import logger, request_id


@pytest.fixture
def api() -> FastAPI:
    return create_app()


@pytest.fixture
def log_output() -> StringIO:
    return StringIO()


@pytest.fixture
def client(
    api: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    log_output: StringIO,
) -> Iterator[TestClient]:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:sentinel-password@127.0.0.1:1/test"
    )
    handlers = logger.handlers[:]
    try:
        with TestClient(api) as client:
            handler = logger.handlers[0]
            assert isinstance(handler, logging.StreamHandler)
            handler.setStream(log_output)
            yield client
    finally:
        logger.handlers = handlers


def test_live_does_not_use_database_and_ready_handles_outage(
    client: TestClient,
) -> None:
    assert client.get("/api/health/live").json() == {"status": "live"}
    response = client.get("/api/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_unavailable"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert "sentinel-password" not in response.text


def test_ready_returns_success_for_healthy_session(
    api: FastAPI, client: TestClient
) -> None:
    session = MagicMock(spec=Session)
    api.dependency_overrides[get_session] = lambda: session
    assert client.get("/api/health/ready").json() == {"status": "ready"}
    session.execute.assert_called_once()


def test_ready_never_echoes_database_exceptions(
    api: FastAPI, client: TestClient, log_output: StringIO
) -> None:
    session = MagicMock(spec=Session)
    session.execute.side_effect = OperationalError(
        "secret SQL",
        {"password": "secret-param"},
        Exception("postgresql://user:secret-password@secret-host/db"),
    )
    api.dependency_overrides[get_session] = lambda: session
    response = client.get("/api/health/ready")
    assert response.status_code == 503
    output = response.text + log_output.getvalue()
    for secret in ("secret SQL", "secret-param", "secret-password", "secret-host"):
        assert secret not in output


def test_valid_correlation_id_is_preserved(client: TestClient) -> None:
    identifier = str(uuid4())
    response = client.get("/api/bootstrap", headers={"X-Request-ID": identifier})
    assert response.headers["x-request-id"] == identifier
    assert request_id.get() == ""


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [("X-Request-ID", "not-valid-secret")],
        [("X-Request-ID", "x" * 500)],
        [("X-Request-ID", str(uuid4())), ("X-Request-ID", str(uuid4()))],
    ],
)
def test_invalid_missing_or_duplicate_ids_are_replaced(
    client: TestClient, headers: list[tuple[str, str]]
) -> None:
    response = client.get("/api/bootstrap", headers=headers)
    identifier = response.headers["x-request-id"]
    assert str(UUID(identifier)) == identifier
    assert identifier not in [value for _, value in headers]


def test_error_envelope_and_protocol_headers(api: FastAPI, client: TestClient) -> None:
    response = client.get("/unknown")
    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Not Found",
            "request_id": response.headers["x-request-id"],
        }
    }
    response = client.post("/api/bootstrap")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"
    assert response.headers["allow"] == "GET"

    @api.get("/_test/auth")
    def auth_error() -> None:
        raise HTTPException(
            401, detail="secret-auth-detail", headers={"WWW-Authenticate": "Bearer"}
        )

    response = client.get("/_test/auth")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert "secret-auth-detail" not in response.text


class Input(BaseModel):
    number: int


def test_validation_and_unexpected_errors_are_safe(
    api: FastAPI, client: TestClient, log_output: StringIO
) -> None:
    @api.post("/_test/input")
    def validate_input(value: Input) -> None:
        pass

    @api.get("/_test/failure")
    def fail() -> None:
        raise RuntimeError("secret-exception-text")

    response = client.post("/_test/input", json={"number": "secret-body"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert "secret-body" not in response.text
    response = client.get("/_test/failure")
    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "internal_error",
        "message": "Internal server error",
        "request_id": response.headers["x-request-id"],
    }
    output = response.text + log_output.getvalue()
    assert "secret-body" not in output
    assert "secret-exception-text" not in output


def test_json_request_logs_are_bounded_and_redacted(
    api: FastAPI, client: TestClient, log_output: StringIO
) -> None:
    @api.get("/_test/resource/{identifier}")
    def resource(identifier: str) -> dict[str, bool]:
        return {"ok": True}

    identifier = str(uuid4())
    response = client.get(
        "/_test/resource/secret-path?token=secret-query",
        headers={"Authorization": "Bearer secret-auth", "X-Request-ID": identifier},
    )
    output = log_output.getvalue()
    events = [json.loads(line) for line in output.splitlines()]
    completed = [event for event in events if event["event"] == "request_completed"]
    assert len(completed) == 1
    event = completed[0]
    assert event["request_id"] == response.headers["x-request-id"] == identifier
    assert event["route"] == "/_test/resource/{identifier}"
    assert event["method"] == "GET" and event["status"] == 200
    assert event["duration_ms"] >= 0
    assert set(event) == {
        "timestamp",
        "level",
        "event",
        "request_id",
        "method",
        "route",
        "status",
        "duration_ms",
    }
    for secret in ("secret-path", "secret-query", "secret-auth"):
        assert secret not in output


def test_unmatched_paths_and_invalid_headers_are_not_logged(
    client: TestClient, log_output: StringIO
) -> None:
    response = client.get(
        "/secret-unknown-path?password=secret-query",
        headers={
            "X-Request-ID": "secret-invalid-id",
            "Origin": "https://untrusted.example",
        },
    )
    assert response.status_code == 404
    assert "access-control-allow-origin" not in response.headers
    output = log_output.getvalue()
    assert json.loads(output.splitlines()[-1])["route"] == "unmatched"
    assert "secret-" not in output


def test_concurrent_request_ids_do_not_leak(
    api: FastAPI, client: TestClient, log_output: StringIO
) -> None:
    @api.get("/_test/concurrent")
    async def concurrent() -> dict[str, str]:
        before = request_id.get()
        await asyncio.sleep(0)
        assert request_id.get() == before
        return {"request_id": before}

    async def exercise() -> None:
        transport = httpx2.ASGITransport(app=api)
        async with httpx2.AsyncClient(
            transport=transport, base_url="http://test"
        ) as http:
            identifiers = [str(uuid4()) for _ in range(8)]
            responses = await asyncio.gather(
                *(
                    http.get("/_test/concurrent", headers={"X-Request-ID": identifier})
                    for identifier in identifiers
                )
            )
            assert [
                response.json()["request_id"] for response in responses
            ] == identifiers
            assert [
                response.headers["x-request-id"] for response in responses
            ] == identifiers

    asyncio.run(exercise())
    events = [json.loads(line) for line in log_output.getvalue().splitlines()]
    assert (
        len(
            {
                event["request_id"]
                for event in events
                if event["event"] == "request_completed"
            }
        )
        == 8
    )
    assert request_id.get() == ""
