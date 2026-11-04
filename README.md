# Manpower ERP

Philippine manpower accounting ERP. P0-01 provides a local React/TypeScript page,
FastAPI API and PostgreSQL development database. P0-02 adds SQLAlchemy sessions,
Alembic migration history, health checks and safe JSON diagnostics. Business modules,
authentication and accounting/tax rules are not implemented yet.

Read [AGENTS.md](AGENTS.md), [the roadmap](tasks/ROADMAP.md),
[status/evidence](tasks/STATUS.md) and [decisions](tasks/DECISIONS.md) before changes.

## Fresh checkout with Docker

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
before API startup and probes readiness. The baseline creates only migration history.

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

## Contributor checks (same gates as CI)

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

To verify the baseline CLI on an owned disposable database:

```sh
uv run --locked alembic upgrade head
uv run --locked alembic check
uv run --locked alembic downgrade base
uv run --locked alembic upgrade head
uv run --locked alembic check
```

The no-op baseline owns no business data; future downgrades need individual safety
review. See [operations](docs/OPERATIONS.md) for lifecycle, configuration, migration
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
