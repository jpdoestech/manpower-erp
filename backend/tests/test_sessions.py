import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import create_database_engine, get_session
from app.main import create_app
from app.observability import logger


@pytest.mark.integration
@pytest.mark.usefixtures("disposable_database")
def test_session_rollback_and_explicit_commit() -> None:
    app = create_app()
    engine = create_database_engine()
    app.state.engine = engine
    request = Request({"type": "http", "app": app})
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE session_probe (value integer)"))
        sessions = get_session(request)
        next(sessions).execute(text("INSERT INTO session_probe VALUES (1)"))
        sessions.close()
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*) FROM session_probe")
                ).scalar_one()
                == 0
            )
        sessions = get_session(request)
        session = next(sessions)
        session.execute(text("INSERT INTO session_probe VALUES (1)"))
        session.commit()
        sessions.close()
        sessions = get_session(request)
        next(sessions).execute(text("INSERT INTO session_probe VALUES (2)"))
        with pytest.raises(ValueError, match="abort"):
            sessions.throw(ValueError("abort"))
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT value FROM session_probe")
            ).scalars().all() == [1]
    finally:
        engine.dispose()


@pytest.mark.integration
@pytest.mark.usefixtures("disposable_database")
def test_readiness_against_real_database() -> None:
    handlers = logger.handlers[:]
    try:
        with TestClient(create_app()) as client:
            assert client.get("/api/health/live").json() == {"status": "live"}
            assert client.get("/api/health/ready").json() == {"status": "ready"}
    finally:
        logger.handlers = handlers
