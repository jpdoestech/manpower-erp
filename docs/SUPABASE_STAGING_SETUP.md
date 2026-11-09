# Supabase staging preparation

Scope: development/staging database and Auth first, explicitly authorized on
2026-11-05. This is not a production deployment or accepted ERP Auth integration.
Windows SQLite and local authentication remain the working local environment.

## Private connection configuration

Use the ignored repository-root `.env.supabase.staging`; do not overwrite `.env`.
Native Python processes do not automatically load this file. Do not commit its
contents, pass credentials on a shell command line or add them to VITE_* variables.
The Supabase publishable/secret API keys are not PostgreSQL credentials.

Set DATABASE_URL privately from Dashboard > Connect. Use a direct connection if
the machine supports its network route, otherwise the session pooler. Retain URL
options and require sslmode=verify-full with the provider's trusted CA configured
for libpq. Percent-encode special characters in the password. Do not resolve
certificate failures by disabling verification. Transaction pooling is not yet
verified for this application's prepared statements and session configuration.

Keep APP_ENV=staging and DATABASE_MODE=supabase. AUTH_PROVIDER=supabase is not
implemented: setting it currently fails closed. AUTH_PROVIDER=local preserves the
existing provider; it does not connect local ERP identities to Supabase Auth.
Do not start a hosted app until its exact HTTPS AUTH_ORIGIN and secure cookie
configuration have been reviewed.

## GitHub integration and a single migration authority

The owner reports connecting this repository in Supabase. The dashboard's linked
project, tracked branches, working directory, automatic branching and deployment
settings have not been independently inspected. Verify them before pushing any
provider configuration or enabling database automation. Keep production branches
outside this staging work.

Alembic under backend/alembic remains the ERP schema authority. Supabase's GitHub
integration reads supabase/config.toml and SQL migration files under
supabase/migrations; it does not execute Python Alembic. This repository has no
Supabase CLI configuration or second SQL migration history. Do not export the same
ERP revisions into a competing migration history or enable two migration runners.
Connecting GitHub alone does not deploy this FastAPI backend.

After the safeguards below are implemented and tested, use one explicitly invoked,
reviewed staging migration job, with environment-scoped secrets and a separate
migrator identity. It must run Alembic once per approved release, never on API
startup or on every request. Existing CI uses disposable databases and must never
receive the hosted staging URL as its test-server URL: integration fixtures create
and drop databases and require a dedicated disposable server.

## Required before the first hosted ERP migration

1. Verify the exact staging project, TLS, connection mode, current schemas and
   existing Alembic revision using read-only queries. Do not stamp an unknown DB.
2. Select a private ERP schema excluded from Data API exposure, with explicit
   least-privilege grants/default privileges. Current migrations use unqualified
   names; prove the chosen schema/search path and version-table behavior before
   running them. Do not blindly install auth tables in public. Check table,
   function and sequence privileges, not just RLS flags.
3. Separate migrator/owner and application roles. Runtime must not own tables,
   have BYPASSRLS or access Supabase's internal auth tables broadly. Browser
   anon/authenticated roles must not read ERP password/session/audit tables.
4. Test clean install, repeat upgrade, drift check, populated preservation and
   safe rollback on a disposable PostgreSQL database using that same schema/role
   configuration. Retain a staging backup and a reviewed recovery procedure.
5. Review Auth public signup (currently enabled), anonymous access, redirect URLs,
   recovery/MFA and operator custody. A Supabase account must never auto-create
   an approved ERP identity or grant company access. Do not change these settings
   under the guise of a read-only connectivity check.
6. Complete the existing human acceptance and ADR-017 decisions before the ERP
   provider adapter. Provider availability and valid JWKS do not prove JWT claim
   validation, ERP mapping, refresh rotation or immediate session revocation.

## Private schema rehearsal and staging runbook

The SQL under `scripts/postgres/` was rehearsed on isolated PostgreSQL 18.3.
Hosted execution waits for the accepted identity foundation and hosting review.
Confirm the staging project and recovery point, exclude `erp_private` from Data
API exposed schemas, and schedule one migration operator. Use a direct database
connection and keep `verify-full` with the staging CA. Keep separate credentials
for the provisioning operator, `erp_migrator`, and `erp_runtime`.

