from sqlalchemy.exc import SQLAlchemyError

from alembic import context
from app.database import Base, create_database_engine, database_url
from app.identity import models  # noqa: F401 -- register identity metadata

target_metadata = Base.metadata


def run_migrations() -> None:
    if context.is_offline_mode():
        context.configure(
            url=database_url(),
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
        return

    engine = create_database_engine()
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    except SQLAlchemyError:
        raise RuntimeError(
            "Migration failed; verify database configuration and connectivity"
        ) from None
    finally:
        engine.dispose()


run_migrations()
