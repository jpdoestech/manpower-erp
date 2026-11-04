# Project Status — Codex Must Maintain

Last updated: 2026-11-04
Current milestone: P0-02
Current task status: REVIEW (local checks pass; P0-02 hosted CI pending)
Repository inspected: YES; feature/p0-02-infrastructure from clean main b3517d3, matching origin
Implemented code: P0-01 bootstrap plus P0-02 sessions/migrations/health/diagnostics; no business workflows or domain schema
Validated requirements: P0-02 local tests, migration round trips, static checks, audits and Compose/CI syntax; hosted runtime gate pending

## Latest outcome
- P0-02 requested; clean main `b3517d3` matched origin and the reported scaffold.
  Created `feature/p0-02-infrastructure`; plan/tests are in `tasks/P0-02.md`.
  Reviewed all mandatory docs, source, lockfiles, Compose and CI; detailed ADRs
  recorded before implementing infrastructure. P0-01 evidence below is historical.
- Added SQLAlchemy 2.1.7/Alembic 1.20.1; all existing locked versions retained.
  The baseline creates only Alembic history; clean/repeated upgrade, drift check,
  safe downgrade/re-upgrade and unrelated-row preservation pass on disposable DBs.
- Added request sessions/pool disposal, live/ready separation, safe consistent
  errors, UUID correlation and whitelisted JSON logs. Frontend behavior unchanged.
- Local backend/frontend verification passed; task remains REVIEW until hosted CI
  verifies migration service, Docker boot and DB outage/recovery/persistence.

## Next task / limits

Finish P0-02 hosted checks and PR; do not merge automatically. Recommend **P1-01**
only after P0-02 completion and a separate user request. No P1-01 work started.
CPA rounding/tax/GL policies, stakeholder hierarchy/role/delegation decisions and
production deployment/permissions remain unapproved; see ADRs. Runtime Compose
credentials remain development-only. Local Windows Docker engine is unavailable.

## P0-02 exact verification (2026-11-04)

Backend commands executed from `backend/` using `..\.tools\Scripts\uv` (uv 0.13.7,
Python 3.13.12). DATABASE_URL explicitly targeted isolated loopback PostgreSQL 18.3
on port 55432, ignored `.local/p0-02-postgres-data`. New tests create/drop only
generated disposable databases; the original input DB is not migrated.

| Command | Final local result |
|---|---|
| `..\.tools\Scripts\uv sync --locked` | PASS; 63 resolved, 61 checked on Windows |
| `..\.tools\Scripts\uv lock --check` | PASS; manifest/lock agree |
| `..\.tools\Scripts\uv run --locked ruff format --check .` | PASS; 13 files |
| `..\.tools\Scripts\uv run --locked ruff check .` | PASS after formatting/import cleanup |
| `..\.tools\Scripts\uv run --locked mypy app tests alembic` | PASS; 13 source files |
| `..\.tools\Scripts\uv run --locked pytest -q` | PASS; 36 tests, no warnings; original P0-01 tests preserved |
| `..\.tools\Scripts\uv run --locked pip-audit` | PASS; no known vulnerabilities |
| `..\.tools\Scripts\uv run --locked alembic upgrade head` (twice), `alembic check`, `alembic current`, `alembic downgrade base`, `alembic upgrade head`, `alembic check` (all prefixed `..\.tools\Scripts\uv run --locked`) | PASS on newly generated disposable CLI DB; head 0001_infrastructure; no upgrade operations detected; DB dropped after checks |
| `npm ci` (frontend) | PASS; 108 added, 109 audited |
| `npm run format:check` (frontend) | PASS; 9 files |
| `npm run lint` (frontend) | PASS; 9 files |
| `npm run typecheck` (frontend) | PASS; tsc exits 0 |
| `npm test` (frontend) | PASS; 5 tests |
| `npm run build` (frontend) | PASS; tsc/Vite 8.3.5, 16 modules |
| `npm audit --audit-level=low` (frontend) | PASS; 0 vulnerabilities |
| `.\.tools\docker-compose.exe config --quiet` (root; process-local test password) | PASS; Compose 5.7.0 |
| `.\.tools\actionlint\actionlint.exe .github/workflows/ci.yml` (root) | PASS; actionlint 1.7.12 |
| `git diff --check` | PASS |

