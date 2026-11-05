# Development infrastructure operations

P0-02 infrastructure plus P1-01 local authentication. No production deployment,
company memberships, tenant business data or financial workflows.
Infrastructure decisions are indexed in `tasks/DECISIONS.md` and `docs/adr/`.

## Windows launchers

Double-click root `setup.bat` once, then `run.bat` for normal local use. Docker
Desktop must be installed, running and in Linux-container mode on its local
default context. The scripts build/start/wait using existing Compose health and
migration dependencies; they pin the Compose file/env/project explicitly. Setup
creates a cryptographically random DB secret only for an absent `.env`, never
overwrites an existing file, and optionally invokes the existing ordinary-user CLI
with hidden confirmed passwords. Existing account names are not reset on failure.
The internal `run.bat --setup` path suppresses browser/pause while setup calls it.
Normal run opens the fixed loopback URL only after successful startup/readiness.

No Windows software installer, Super Admin grant, automatic test account, security
acceptance, volume deletion or production operation is included. Native Docker
Desktop execution is separate from the Windows stub tests; use CI evidence and
STATUS to see what was actually run. The API runtime container excludes test
dependencies, so use README's native/CI test commands rather than container pytest.

## Database configuration and lifecycle

Native API/Alembic requires an explicitly exported `DATABASE_URL`, using
`postgresql://` or `postgresql+psycopg://` with username, host and database.
Malformed/missing configuration fails with a generic startup error. CR-002A adds
explicit local SQLite and TLS PostgreSQL transport modes; see
[DATABASE_MODES.md](DATABASE_MODES.md) for native commands and restrictions.
PostgreSQL remains the default; there is no fallback. URL-encode password
characters when writing a native URL.
The `.env` file is loaded by Compose, not automatically by the native API/CLI.

Compose passes `POSTGRES_HOST=db`, `POSTGRES_USER`, `POSTGRES_PASSWORD` and
`POSTGRES_DB` as separate components. SQLAlchemy URL.create preserves special
password characters without string concatenation or manual escaping. Native
DATABASE_URL takes precedence if explicitly provided to a process; Compose does
not pass the host's native URL into containers. Never print resolved Compose
configuration with credentials; use `docker compose config --quiet`.

Each API worker creates one synchronous psycopg/SQLAlchemy pool on lifespan start,
without requiring DB connectivity just to stay live. Pool: five retained/five
overflow connections, two-second checkout and connection timeouts, pre-ping,
three-second statement timeout, echo off and parameters hidden. DB failures affect
readiness. Shutdown disposes the pool. A request session closes/rolls back pending
writes even on exceptions; domain services must explicitly commit transactions.
No background task may reuse a request session.

Compose retains P0-01's development DB owner credentials. This is not a production
role model. Before production, provision separate least-privilege runtime and
migrator roles, revoke unnecessary public/DDL privileges, enforce TLS/network
isolation and review RLS/backup/restore; no such production changes occur here.
Integration tests require CREATE DATABASE only for a test-only disposable cluster;
never grant that capability to a production runtime role.

## Migration commands and safe rollback

From `backend/`, with an exported URL for a database you own:

```sh
uv sync --locked
uv run --locked alembic upgrade head
uv run --locked alembic current
uv run --locked alembic check
```

Compose runs a one-off `migrate` service after PostgreSQL is healthy and before
the API starts. Failed migration prevents API startup. Each API worker does not
run migrations. Only one migration job should run per environment at a time.
For an explicit rerun: `docker compose run --rm migrate`.

The historical baseline `0001_infrastructure` owns no business objects. It initializes only
`alembic_version`. Its safe downgrade removes the version row, leaves the version
table, and never drops unrelated data:

```sh
uv run --locked alembic downgrade base
uv run --locked alembic upgrade head
uv run --locked alembic check
```

Current head `0002_identity` creates global identity/session/attempt/audit tables.
It allows downgrade only when all four tables are empty and checked online;
otherwise it refuses before any drop and retains the revision/history. Never delete
identity or audit rows just to force a downgrade. Use backup/restore or a reviewed
forward fix after real data exists. Tests verify refusal/data preservation.

