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

## Private schema rehearsal plan — 2026-11-09

The user authorized the migration rehearsal and subsequent staging application
subject to the release gates. Work in PR #13. Add operator SQL under
`scripts/postgres/` and document commands in the staging guide. Use an isolated
loopback PostgreSQL cluster with synthetic credentials and Supabase-style API
roles. Existing Alembic revisions and runtime code stay unchanged.

1. Provision `erp_private` for a dedicated non-superuser migrator and a separate
   non-owner runtime. Set the database-specific search path for both. Refuse an
   unsafe role or conflicting starting state before any migration.
2. Verify clean install, repeat upgrade, drift check, and empty downgrade/reinstall.
   Verify existing audit and identity history blocks destructive downgrade.
3. Grant runtime access only to the existing identity operations. Prove real API
   login/logout, append-only audit, denial of runtime DDL and schema history writes,
   and denial of ERP reads for both API roles even with Supabase-style public
   defaults. Run backend lint, types and both SQLite and PostgreSQL suites.
4. Run the rehearsal from the committed inputs, record exact results and push the
   review. Stop before hosted DDL if the accepted foundation or hosting gates are
   still pending. No stage of this rehearsal provisions Supabase Auth or users.

## Private schema rehearsal results — 2026-11-09

Executed all three `scripts/postgres/` SQL files using psycopg on a new isolated
PostgreSQL 18.3 cluster bound to loopback. The local Python rehearsal checked the
server data directory before setup. No hosted credentials were loaded.

- Setup rejected a runtime role with BYPASSRLS and a pre-existing public identity
  table. Both failures rolled back. Repeated setup and repeated grants succeeded.
- Alembic as `erp_migrator`: `upgrade head` twice, `check`, `downgrade base`,
  `upgrade head`, `check` all passed. Identity tables and Alembic history stayed in
  `erp_private`. A populated downgrade failed as intended. The identity, audit
  rows and current revision survived, and the final drift check passed.
- Verified denied identity reads as `anon`, `authenticated`, and `service_role`.
  Runtime DDL, Alembic reads/writes, audit reads and audit truncation were denied.
  FastAPI using the restricted role provisioned a synthetic account and returned
  readiness 200, login 200, session lookup 200, CSRF logout 204, and session lookup
  401 after logout. This exercised the local auth provider against private PG.
- From `backend`: `.venv/Scripts/pytest.exe -q -m 'not integration'` returned
  110 passed, 42 deselected in 19.41s. With the loopback disposable PostgreSQL
  URL, `.venv/Scripts/pytest.exe -q -m integration` returned 42 passed,
  110 deselected in 57.72s.
- From `backend`: `.venv/Scripts/ruff.exe format --config pyproject.toml --check . ../scripts`
  reported 37 formatted files. `.venv/Scripts/ruff.exe check --config pyproject.toml . ../scripts`
  passed. `.venv/Scripts/mypy.exe app tests alembic ../scripts` reported no issues
  in 37 source files. `git diff --check` passed.

Fresh fetch still finds main at `b3517d3`. GitHub returned zero submitted reviews
for PRs #2, #3, #9 and #12, and both P1-01 security decisions remain pending in
the repository. The local result is ready for review in PR #13. Hosted DDL and
live Data API checks are still pending the accepted identity foundation and CR-002
hosting review. No cloud roles, schemas, data or settings were changed.
