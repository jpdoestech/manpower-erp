# Manpower ERP

Philippine manpower accounting ERP. P0-01 provides a local React/TypeScript page,
FastAPI API and PostgreSQL development database. P0-02 adds SQLAlchemy sessions,
Alembic migration history, health checks and safe JSON diagnostics. Business modules and
accounting/tax rules are not implemented yet. P1-01 adds operator-provisioned users,
password sign-in and revocable cookie sessions; MFA is planned, not implemented.
The P1-01 follow-up adds technical administrator approval and expiring recovery;
see [account administration](docs/OPERATIONS.md#controlled-account-administration-p1-01).

Read [AGENTS.md](AGENTS.md), [the roadmap](tasks/ROADMAP.md),
[status/evidence](tasks/STATUS.md) and [decisions](tasks/DECISIONS.md) before changes.

## Fresh checkout with Docker

CR-002A adds an opt-in **Docker-free SQLite** path with manual commands:
[database modes and Windows setup](docs/DATABASE_MODES.md#manual-windows-native-setup-phase-a).
Use Python 3.13.18 (patched SQLite WAL runtime). Existing root BAT files below
still use Docker; native BAT tooling is CR-002B after A acceptance. Supabase Auth,
cloud deployment and transfer are later phases, not implemented here.

On Windows, use the root BAT files after installing/starting Docker Desktop in
Linux-container mode:

1. Double-click **setup.bat**. It creates `.env` only if absent, with a random local
   database password and matching native URL. Existing settings are preserved.
   It builds/starts the stack, runs migrations and waits for health checks. Choose
   Y to create an ordinary test account; username and hidden password prompts use
   the existing operator CLI. No default account or administrator grant is created.
2. Double-click **run.bat** on later runs. It builds/starts the same stack, waits for
   readiness and opens [the app](http://127.0.0.1:5173). Closing the BAT window keeps
   containers running. Rerunning setup is safe; choose N to retain existing accounts.

Both scripts locate the repository regardless of the launching directory, use the
local default Docker context, and pin `compose.yaml`, `.env` and project name
`manpower-erp`. They do not install Docker, delete volumes or reset credentials.
If an existing `.env` is invalid/has a blank password, edit it and rerun setup;
changing the file does not change a password in an existing database volume.
PowerShell generates the initial local DB secret without displaying it. Keep
`.env` private and ignored. [Docker CLI context options](https://docs.docker.com/reference/cli/docker/)
take precedence over context environment settings. These helpers are local tooling;
P1-01 still awaits human security acceptance and P1-02 remains planning only.

To stop this local stack while keeping its data:

```powershell
docker --context default compose -f compose.yaml --env-file .env -p manpower-erp stop
```

The equivalent manual setup follows.

Install Git and Docker with Compose v2 (`docker compose version`). On Windows use
Docker Desktop with Linux containers. Run from the repository root:

```powershell
git clone https://github.com/jpdoestech/manpower-erp.git
cd manpower-erp
Copy-Item .env.example .env
```

On macOS/Linux replace `Copy-Item` with `cp`. Edit `.env`: set `POSTGRES_PASSWORD`
to a unique local password and match it in `DATABASE_URL` (URL-encode special
characters in the URL). A blank password deliberately prevents Compose startup.
These credentials are for disposable local data only. `.env` is ignored by Git.

```sh
docker compose config --quiet
docker compose up --build --wait
```

Open [the application](http://127.0.0.1:5173),
[bootstrap metadata](http://127.0.0.1:8000/api/bootstrap) and
[OpenAPI documentation](http://127.0.0.1:8000/docs).
The page should show **API connected**. That message confirms the API response;
it does not check database readiness. Check [readiness](http://127.0.0.1:8000/api/health/ready)
and [liveness](http://127.0.0.1:8000/api/health/live) separately. Compose runs migrations
before API startup and probes readiness. Current head adds global identity tables;
there are no company or financial tables.

```sh
docker compose ps
docker compose logs --tail 100
docker compose down
docker compose up --wait
```

`down` preserves the named PostgreSQL volume; `stop`/`start` also preserve it.
Do not add `--volumes` to `down` unless you intend to delete this local database.
Changing the password in `.env` does not update an already initialized database.
Services publish only on `127.0.0.1` (5432/8000/5173); free those ports first if
another local database or app uses them. Rebuild after source/dependency changes
with `docker compose up --build --wait`. The Compose web server is for development.

## Native development with hot reload

Install Python 3.13, Node 24/npm, and uv **0.13.7**
(`python -m pip install uv==0.13.7`). Versions are recorded in
`backend/.python-version` and `.node-version`. Language dependencies are locked;
use `uv sync --locked` and `npm ci`, not unlocked installs for verification.

Start just PostgreSQL with `docker compose up -d --wait db`, or use a separate
local PostgreSQL 18 database you own. Never point the tests at a shared database.
The bootstrap API serves static metadata without opening a DB connection. The API
process now requires valid database configuration at startup; unavailable PostgreSQL
fails readiness while liveness remains available. Native API/Alembic do not load
`.env` automatically. Export DATABASE_URL in terminal 1 before running the commands
below (PowerShell: `$env:DATABASE_URL = 'postgresql://USER:PASSWORD@127.0.0.1:5432/DB'`;
bash: `export DATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:5432/DB'`).
Use your own local database credentials and URL-encode special password characters.

Terminal 1:

```sh
cd backend
uv sync --locked
uv run --locked alembic upgrade head
uv run --locked uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Terminal 2:

```sh
cd frontend
npm ci
npm run dev
```

Vite proxies `/api` to `127.0.0.1:8000`, avoiding a permissive CORS configuration.
Compose changes the internal proxy target to `http://api:8000`.

## Local account access (P1-01)

No default account or public signup exists. After `alembic upgrade head`, an
authorized local operator can provision a test account from `backend/` with its
explicitly exported local DATABASE_URL:

```sh
uv run --locked python -m app.identity.cli create-user your.username
uv run --locked python -m app.identity.cli reset-password your.username
uv run --locked python -m app.identity.cli deactivate-user your.username
uv run --locked python -m app.identity.cli bootstrap-admins first.admin second.admin
```

For Compose: `docker compose exec api .venv/bin/python -m app.identity.cli create-user your.username`.

`bootstrap-admins` is one-time provisioning of two distinct technical administrators,
with each password entered and confirmed in hidden prompts. It grants no company
access. Existing CLI commands are privileged operator recovery; routine account
registration/activation/reset/deactivation uses independent administrator approval
through the documented API. See OPERATIONS for verified private recovery delivery.
Passwords are prompted twice with hidden input (15–128 characters). Never put a
password in command arguments/history, source or logs. Usernames are normalized
lowercase ASCII, 3–64 characters; begin with a letter, then letters/digits/._-.
Deactivation preserves identity/audit history. Reset/deactivation revoke sessions;
reset does not reactivate a disabled user. No operator command grants company roles.

The page offers sign-in, sign-out and current-password change. Successful password
change ends all sessions and requires sign-in again. Sessions are HttpOnly and
SameSite=Strict; no browser localStorage token. API errors remain generic.
Login attempts are limited across workers (5/name/15 min, 60 total/minute).

For native **local HTTP** development, export `AUTH_COOKIE_SECURE=false` and
`AUTH_ORIGIN=http://127.0.0.1:5173` before starting the API. In PowerShell use
`$env:AUTH_COOKIE_SECURE='false'`; bash uses `export AUTH_COOKIE_SECURE=false`.
Compose reads these from `.env.example` after you copy it to `.env`. Secure cookies
are the server default; disabling Secure is rejected for non-loopback origins.
Use the configured 127.0.0.1 origin consistently. HTTPS deployment/security/MFA
policy needs separate approval; this is not production-ready authentication.

Current head `0003_account_controls` adds only identity administration/recovery to
the global auth tables introduced in `0002_identity`. Downgrade refuses security
history/grant loss, populated identity tables and offline
SQL downgrades. Do not erase accounts/audit rows to bypass that guard. Restore or
forward-fix planning is required once identity data exists. See ADR-011.

## Contributor checks (same gates as CI)

The runtime API image installs with `--no-dev`; it does **not** contain pytest or
test files. Use the native commands below for backend tests, or the GitHub Actions
backend job with its disposable PostgreSQL service. Do not run container pytest.
Frontend tests use the native frontend commands below or the frontend CI job.

Windows BAT orchestration regression checks use the actual Windows shell with a
disposable Docker stub (no real containers, credentials or browser are launched):

```powershell
python -m unittest discover -s scripts/tests -p test_windows_launchers.py -v
```

From `backend/`:

```sh
uv sync --locked
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy app tests alembic
uv run --locked pytest -q -m "not integration"
uv run --locked pip-audit
```

For the database test, set `DATABASE_URL` explicitly to a disposable PostgreSQL 18
database. In PowerShell: `$env:DATABASE_URL = 'postgresql://USER:PASSWORD@127.0.0.1:5432/TEST_DB'`.
In bash: `export DATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:5432/TEST_DB'`.
Use your own local credentials; `.env` is consumed by Compose, not automatically
loaded by pytest. Then run:

```sh
uv run --locked pytest -q -m integration
```

An unset URL fails integration tests rather than silently skipping them. Migration
and session tests create/drop UUID-named disposable databases on that test server;
the test-only role needs CREATE DATABASE. The original test uses a session-local
temporary table. No ERP domain tables are created in the configured input database.
Never point tests at production or grant database-creation rights to runtime roles.

To verify the current migration CLI on an owned **empty** disposable database:

```sh
uv run --locked alembic upgrade head
uv run --locked alembic check
uv run --locked alembic downgrade base
uv run --locked alembic upgrade head
uv run --locked alembic check
```

The baseline owns no business data; identity downgrade refuses populated tables.
Future downgrades need individual safety review. See [operations](docs/OPERATIONS.md) for lifecycle, configuration, migration
rollback, health/error contracts and log-derived metrics design; see
[ADRs](tasks/DECISIONS.md) for pending stakeholder/CPA decisions.

From `frontend/`:

```sh
npm ci
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
npm audit --audit-level=low
```

Format edits using `uv run --locked ruff format .` in backend and `npm run format`
in frontend. When intentionally updating Python dependencies, run `uv lock` then
`uv sync --locked`; npm updates must include `package-lock.json`. Rerun audits
and relevant checks. Never commit `.env`, credentials, dependency directories,
database clusters or logs.

CI also boots Compose from scratch, checks the web/proxied API and health over
HTTP, stops PostgreSQL to prove live/ready distinguish an outage, checks recovery,
then recreates containers and verifies the same database cluster identifier survives.
CI uses disposable service credentials and deletes its own test volumes at the end.
Hosted CI results require a real GitHub run; see STATUS for what was actually run.

No production deployment or compliance approval is implied by this bootstrap.