1. Provision `erp_migrator` and `erp_runtime` as dedicated LOGIN roles with no
   memberships, superuser, role/database creation, replication, or BYPASSRLS.
   Set credentials through a private operator channel. The SQL expects the
   Supabase roles `anon`, `authenticated`, and `service_role` to exist.
2. As the provisioning operator, from the repository root, run
   `psql -X -v ON_ERROR_STOP=1 -f scripts/postgres/prepare-private-schema.sql`.
   Supply connection settings through the operator's private environment. This
   transaction creates the schema, sets database-specific role search paths,
   and rejects unsafe roles, unexpected ownership, or ERP tables outside it.
3. Open a fresh migrator connection. Verify `SELECT current_user, current_schema()`
   returns `erp_migrator, erp_private`. From `backend` with the migrator's private
   `DATABASE_URL` and `DATABASE_MODE=supabase`, run `uv run --locked alembic upgrade head`
   followed by `uv run --locked alembic check`. Use the reviewed revision only.
   The role's search path puts both ERP tables and Alembic history in the private
   schema without rewriting migrations or changing SQLite.
4. From the root, as `erp_migrator`, run
   `psql -X -v ON_ERROR_STOP=1 -f scripts/postgres/grant-private-runtime.sql` and
   `psql -X -v ON_ERROR_STOP=1 -f scripts/postgres/verify-private-schema.sql`.
   Grants are pinned to the tested revision. Review them for each schema change.
   Runtime gets the necessary identity operations, append-only audit access
   with the `created_at` return column, and no access to Alembic history.
5. Reconnect as `erp_runtime` and check the current role/schema. Check readiness,
   login, session lookup, CSRF logout, and rejection of the old session using a
   synthetic account. Verify denied reads as the Data API roles and denied DDL
   as the runtime. Point FastAPI only at the runtime connection after those checks.

If any step fails, keep the API disconnected from the staging database. Compare
the Alembic revision and catalog privileges before retrying. Each SQL script
that writes is transactional, and repeat setup/grant and repeat upgrade were
rehearsed. Empty downgrade/reinstall was tested locally only. Preserve populated
identity and audit history and use the reviewed recovery point for recovery.

References for the security boundary include the [PostgreSQL schema search path](https://www.postgresql.org/docs/current/ddl-schemas.html)
and [Supabase Data API security](https://supabase.com/docs/guides/api/securing-your-api).

## Verified preflight — 2026-11-05

Bounded HTTPS GETs using the supplied public project configuration returned:

- JWKS: HTTP 200, one ES256 public signing key.
- Auth health: HTTP 200.
- Auth settings: HTTP 200, disable_signup=false. Anonymous eligibility was not
  established by the returned field; do not infer it is disabled.
- PostgreSQL: not tested because DATABASE_URL remained empty in the ignored file.

Follow-up: the saved database URL now matches the project and contains an actual
password value. The missing sslmode=verify-full option was added privately.
Connectivity is still unverified: default CA configuration is missing; a
process-only system trust-store retry rejects the server certificate. Download
the database CA from Supabase Database Settings to ignored .local/supabase-ca.crt
before retrying with an explicit sslrootcert. No certificate bypass is permitted.

Latest result: the supplied CA parses and explicit sslrootcert is now configured
privately. The read-only probe exits 0 with TLS, CA/hostname verification and
read-only transactions. No ERP identity tables, Alembic version table or
erp_private schema were found. The connected role has BYPASSRLS; it is unsuitable
for API runtime. Both API roles have public schema USAGE, and the catalog contains
32 default table privilege entries for those roles in public (not a table count).
Do not migrate unqualified auth tables there. A private schema/role configuration
and its disposable PostgreSQL tests are the next step; no cloud DDL has run.

No migrations, cloud accounts, settings or data were changed. No SDK was installed.
The offered @supabase/server package targets JavaScript runtimes; the existing
FastAPI Python backend remains authoritative. No cloud login is enabled.

References: [GitHub integration](https://supabase.com/docs/guides/deployment/branching/github-integration),
[PostgreSQL connections](https://supabase.com/docs/guides/database/connecting-to-postgres),
[API keys](https://supabase.com/docs/guides/getting-started/api-keys),
[server package](https://supabase.com/docs/reference/server/introduction).
