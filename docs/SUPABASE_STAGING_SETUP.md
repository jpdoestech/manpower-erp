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
