# Database modes — CR-002A

PostgreSQL remains the production transactional database. SQLite is opt-in local
identity development only; future business modules have separate acceptance gates.
Native processes read environment variables; they do not automatically load `.env`.

| DATABASE_MODE | Configuration | Current support |
|---|---|---|
| postgres (default) | Existing PostgreSQL URL or POSTGRES_* components | Existing local/CI path, unchanged psycopg pool/locks |
| sqlite | APP_ENV=local or test, explicit sqlite URL | Native local files, migrated identity schema |
| supabase | Explicit PostgreSQL URL with sslmode=verify-full | TLS transport configuration only; live role/pooler/cloud validation in D |

No fallback between modes. Unknown modes, SQLite URLs in PostgreSQL mode and
SQLite staging/production fail closed. `AUTH_PROVIDER` defaults to `local`;
other values fail until the real provider integration in C. Supabase PostgreSQL
transport is independent of Supabase Auth. Never send a DATABASE_URL/password to
Vite/browser code. Use a provider CA via backend libpq `sslrootcert` when needed;
certificate verification is mandatory for the Supabase transport configuration.
Do not use transaction pooling yet: prepared statements, role separation and
serverless pool sizes are unverified until D. No hosted connection is claimed.

SQLite URLs resolve relative to the checkout, even from `backend`. Only `.db`,
`.sqlite` or `.sqlite3` files beneath the real, non-relocated `.local` directory
are accepted. URI/query/memory/network/outside/temp-checkout paths are rejected;
directories are created when constructing the engine. Keep the checkout on a
local disk outside cloud-synced/network folders (mapped network drives cannot be
reliably identified by pathname). Protect `.local` with your OS account permissions.
SQLite files are unencrypted and unsuitable for real employee/fiscal data.

Every SQLite connection enables foreign_keys, busy_timeout=10000ms, WAL; every
transaction uses BEGIN IMMEDIATE with explicit service commit / close rollback.
Reads serialize too. No application-level write retries are added. Shutdown all
processes before file operations; don't copy just a live WAL database file. Safe
backup/restore tooling is B, data transfer is E, neither is implemented in A.
SQLite migrations require online data verification; offline SQL generation is
explicitly rejected. PostgreSQL offline generation remains available.

Use Python **3.13.18**, uv **0.13.7**, locked dependencies. The managed runtime
tested locally bundles SQLite 3.53.1. SQLite WAL requires the WAL-reset fix:
3.51.3+, or the 3.50.7/3.44.6 backport series; other runtimes fail before opening
the file. This patch pin changes the former 3.13 minor-only preference because
the old local Python 3.13.12 bundled affected SQLite 3.50.4.
[Upstream advisory](https://www.sqlite.org/wal.html#the_wal_reset_bug).

## Manual Windows native setup (phase A)

Install Node 24/npm and Python/uv. In a PowerShell at repository root:

```powershell
$env:UV_PYTHON_INSTALL_DIR=Join-Path (Get-Location) '.tools\python'
uv python install 3.13.18 --no-bin --no-registry
$env:APP_ENV='local'
$env:DATABASE_MODE='sqlite'
$env:DATABASE_URL='sqlite:///./.local/manpower_erp.db'
$env:AUTH_PROVIDER='local'
$env:AUTH_ORIGIN='http://127.0.0.1:5173'
$env:AUTH_COOKIE_SECURE='false'
cd backend
uv sync --locked --managed-python
uv run --locked alembic upgrade head
uv run --locked alembic check
uv run --locked python -m app.identity.cli create-user test-user
uv run --locked uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

The CLI uses hidden confirmed passwords (15–128 characters); ordinary test users
gain no administrator/company grants. In a second PowerShell, from the root:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Check /api/health/live and /api/health/ready at port
8000; sign in through the existing frontend. Ctrl+C stops each foreground process.
The `.env.sqlite.example` is a reference, not an automatic loader. Don't overwrite
an existing Docker `.env`. **Root setup.bat/run.bat still require Docker**; the
nine Docker-free BAT commands are phase B, after A acceptance.

From `backend`, `uv run --locked pytest -q -m "not integration"` needs no Docker
or PostgreSQL. SQLite tests create/remove only their own temporary directories
inside `.local`. Existing PostgreSQL integration tests require an explicit
disposable-test-server URL with CREATEDB authority; their fixture creates/drops
UUID-named databases and never migrates the input database. See OPERATIONS.