Run downgrade tests only on disposable databases. Future migrations must specify
data-preserving expand/backfill/contract steps and rollback or forward-fix limits;
never assume future downgrades are safe. Review autogenerate output, including
metadata imports, before applying it. Runtime never calls Base.metadata.create_all.
The migration template rejects unimplemented downgrade logic instead of silently
pretending to restore data. Production migrations require explicit authorization.

`uv run --locked pytest -q -m integration` uses the explicitly configured test
PostgreSQL server. New migration/session tests create UUID-named `p0_02_*`
databases, migrate only those and drop only those in finally cleanup. The original
P0-01 test uses a session-temporary table in the input test DB. An unset URL fails,
never silently skips. A failed/abruptly killed test may leave a generated DB for
manual inspection; do not blanket-delete similarly named databases.

## Health and API error contract

| Route | Success | Dependency failure | Privilege |
|---|---|---|---|
| GET /api/bootstrap | Existing product/stage metadata | Independent of DB | Public, no business data |
| GET /api/health/live | 200 `{"status":"live"}` | Remains 200 during DB outage | Public, no business data |
| GET /api/health/ready | 200 `{"status":"ready"}` after SELECT 1 | Generic 503 | Public, no DB details |

For local account provisioning and native/Compose cookie configuration see README.
P1-01 APIs: POST /api/auth/login, GET /api/auth/me, POST /api/auth/logout/password.
Authentication events persist subject UUID, source/kind, request UUID and time;
they are not the financial audit ledger. Retain UUIDs/history on deactivation.
API sessions grant no company membership or business approval authority.
Cookie/origin/CSRF, throttle and MFA/production limits are specified in ADR-011.
Operational retention/cleanup for expired sessions, throttle windows and auth events
requires security/DPO policy; no blanket deletion command is provided.

Readiness proves a connection/query, not business schema, compliance or accounting
readiness. CI verifies migration head separately. No probes reveal host, user,
credentials, version or SQL/exception text. Invalid DB configuration prevents
startup; a correctly configured but unavailable DB allows live and fails ready.

API 404/405/422/500/503 errors use:

```json
{"error":{"code":"service_unavailable","message":"Service Unavailable","request_id":"00000000-0000-4000-8000-000000000000"}}
```

Status codes retain their meaning; Allow and WWW-Authenticate headers survive.
Validation errors omit input/field details; unexpected errors omit tracebacks.
Each response includes X-Request-ID. A single canonical lowercase hyphenated UUID
is accepted from the caller, otherwise a fresh UUID is generated. This is diagnostic
input, never proof of user/company authority. Supply it with a reproducible synthetic
case for debugging, rather than copying real employee/accounting payloads into logs.

## JSON logs and basic metrics design

The `manpower` application logger emits one JSON object per line to stdout. UTC
timestamp, level, fixed event and request_id are standard. request_completed adds
method, route template (or `unmatched`), status and duration_ms. request_failed
includes exception class only. database_unavailable reports no exception text.
Lifespan events have an empty request ID. Request IDs use per-request contextvars,
including concurrent requests. Never use raw URL/path/query values as log labels.

Documented/container Uvicorn entrypoints disable raw access logs. Framework startup
messages may still be plain text; application events are JSON. Keep SQLAlchemy echo
disabled. Do not turn on SQL parameter/body/header/exception-text logging against
real data. Diagnostic logs do not replace the future immutable financial audit log.

Derive request/error counts and latency distributions from request_completed,
grouped by bounded method, known route template and status. Use readiness probes
for availability; treat live as process health only. Never use request IDs, tenant
IDs or arbitrary paths as metric labels. No public metrics endpoint/exporter is
added. Production logging retention/access, probe limits, alerts and monitoring
backend require DPO/security/release-owner approval. Streaming/background work is
not implemented; a failure after response start can only terminate the response,
not replace already-sent headers/body with a new error envelope.

## Diagnostics

```sh
docker compose ps --all
docker compose logs --tail 100 api migrate
curl --fail http://127.0.0.1:8000/api/health/live
curl --fail http://127.0.0.1:8000/api/health/ready
```

On local failure, check exported variable names without printing their values,
DB process/network reachability, migration job exit status and safe request ID.
Never paste `.env`, raw `docker inspect` output or DB URLs into issue reports.

