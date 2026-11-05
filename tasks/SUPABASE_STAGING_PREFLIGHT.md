# Supabase staging connection preflight

2026-11-05. Explicit scope: user-confirmed development/staging, database/Auth first.
This authorizes staging preparation and connection checks, not production,
fabricated human security acceptance or replacement of the FastAPI backend.

Before changes: keep Windows SQLite/local auth and existing .env untouched. Do not
install @supabase/server into Python: it is a JavaScript/server-runtime package.
Read current official package, Edge Functions, API key and PostgreSQL docs.

## Small slice and acceptance

1. Create an ignored .env.supabase.staging only if absent, using supplied public
   project values; leave missing secrets/database credentials blank. Never commit
   the live project configuration or paste credentials into test output.
2. Probe only public JWKS and read-only Auth health/settings endpoints with bounded
   HTTPS requests. Record availability/configuration categories, not user records,
   keys or tokens. No account creation, sign-in, settings mutation or migrations.
3. Document Python/SQLAlchemy/PostgreSQL configuration, protected schema/roles and
   Data API exposure prerequisites. API keys cannot substitute for DATABASE_URL.
4. Ask user to set a staging PostgreSQL URL privately in the ignored file. Until
   supplied, DB connectivity/migrations remain unverified, not a successful deploy.
5. Preserve pending P1-01/B/ADR-017 auth acceptance; no cloud login implementation
   or production deployment. Commit/push only plan/guide/status evidence.

Acceptance: provided project classified staging; local configuration ignored,
native tooling unchanged; exact read-only probe outcomes and remaining credentials/
permissions recorded. Supabase platform availability is not ERP Auth integration.

## Results

Read-only probe executed with
`backend/.venv/Scripts/python.exe .local/supabase-staging-preflight.py`:
exit 1, because DATABASE_URL is empty. JWKS/health/settings each returned HTTP 200;
JWKS contains one ES256 key; disable_signup=false; anonymous setting unverified.
The ignored scratch probe bounded HTTPS responses/timeouts and suppressed secrets.
Database connection, TLS, grants and migrations remain NOT TESTED. The user's
"ready" reply is not treated as connection evidence. Requested private file update.

GitHub integration is owner-reported; dashboard automation settings unverified.
Official documentation confirms it does not execute Alembic. See
docs/SUPABASE_STAGING_SETUP.md for a single-authority migration path and the
private-schema/Data API/runtime-role safeguards required before hosted migration.
No package installed and no cloud resource changed. No full regression suite rerun
for this documentation-only slice; prior RC evidence is explicitly separate.

Follow-up private configuration check (2026-11-05): DATABASE_URL is now populated,
the project host matches, and the password placeholder is removed. Added the
missing sslmode=verify-full option to the ignored file without displaying secrets.
The read-only probe exits 1: default libpq trust requires a CA certificate. A
process-only retry with PGSSLROOTCERT=system also exits 1, reporting that the server
certificate is not trusted by that CA store. Installed libpq reports 180004.
No authenticated DB query or migration succeeded. Requested the provider's database
CA certificate at .local/supabase-ca.crt; never downgrade certificate verification.
Auth GETs still return HTTP 200. No product code or cloud setting changed.

## Successful certificate-backed connection — 2026-11-05

The saved .local/supabase-ca.crt parses as a CA file. Added an explicit sslrootcert
path to ignored staging configuration while preserving sslmode=verify-full.
`backend/.venv/Scripts/python.exe .local/supabase-staging-preflight.py` now exits 0,
including an expanded catalog-only permissions check. Exact observed results:

- JWKS, Auth health and settings: HTTP 200; one ES256 key; signup still enabled.
- Database connected with TLS and transaction_read_only=true. Verification of CA
  and hostname remained enabled. No application records were read.
- Connected role: superuser=false, bypass_rls=true. Not acceptable as app runtime.
- All six current ORM auth table names checked: zero present; zero in public.
- No erp_private schema or Alembic version table found.
- anon and authenticated roles both have public schema USAGE. Catalog contains
  32 public default table ACL privilege entries for those roles. This is a count
  of privilege entries, not tables; effective grants for new objects still depend
  on their creating role and need explicit testing.
- Transactions rolled back; no schema, account, grants or Auth settings changed.

Next safe implementation slice: plan/test an ERP-private schema and separate
runtime/migrator roles against disposable PostgreSQL before hosted migration.
Do not run current unqualified migrations into public, enable an automatic GitHub
migration runner, or reuse this privileged connection in a deployed API. Keep
ADR-017/human Auth acceptance pending. Supabase availability is not ERP cloud login.
git diff --check and ignored-file checks pass; product regression suites were not
rerun for documentation/private-configuration-only changes.
