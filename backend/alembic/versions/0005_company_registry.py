"""Company registry and explicit bootstrap grants."""

import sqlalchemy as sa

from alembic import op

revision: str = "0005_company_registry"
down_revision: str = "0004_sqlite_constraints"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.create_table(
        "org_companies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(32), unique=True, nullable=False),
        sa.Column("legal_name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("auth_users.id")),
        sa.CheckConstraint("length(code) BETWEEN 2 AND 32", name="ck_company_code"),
        sa.CheckConstraint(
            "length(legal_name) BETWEEN 1 AND 200", name="ck_company_name"
        ),
        sa.CheckConstraint("version > 0", name="ck_company_version"),
    )
    op.create_table(
        "org_company_grants",
        sa.Column(
            "company_id", sa.Uuid(), sa.ForeignKey("org_companies.id"), primary_key=True
        ),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("auth_users.id"), primary_key=True
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "org_company_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "company_id", sa.Uuid(), sa.ForeignKey("org_companies.id"), nullable=False
        ),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("auth_users.id")),
        sa.Column("subject_id", sa.Uuid(), sa.ForeignKey("auth_users.id")),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("before_name", sa.String(200)),
        sa.Column("after_name", sa.String(200)),
        sa.Column("before_active", sa.Boolean()),
        sa.Column("after_active", sa.Boolean()),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_org_company_events_company_id", "org_company_events", ["company_id"]
    )
    if op.get_bind().dialect.name == "sqlite":
        for operation in ("UPDATE", "DELETE"):
            name = f"org_company_events_immutable_{operation.lower()}"
            op.execute(f"""CREATE TRIGGER {name}
                BEFORE {operation} ON org_company_events FOR EACH ROW
                BEGIN SELECT RAISE(ABORT, 'Company events are immutable'); END""")
        return
    op.execute("""CREATE TRIGGER org_company_events_immutable
        BEFORE UPDATE OR DELETE OR TRUNCATE ON org_company_events
        FOR EACH STATEMENT EXECUTE FUNCTION auth_reject_event_mutation()""")
    for table in ("org_companies", "org_company_grants", "org_company_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    # Table owners are trusted provisioning operators. Runtime must be a non-owner.
    actor = "NULLIF(current_setting('erp.user_id', true), '')::uuid"
    op.execute(f"""CREATE POLICY company_grant_read ON org_company_grants
        FOR SELECT USING (user_id = {actor})""")
    scope = f"""EXISTS (SELECT 1 FROM org_company_grants g
        WHERE g.company_id = id AND g.user_id = {actor} AND g.is_active)"""
    op.execute(
        f"CREATE POLICY company_read ON org_companies FOR SELECT USING ({scope})"
    )
    op.execute(f"""CREATE POLICY company_update ON org_companies
        FOR UPDATE USING ({scope}) WITH CHECK ({scope})""")
    event_scope = f"""EXISTS (SELECT 1 FROM org_company_grants g
        WHERE g.company_id = org_company_events.company_id
          AND g.user_id = {actor} AND g.is_active)"""
    op.execute(f"""CREATE POLICY company_event_insert ON org_company_events
        FOR INSERT WITH CHECK (actor_id = {actor} AND {event_scope})""")
    op.execute(f"""CREATE POLICY company_event_read ON org_company_events
        FOR SELECT USING ({event_scope})""")


def downgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("Company downgrade requires online empty-table verification")
    for table in ("org_company_events", "org_company_grants", "org_companies"):
        if op.get_bind().scalar(sa.text(f"SELECT 1 FROM {table} LIMIT 1")):
            raise RuntimeError(
                "Company downgrade refused; preserve organization history"
            )
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP POLICY company_read ON org_companies")
        op.execute("DROP POLICY company_update ON org_companies")
    for table in ("org_company_events", "org_company_grants", "org_companies"):
        op.drop_table(table)