## Controlled account administration (P1-01)

Migrate before starting the new API. Revision 0003 expands identity tables only;
old users remain active/inactive as before and gain no administrator capability.
Old application readers can ignore the added columns/tables. Roll back code first
if needed, retaining schema; downgrade refuses new security history/admin grants.
Do not erase audit history or force downgrade. No production execution authorized.

From `backend/` with an explicitly configured development database:

```sh
uv run --locked python -m app.identity.cli bootstrap-admins first.admin second.admin
```

Compose equivalent: `docker compose exec api .venv/bin/python -m app.identity.cli bootstrap-admins first.admin second.admin`.
Use an interactive terminal (not `exec -T`); each operator enters and confirms their
own passphrase without echo. No password arguments/env defaults. Both usernames
must be distinct and unused. One transaction creates both technical admins or
neither; bootstrap refuses if any admin exists, including a disabled one. Repeating
it cannot elevate an existing user. The ordinary create-user CLI grants no admin
capability. Database/server access is already privileged; protect it with operator
access control, independent custody and monitored recovery before production.

Initial API operator surface is the local OpenAPI documentation or a trusted
same-origin API client. Admin A and Admin B must use separate browser profiles or
cookie jars. Sign in through POST `/api/auth/login`; GET `/api/auth/me` supplies a
session-bound CSRF value. Use `X-CSRF-Token`, the session cookie and matching
browser Origin on every administrative mutation. Never put credentials in shell
arguments, request URLs, tickets, screenshots, traces or browser localStorage.

1. Admin A POSTs `/api/auth/admin/requests` with `username`, `action` and
   `current_password`. Actions: register, activate, deactivate, reset_password,
   unlock. Register creates an inactive non-admin identity and activation request;
   no known initial password. The response supplies request and subject UUIDs.
2. Admin B GETs `/api/auth/admin/requests?offset=0` (50 pending/unexpired records,
   then offset=50, etc.; maximum offset 10000). Verify the canonical target username,
   UUID, action and requester independently. POST
   `/api/auth/admin/requests/{id}/approve` with `current_password` and own CSRF.
   Requester and target cannot approve. Both admins must still be active/current
   admins; requests expire in 24 hours. No API changes to technical admin capability.
3. Activate/reset approval returns `reset_token` once; deactivate/unlock returns
   null. Verify the account owner's identity through your approved private process
   and hand the token directly to that owner. It is a credential: do not record it
   in logs/tickets or send it through an unverified address. No email integration or
   automated identity verification is implemented. Lost response/token requires a
   new reset request and independent approval; approval replay cannot recover it.
4. Owner opens the app's labelled recovery form and enters token/new passphrase,
   or POSTs `/api/auth/reset-password` with `token` and `new_password`. Token expires
   after 15 minutes, is consumed once, and cannot log in by itself. Only its hash is
   stored. Sign in again after reset; no automatic session is created.

Issuance revokes current sessions and older recovery tokens; redemption, password
change/operator reset and deactivation invalidate remaining tokens/sessions.
Activation of a disabled identity invalidates its old password and requires token
recovery. Unlock clears only that login name's 5-attempt/15-minute window; it
doesn't activate an account, change credentials or bypass global 60/minute limits.
Administrative reauthentication uses the same name window; recovery uses a separate
fixed 5/15-minute bucket. Retry-After is returned on 429. Normal timed lockout expires
without administrator action. Preserve at least two active technical admins through
the API; exceptional operator recovery has separate privileged custody.

Audit events link actor, subject and change UUID to retained request/approval
evidence without storing secrets. Development DB owners can still alter tables or
triggers: production privilege separation/retention/monitoring remains required.
These admins cannot access company data or approve financial documents. Memberships,
scoped RBAC and financial Maker–Checker remain scheduled P1-02/P1-03. Password proof
is not MFA; ADR-011's MFA plan and human security acceptance remain outstanding.

The bootstrap pair is fixed for this slice; there is no API for adding/promoting
technical admins. Total loss/disablement of both admins requires a separately
reviewed operator recovery process before production. Do not use the ordinary
operator deactivation CLI on that pair during normal development operation.
