"""Initialize migration history without business schema."""

revision: str = "0001_infrastructure"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    # The baseline owns no domain objects; Alembic removes only the version row.
    pass
