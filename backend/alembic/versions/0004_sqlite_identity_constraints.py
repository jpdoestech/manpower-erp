"""Match PostgreSQL identity length/Boolean constraints on local SQLite."""

from alembic import op

revision: str = "0004_sqlite_constraints"
down_revision: str = "0003_account_controls"
branch_labels: str | None = None
depends_on: str | None = None

# Fixed schema definitions; no request/config input is interpolated into DDL.
LIMITS = {
    "auth_users": {"password_hash": 512},
    "auth_sessions": {"token_hash": 64},
    "auth_login_limits": {"key": 80},
    "auth_events": {"kind": 40, "source": 16},
    "auth_account_changes": {"action": 24},
    "auth_password_resets": {"token_hash": 64},
}
UUID_COLUMNS = {
    "auth_users": ("id",),
    "auth_sessions": ("user_id",),
    "auth_login_limits": (),
    "auth_events": ("id", "user_id", "actor_id", "change_id", "request_id"),
    "auth_account_changes": ("id", "user_id", "requested_by", "approved_by"),
    "auth_password_resets": ("user_id",),
}


def upgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        return
    for table, columns in LIMITS.items():
        conditions = [f"length(NEW.{name}) > {size}" for name, size in columns.items()]
        for name in UUID_COLUMNS[table]:
            conditions.append(
                f"(NEW.{name} IS NOT NULL AND (length(NEW.{name}) <> 32 "
                f"OR NEW.{name} GLOB '*[^0-9a-f]*'))"
            )
        if table == "auth_login_limits":
            conditions.append("typeof(NEW.attempts) <> 'integer'")
        if table == "auth_users":
            conditions.extend(
                ["NEW.is_active NOT IN (0, 1)", "NEW.is_super_admin NOT IN (0, 1)"]
            )
        condition = " OR ".join(conditions)
        # Do not silently bless invalid rows when upgrading an existing file.
        invalid = condition.replace("NEW.", "")
        if (
            op.get_bind()
            .exec_driver_sql(f"SELECT 1 FROM {table} WHERE {invalid} LIMIT 1")
            .first()
        ):
            raise RuntimeError(
                "SQLite identity constraints require valid existing data"
            )
        for operation in ("INSERT", "UPDATE"):
            op.execute(f"""
                CREATE TRIGGER {table}_limits_{operation.lower()}
                BEFORE {operation} ON {table} FOR EACH ROW WHEN {condition}
                BEGIN SELECT RAISE(ABORT, 'Invalid identity field'); END
            """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        for table in LIMITS:
            for operation in ("insert", "update"):
                op.execute(f"DROP TRIGGER {table}_limits_{operation}")
