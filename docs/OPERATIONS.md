# Development infrastructure operations

P0-02 only. No production deployment, auth, tenant data or financial workflows.
Infrastructure decisions are indexed in `tasks/DECISIONS.md` and `docs/adr/`.

## Database configuration and lifecycle

Native API/Alembic requires an explicitly exported `DATABASE_URL`, using
`postgresql://` or `postgresql+psycopg://` with username, host and database.
Other drivers/SQLite and malformed/missing configuration fail with a generic
startup error. URL-encode password characters when writing a native URL.
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

The baseline `0001_infrastructure` owns no business objects. It initializes only
`alembic_version`. Its safe downgrade removes the version row, leaves the version
table, and never drops unrelated data:

```sh
uv run --locked alembic downgrade base
uv run --locked alembic upgrade head
uv run --locked alembic check
```

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
