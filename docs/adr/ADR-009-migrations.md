# ADR-009 — Explicit, transactional Alembic migrations

Date: 2026-11-04. Status: ADOPTED for P0-02 infrastructure.

Alternatives: ORM create_all at startup, handwritten untracked DDL, or Alembic
revision history. Choose Alembic with SQLAlchemy metadata, one linear head and
reviewed revisions. Runtime workers never create tables or auto-run migrations.
An explicit migration job runs before API readiness. Use environment configuration;
no credentials in alembic.ini, revision files or logging.

The baseline revision has no domain DDL: only Alembic's version table initializes.
Upgrade is repeatable; safe downgrade removes the version row but leaves the
version table. It must not delete unrelated data. Future revisions use constraints,
expand/backfill/contract sequencing and a documented rollback/forward-fix plan;
never pretend a destructive downgrade is reversible. Alembic autogenerate output
is a proposal requiring review, not permission to apply destructive changes.

Tests create generated disposable databases, exercise clean/repeated upgrade,
metadata drift check, safe downgrade and re-upgrade with a preservation sentinel.
CI has test-only database-creation privileges. Runtime code requires only the
privileges its queries need; production migrator/runtime roles must be separate.
Current Compose credentials remain development-only, consistent with P0-01.

Consequences: deploy ordering is explicit and migration files ship in the API
image. Local upgrades must target an owned disposable DB; production runs require
explicit release authorization and backup/restore evidence. No production migration
or permission provisioning is part of P0-02.
Evidence: `backend/alembic/`, migration tests, Compose/CI migration commands.