Compared HEAD's uv.lock to the new lock using Python tomllib: **no previous package
version changed**; only sqlalchemy, alembic, mako and markupsafe were added.
Offline SQL generation is tested without connecting or disclosing credentials.
Migration tests prove only alembic_version exists after clean initialization,
single head/idempotence, downgrade safety and preservation of an unrelated row.
Session tests prove rollback-on-close/exception and explicit-commit persistence.

Initial issues resolved before delivery: Ruff formatting/import order and strict
test typing; two log-capture tests initially bound a pytest phase stream, corrected
to a stable StringIO using the real configured JSON handler. Added Alembic's
path_separator=os to remove deprecation warnings. No failed attempt counted as pass.

Hosted CI/PR evidence: pending push and real run. No production migration/deploy.
Tenant/RBAC/Maker–Checker/financial tests are N/A without business records/workflows;
architecture documentation does not certify implementation of those controls.

## P0-02 changed files

- Runtime/config: `.env.example`, `backend/app/main.py`, `backend/app/database.py`,
  `backend/app/observability.py`, `backend/pyproject.toml`, `backend/uv.lock`,
  `backend/Dockerfile`, `compose.yaml`, `.github/workflows/ci.yml`.
- Migrations: `backend/alembic.ini`, `backend/alembic/env.py`,
  `backend/alembic/script.py.mako`, `backend/alembic/versions/0001_infrastructure_baseline.py`.
