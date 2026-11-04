"""Add global identity without company memberships or role grants."""

import sqlalchemy as sa

from alembic import op

revision: str = "0002_identity"
down_revision: str = "0001_infrastructure"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    sqlite = op.get_bind().dialect.name == "sqlite"
    op.create_table(
        "auth_users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            (
                "length(username) BETWEEN 3 AND 64 AND username GLOB '[a-z]*' "
                "AND username NOT GLOB '*[^a-z0-9_.-]*' "
                "AND instr(username, char(0)) = 0"
                if sqlite
                else "username ~ '^[a-z][a-z0-9_.-]{2,63}$'"
            ),
            name="ck_auth_username",
        ),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("auth_users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_table(
        "auth_login_limits",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("window_started", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.CheckConstraint("attempts > 0", name="ck_auth_attempts"),
    )
    op.create_table(
        "auth_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("auth_users.id")),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    if sqlite:
        for operation in ("UPDATE", "DELETE"):
            op.execute(f"""
                CREATE TRIGGER auth_events_immutable_{operation.lower()}
                BEFORE {operation} ON auth_events FOR EACH ROW
                BEGIN SELECT RAISE(ABORT, 'Authentication events are immutable'); END
            """)
        return

    op.execute("""
        CREATE FUNCTION auth_reject_event_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Authentication events are immutable';
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER auth_events_immutable
        BEFORE UPDATE OR DELETE OR TRUNCATE ON auth_events
        FOR EACH STATEMENT EXECUTE FUNCTION auth_reject_event_mutation()
    """)


def downgrade() -> None:
    # Identity/audit history is retained; this downgrade is safe only on an empty DB.
    if op.get_context().as_sql:
        raise RuntimeError(
            "Identity downgrade requires online empty-table verification"
        )
    connection = op.get_bind()
    for table in ("auth_events", "auth_sessions", "auth_login_limits", "auth_users"):
        if connection.scalar(
            sa.select(sa.literal(True)).select_from(sa.table(table)).limit(1)
        ):
            raise RuntimeError(
                "Identity downgrade requires empty tables; preserve user/audit history"
            )
    op.drop_table("auth_events")
    if connection.dialect.name == "postgresql":
        op.execute("DROP FUNCTION auth_reject_event_mutation()")
    op.drop_table("auth_login_limits")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("auth_users")
