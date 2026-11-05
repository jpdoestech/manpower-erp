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
