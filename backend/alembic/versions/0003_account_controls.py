"""Add controlled identity administration; existing identities gain no authority."""

import sqlalchemy as sa

from alembic import op

revision: str = "0003_account_controls"
down_revision: str = "0002_identity"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "auth_users",
        sa.Column(
            "is_super_admin", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.create_table(
        "auth_account_changes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("auth_users.id"), nullable=False),
        sa.Column(
            "requested_by", sa.Uuid(), sa.ForeignKey("auth_users.id"), nullable=False
        ),
        sa.Column("action", sa.String(24), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("auth_users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "action IN ('activate', 'deactivate', 'reset_password', 'unlock')",
            name="ck_auth_change_action",
        ),
        sa.CheckConstraint(
            "approved_by IS NULL OR "
            "(approved_by <> requested_by AND approved_by <> user_id)",
            name="ck_auth_change_separation",
        ),
        sa.CheckConstraint(
            "(approved_by IS NULL) = (approved_at IS NULL)",
            name="ck_auth_change_approval",
        ),
    )
    op.create_table(
        "auth_password_resets",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("auth_users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_auth_password_resets_user_id", "auth_password_resets", ["user_id"]
    )
    op.add_column(
        "auth_events", sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("auth_users.id"))
    )
    op.add_column(
        "auth_events",
        sa.Column("change_id", sa.Uuid(), sa.ForeignKey("auth_account_changes.id")),
    )


def downgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("Account controls downgrade requires online verification")
    connection = op.get_bind()
    for table in ("auth_account_changes", "auth_password_resets"):
        if connection.scalar(
            sa.select(sa.literal(True)).select_from(sa.table(table)).limit(1)
        ):
            raise RuntimeError(
                "Account controls downgrade would erase security history"
            )
    if connection.scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM auth_users WHERE is_super_admin)")
    ):
        raise RuntimeError(
            "Account controls downgrade would erase administrator grants"
        )
    if connection.scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM auth_events "
            "WHERE actor_id IS NOT NULL OR change_id IS NOT NULL)"
        )
    ):
        raise RuntimeError("Account controls downgrade would erase security history")
    op.drop_column("auth_events", "change_id")
    op.drop_column("auth_events", "actor_id")
    op.drop_index("ix_auth_password_resets_user_id", table_name="auth_password_resets")
    op.drop_table("auth_password_resets")
    op.drop_table("auth_account_changes")
    op.drop_column("auth_users", "is_super_admin")
