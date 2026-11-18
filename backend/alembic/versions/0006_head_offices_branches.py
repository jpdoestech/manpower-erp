"""Company-preserving operational hierarchy and explicit access capability."""

import sqlalchemy as sa

from alembic import op

revision: str = "0006_head_offices_branches"
down_revision: str = "0005_company_registry"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.add_column(
        "org_company_grants",
        sa.Column(
            "manage_hierarchy", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    for table, prefix in (
        ("org_head_offices", "head_office"),
        ("org_branches", "branch"),
    ):
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "company_id",
                sa.Uuid(),
                sa.ForeignKey("org_companies.id"),
                nullable=False,
            ),
            sa.Column("code", sa.String(32), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("valid_from", sa.Date(), nullable=False),
            sa.Column("valid_to", sa.Date()),
            sa.Column(
                "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
            ),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column(
                "created_by", sa.Uuid(), sa.ForeignKey("auth_users.id"), nullable=False
            ),
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
            *(
                [
                    sa.Column("head_office_id", sa.Uuid(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ["company_id", "head_office_id"],
                        ["org_head_offices.company_id", "org_head_offices.id"],
                    ),
                ]
                if table == "org_branches"
                else []
            ),
            sa.UniqueConstraint("company_id", "code", name=f"uq_{prefix}_code"),
            sa.UniqueConstraint("company_id", "id", name=f"uq_{prefix}_company_id"),
            sa.CheckConstraint(
                "length(code) BETWEEN 2 AND 32", name=f"ck_{prefix}_code"
            ),
            sa.CheckConstraint(
                "length(name) BETWEEN 1 AND 200", name=f"ck_{prefix}_name"
            ),
            sa.CheckConstraint(
                "valid_to IS NULL OR valid_to >= valid_from", name=f"ck_{prefix}_dates"
            ),
            sa.CheckConstraint("version > 0", name=f"ck_{prefix}_version"),
        )
    op.create_table(
        "org_hierarchy_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "company_id", sa.Uuid(), sa.ForeignKey("org_companies.id"), nullable=False
        ),
        sa.Column("head_office_id", sa.Uuid()),
        sa.Column("branch_id", sa.Uuid()),
        sa.Column(
            "actor_id", sa.Uuid(), sa.ForeignKey("auth_users.id"), nullable=False
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("before_state", sa.JSON()),
        sa.Column("after_state", sa.JSON(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id", "head_office_id"],
            ["org_head_offices.company_id", "org_head_offices.id"],
        ),
        sa.ForeignKeyConstraint(
            ["company_id", "branch_id"], ["org_branches.company_id", "org_branches.id"]
        ),
        sa.CheckConstraint(
            "(head_office_id IS NULL) <> (branch_id IS NULL)",
            name="ck_hierarchy_event_subject",
        ),
    )
    op.create_index(
        "ix_org_hierarchy_events_company_id", "org_hierarchy_events", ["company_id"]
    )
    if op.get_bind().dialect.name == "sqlite":
        for operation in ("UPDATE", "DELETE"):
            name = f"org_hierarchy_events_immutable_{operation.lower()}"
            op.execute(f"""CREATE TRIGGER {name}
                BEFORE {operation} ON org_hierarchy_events FOR EACH ROW
                BEGIN SELECT RAISE(ABORT, 'Hierarchy events are immutable'); END""")
        return
    op.execute("""CREATE TRIGGER org_hierarchy_events_immutable
        BEFORE UPDATE OR DELETE OR TRUNCATE ON org_hierarchy_events
        FOR EACH STATEMENT EXECUTE FUNCTION auth_reject_event_mutation()""")
    actor = "NULLIF(current_setting('erp.user_id', true), '')::uuid"
    for table in ("org_head_offices", "org_branches", "org_hierarchy_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        scope = f"""EXISTS (SELECT 1 FROM org_company_grants g
            WHERE g.company_id = {table}.company_id AND g.user_id = {actor}
              AND g.is_active AND g.manage_hierarchy)"""
        op.execute(
            f"CREATE POLICY hierarchy_read ON {table} FOR SELECT USING ({scope})"
        )
        proof = "actor_id" if table == "org_hierarchy_events" else "created_by"
        op.execute(f"""CREATE POLICY hierarchy_insert ON {table}
            FOR INSERT WITH CHECK ({scope} AND {proof} = {actor})""")
        if table != "org_hierarchy_events":
            op.execute(f"""CREATE POLICY hierarchy_update ON {table}
                FOR UPDATE USING ({scope}) WITH CHECK ({scope})""")


def downgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("Hierarchy downgrade requires online history verification")
    for table in ("org_hierarchy_events", "org_branches", "org_head_offices"):
        if op.get_bind().scalar(sa.text(f"SELECT 1 FROM {table} LIMIT 1")):
            raise RuntimeError(
                "Hierarchy downgrade refused; preserve organization history"
            )
    if op.get_bind().scalar(
        sa.text("SELECT 1 FROM org_company_grants WHERE manage_hierarchy LIMIT 1")
    ):
        raise RuntimeError("Hierarchy downgrade refused; revoke hierarchy grants first")
    for table in ("org_hierarchy_events", "org_branches", "org_head_offices"):
        op.drop_table(table)
    op.drop_column("org_company_grants", "manage_hierarchy")
