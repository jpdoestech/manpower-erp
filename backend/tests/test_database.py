import os

import psycopg
import pytest


@pytest.mark.integration
def test_postgres_connection_and_rollback() -> None:
    # Fail rather than skip: integration checks must explicitly target a test DB.
    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5) as connection:
        assert connection.execute("SELECT 1").fetchone() == (1,)
        connection.execute("CREATE TEMP TABLE bootstrap_probe (value integer)")
        connection.commit()
        connection.execute("INSERT INTO bootstrap_probe VALUES (1)")
        connection.rollback()
        assert connection.execute(
            "SELECT count(*) FROM bootstrap_probe"
        ).fetchone() == (0,)
