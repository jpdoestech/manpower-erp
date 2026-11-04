from pathlib import Path

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from alembic import command
from app.database import create_database_engine


@pytest.mark.integration
@pytest.mark.usefixtures("disposable_database")
def test_clean_migrations_repeat_downgrade_and_preserve_data() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    assert ScriptDirectory.from_config(config).get_heads() == ["0001_infrastructure"]
    engine = create_database_engine()
    try:
        assert inspect(engine).get_table_names() == []
        command.upgrade(config, "head")
        assert inspect(engine).get_table_names() == ["alembic_version"]
        command.upgrade(config, "head")
        command.check(config)
        with engine.begin() as connection:
            assert (
                MigrationContext.configure(connection).get_current_revision()
                == "0001_infrastructure"
            )
            connection.execute(text("CREATE TABLE preservation_probe (value integer)"))
            connection.execute(text("INSERT INTO preservation_probe VALUES (42)"))
        command.downgrade(config, "base")
        with engine.connect() as connection:
            assert MigrationContext.configure(connection).get_current_revision() is None
            assert (
                connection.execute(
                    text("SELECT value FROM preservation_probe")
                ).scalar_one()
                == 42
            )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert (
                MigrationContext.configure(connection).get_current_revision()
                == "0001_infrastructure"
            )
            assert (
                connection.execute(
                    text("SELECT value FROM preservation_probe")
                ).scalar_one()
                == 42
            )
    finally:
        engine.dispose()