- Tests: `backend/tests/conftest.py`, `backend/tests/test_api.py`,
  `backend/tests/test_configuration.py`, `backend/tests/test_diagnostics.py`,
  `backend/tests/test_migrations.py`, `backend/tests/test_sessions.py`.
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY_RBAC.md`,
  `docs/OPERATIONS.md`, seven ADRs (001/002/003/005/006/009/010) under `docs/adr/`,
  `tasks/P0-02.md`, `tasks/STATUS.md`, `tasks/DECISIONS.md`.

## Historical P0-01 outcome

- Read all mandatory documents and wrote `tasks/P0-01.md` before coding.
- Original starter-pack report matched the code. The folder initially lacked Git;
  after the user initialized it, inspection found a clean governance-only commit.
  Git initialization also supplied `.gitattributes`; it now enforces LF on checkout.
- Added a minimal React/TypeScript page, public FastAPI bootstrap contract,
  PostgreSQL integration test, locked dependencies, lint/types/tests, local Compose,
  CI and contributor instructions. No accounting/business modules implemented.
- ADR-001 adopted for local bootstrap only; access surface documented in SECURITY_RBAC.
- Native HTTP smoke and browser inspection show the page and **API connected**.
  The bootstrap endpoint is static metadata, not a DB health check.
- All runnable local checks pass. The user subsequently authorized commit/push;
  implementation commit `f0c60ea0fed74edb56ba29bd29419a151b8be828` was pushed to main.
- Hosted [CI run 41749669989](https://github.com/jpdoestech/manpower-erp/actions/runs/41749669989)
  completed successfully on 2026-11-04: **backend**, **frontend**, and **compose**
  jobs all passed. Docker build/start, HTTP smoke and database volume persistence
  are now verified on the Linux runner. P0-01 is DONE; no P0-02 work started.
- No production deployment or production data changes were performed.

P0-01's next-task handoff was P0-02, which is the current authorized task above.

## Task evidence log
| Task | Date | Change / commit | Checks executed | Result | Reviewer |
|---|---|---|---|---|---|
| P0-01 | 2026-11-04 | f0c60ea; pushed to main | Commands below, `tasks/P0-01.md`, CI run 41749669989 | PASS; all acceptance gates, including hosted Docker boot/persistence | Automated checks; no human review claimed |
| P0-02 | 2026-11-04 | Feature branch; implementation delivery pending | P0-02 commands above | Local gates PASS; hosted CI pending | Automated local checks; no human review claimed |

## Historical P0-01 verification commands and results

Host: Windows, Node **24.14.1**, npm **11.19.1**, Python **3.13.12**, uv **0.13.7**,
isolated PostgreSQL **18.3**. uv was installed into the ignored `.tools` venv.
Backend commands used `..\.tools\Scripts\uv` from `backend/`. A fresh environment
was selected using `$env:UV_PROJECT_ENVIRONMENT='../.local/clean-backend'`.

| Directory | Exact command | Final result |
|---|---|---|
| backend | `..\.tools\Scripts\uv sync --locked` | PASS; fresh venv, 57 packages installed, 59 resolved across platforms |
| backend | `..\.tools\Scripts\uv lock --check` | PASS; lock matches manifest |
| backend | `..\.tools\Scripts\uv run --locked ruff format --check .` | PASS; 4 files already formatted |
| backend | `..\.tools\Scripts\uv run --locked ruff check .` | PASS; All checks passed |
| backend | `..\.tools\Scripts\uv run --locked mypy app tests` | PASS; no issues in 4 source files |
| backend | `..\.tools\Scripts\uv run --locked pytest -q -m 'not integration'` | PASS; 7 passed, 1 deselected; no warnings |
| backend | `..\.tools\Scripts\uv run --locked pytest -q -m integration` | PASS; 1 passed, 7 deselected; no warnings |
| backend | `..\.tools\Scripts\uv run --locked pip-audit` | PASS; No known vulnerabilities found |
| frontend | `npm ci` | PASS; 108 packages added, 109 audited |
| frontend | `npm run format:check` | PASS; Biome checked 9 files |
| frontend | `npm run lint` | PASS; Biome recommended rules, warnings fail, 9 files |
| frontend | `npm run typecheck` | PASS; tsc exits 0 |
| frontend | `npm test` | PASS; 1 file, 5 tests |
| frontend | `npm run build` | PASS; tsc + Vite 8.3.5, 16 modules; output in ignored dist |
| frontend | `npm audit --audit-level=low` | PASS; 0 vulnerabilities |
| root | `.\.tools\docker-compose.exe config --quiet` | PASS with process-local POSTGRES_PASSWORD; Compose 5.7.0 standalone |
| root | `.\.tools\docker-compose.exe config --format json` | PASS; asserted db/api/web published host_ip equals 127.0.0.1 |
| root | `.\.tools\docker-compose.exe config --quiet` with password unset | Expected nonzero; missing-password configuration rejected |
| root | `.\.tools\docker-compose.exe up --build --wait --wait-timeout 180` | NOT PASSED; Docker engine named pipe does not exist |
| root | `.\.tools\actionlint\actionlint.exe -color .github/workflows/ci.yml` | PASS; actionlint 1.7.12 exits 0; no hosted execution implied |
| root | `git diff --check` | PASS; exit 0 |
| root | `git check-ignore .env .local/p0-01-postgres-data/PG_VERSION backend/.venv/pyvenv.cfg frontend/node_modules/react/package.json .tools/docker-compose.exe` | PASS; all ignored |
| hosted CI | `backend` job: locked install, Ruff, mypy, API tests, PostgreSQL integration, pip-audit | PASS; run 41749669989, job 126311356836 |
| hosted CI | `frontend` job: npm ci, format/lint/types/tests/build/audit | PASS; run 41749669989, job 126311356732 |
| hosted CI | `compose` job: `docker compose config --quiet`, `docker compose up --build --wait --wait-timeout 180`, HTML/proxy assertions, `docker compose down`, `docker compose up --wait --wait-timeout 180`, cluster identifier comparison | PASS; run 41749669989, job 126311356501; test volume cleaned up |

Database test environment: `$env:DATABASE_URL='postgresql://postgres@127.0.0.1:55432/postgres'`.
An isolated cluster was initialized under ignored `.local/p0-01-postgres-data`
using `initdb.exe -D .local/p0-01-postgres-data -U postgres --auth=trust --encoding=UTF8 --locale=C`.
Only loopback port 55432 was bound with `pg_ctl.exe -D .local/p0-01-postgres-data -l .local/postgres.log -o '-h 127.0.0.1 -p 55432' -w start`.
This test-only cluster contains no real records and is now stopped; native API
and Vite processes were also stopped after verification.

HTTP checks: ran `uv run --locked uvicorn app.main:app --host 127.0.0.1 --port 8000`
and `npm run dev`; Python urllib assertions verified the HTML title at port 5173
and exact `{name: 'Manpower ERP', stage: 'bootstrap'}` JSON through its `/api/bootstrap`
proxy. Browser AX/screenshot inspection confirmed visible heading and connected
status. See P0-01.md for the full HTTP assertion command.

Migration review: no SQL/migration files or domain schema were introduced. A
psycopg inspection of `information_schema.tables` confirmed **0 public tables**
after integration testing. Migration up/down is N/A until P0-02. Tenant/RBAC,
Maker–Checker and financial reconciliation tests are N/A for this metadata-only
bootstrap; these controls are not implemented or claimed to pass.

Earlier findings resolved: initial Ruff line-length issues were formatted; initial
ESLint/minimatch audit reported 11 moderate findings, removed by using Biome;
Starlette's httpx deprecation was removed by using httpx2. An optional native psql
schema-inspection command could not execute (invalid OS executable); the equivalent
inspection passed using psycopg. No failed check is counted as a pass.

## Changed files

- Root: `.gitattributes`, `.gitignore`, `.dockerignore`, `.env.example`,
  `.node-version`, `compose.yaml`, `README.md`, `.github/workflows/ci.yml`.
- Backend: `backend/.python-version`, `backend/pyproject.toml`, `backend/uv.lock`,
  `backend/Dockerfile`, `backend/app/__init__.py`, `backend/app/main.py`,
  `backend/tests/test_api.py`, `backend/tests/test_database.py`.
- Frontend: `frontend/package.json`, `frontend/package-lock.json`,
  `frontend/tsconfig.json`, `frontend/biome.json`, `frontend/vite.config.ts`,
  `frontend/Dockerfile`, `frontend/index.html`, `frontend/src/main.tsx`,
  `frontend/src/App.tsx`, `frontend/src/style.css`, `frontend/src/App.test.tsx`,
  `frontend/src/test-setup.ts`.
- Governance: `docs/SECURITY_RBAC.md`, `tasks/P0-01.md`, `tasks/DECISIONS.md`,
  `tasks/STATUS.md`, `AGENTS.md` (standing commit/push preference).

## Open blockers / compliance decisions
- Confirm legal entity types (labor service cooperative vs corporation), tax status and approved CPA treatments per company.
- Confirm company scope and branch establishment registration model.
- Confirm exact document series and invoice design with tax reviewer.
- Local Docker engine absent; container builds, volume persistence and Linux runtime
  passed on hosted CI. Windows Docker Desktop execution remains unverified. Branch
  protection is not configured/verified. Commit/push explicitly authorized by user.
- Production deployment/secrets remain undecided. Base image tags can receive patches;
  this is locked language dependency installation, not byte-reproducible OS images.

## Session handoff template
- Goal:
- Files changed:
- Schema/API changes:
- Tests and exact outputs:
- Security/accounting impacts:
- Known limitations:
- Next task ID:
