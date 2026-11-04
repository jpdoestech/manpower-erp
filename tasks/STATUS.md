# Project Status — Codex Must Maintain

Last updated: 2026-11-04
Current milestone: P0-01
Current task status: REVIEW (container boot/persistence and hosted CI pending)
Repository inspected: YES; initial commit 99cd935, origin https://github.com/jpdoestech/manpower-erp.git
Implemented code: P0-01 local bootstrap only; no business workflows or domain schema
Validated requirements: Local frozen installs, static checks, API/UI tests, PostgreSQL integration, HTTP smoke, Compose configuration and CI syntax

## Latest outcome
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
- All final runnable local checks pass. P0-01 is **not DONE**: no Docker engine is
  available, and no hosted CI execution has been performed. No commit/push/deploy
  was made during implementation. The user subsequently authorized commit/push;
  see Git history for delivery. Production deployment remains unauthorized.

## Next Codex actions
1. Finish P0-01 gates on a Docker-enabled host: Compose clean build/start, HTTP smoke
   and volume persistence. The CI Compose job encodes these checks.
2. Observe an actual GitHub CI run after the changes are published by an authorized
   user; commit/push now has standing user authorization. Do not treat static
   workflow validation as a hosted pass.
3. Only after P0-01 is accepted, P0-02 is next. It was not started here.

## Task evidence log
| Task | Date | Change / commit | Checks executed | Result | Reviewer |
|---|---|---|---|---|---|
| P0-01 | 2026-11-04 | Working tree; no new commit | Commands below and `tasks/P0-01.md` | Local gates pass; Docker engine/hosted CI pending | Not yet reviewed |

## Exact verification commands and results

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
  remain unverified here. Hosted CI and branch protection are not configured/verified
  remotely. Workflow and remote URL exist; commit/push explicitly authorized by user.
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
