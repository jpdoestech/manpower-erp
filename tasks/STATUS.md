# Project Status — Codex Must Maintain

Last updated: 2026-11-04
Current requested milestone: P1-02 (prerequisite audit/planning only)
Current task status: BLOCKED at prerequisite; P1-01 remains REVIEW pending human security acceptance
Repository inspected: YES; fetched main b3517d3, P0-02 4fd3914, P1-01 dc7fca3; clean before new branch
Implemented code: existing P0/P1 foundations plus technical account administration/recovery follow-up; no company/finance modules
Validated requirements: follow-up 5ca0ad3 has 6/6 hosted checks, 92 backend/13 frontend tests, migrations and Docker gates pass

## P1-02 prerequisite audit and plan

Latest request authorizes P1-02 subject to verified prerequisites; explicitly says
not to bypass security acceptance or merge automatically. Fetch confirms unchanged
main b3517d3 and feature heads 4fd3914/dc7fca3/37dbd7f. Working tree was clean.
Inspected all three PRs and mandatory docs, actual API/security/migration/test/CI
surfaces. Fresh connected-account diagnostics report 6/6 successful checks at each
exact head. PR #1 targets main; #2 targets P0-02; #3 targets P1-01 foundation. All
remain open/unmerged. P1-01 #2/#3 show No reviews; STATUS/ADRs still require human
security acceptance. Task authorization is separate from prerequisite acceptance.

Ancestry verifies the complete P0/P1 stack in 37dbd7f but not in origin/main. No
integration or merge performed. Created feature/p1-02-organizations from 37dbd7f
for audit/plan documents only. `tasks/P1-02.md` contains the pre-code plan, acceptance
cases, intended files, exact prerequisite CI links and missing approval evidence.
ADR-013 is PROPOSED ONLY; architecture/index updated without changing adopted
company/security/tax policy. Asked for the recorded P1-01 reviewer/decision.

No organization schema/migration/API/UI, grant or P1-02 automated test exists yet.
No production work or P1-03. Matching-head hosted prerequisite results reused;
no fresh local application-test run is claimed for these documentation edits.
Next safe action: record actual P1-01 security acceptance, verify chosen base after
fresh fetch, then implement P1-02 and its full automated gates. P1-03 follows only
after completed/accepted P1-02 and separate authorization.

## Current P1-01 CR-001 follow-up

Latest user request expands account controls. Actual source inspection confirms
P0-01/P0-02 acceptance implementations and original P1-01 foundation; main still
contains only P0-01. PRs #1/#2 remain open/unmerged. No duplicate bootstrap/infra.
New branch feature/p1-01-account-controls from dc7fca3, stacked on #2. Pre-code
plan/acceptance: tasks/P1-01-account-controls.md; CR-001/ADR-012 recorded before code.

Additive migration 0003, technical admin bootstrap, independent account requests,
single-use recovery and UI implemented. Final local gates: 92 tests in 55.76s;
after reactivation-password hardening, 19 account-control cases pass in 30.63s.
Frontend 13 tests, Ruff format/lint, strict mypy (26 files), Biome/tsc, build,
lock check, pip/npm audits, Compose configuration, actionlint and diff check pass.
Migration tests preserve 0002 user/session/audit rows and verify clean/repeat/drift/
safe downgrade/re-upgrade plus history/grant refusal. Concurrent approval/recovery/
bootstrap and server authorization tests pass. No dependency versions changed.

Exact commands, initial failures/corrections, changed-file ledger and limitations:
[P1-01-account-controls.md](P1-01-account-controls.md). Implementation commit
`5ca0ad3ab96e1e0fb3ea68f83ddc6302d5c061c3` in [PR #3](https://github.com/jpdoestech/manpower-erp/pull/3)
passes all six exact-head GitHub checks: [push CI 41765130592](https://github.com/jpdoestech/manpower-erp/actions/runs/41765130592)
and [PR CI 41765194928](https://github.com/jpdoestech/manpower-erp/actions/runs/41765194928).
PR backend logs: 50 unit/API passed (1.66s), 42 PostgreSQL integration passed
(13.79s). All source tests pass after final hardening. Migration CLI and Linux
Docker boot/authentication/outage/recovery/persistence pass. Existing Node/runner
annotations are non-failing maintenance notices. No lock/dependency changes.
Local probe via psycopg verifies 0 input public tables and 0 generated DBs remaining;
PostgreSQL stopped. Native psql unavailable; equivalent probe succeeded. Local
Windows Docker execution unavailable. Human security acceptance remains required. Initial
admin operator pair/manual private token delivery/MFA/production recovery and
permissions require review. No company grants, P1-02, merge or production deployment.
PR #3 stacks on #2; #1/#2 remain open. Next: review P1-01, then separately authorize
P1-02 after acceptance. Documentation-only evidence follows the verified source.

## Historical P1-01 foundation outcome (before CR-001)

- User explicitly authorized verify-and-continue. Fetch confirmed two existing local/
  remote branches, five commits, clean worktree, open PR #1 and no open issues.
  P0-02 existed in full on 4fd3914; main still ends at P0-01. GitHub UI confirms
  exact-head 6/6 checks; fresh local prerequisite run passed 36 tests, Ruff/mypy,
  pip-audit. Reviewed migrations, health/live-ready, logs/correlation/redaction,
  sessions, docs and CI against acceptance; no missing P0-02 code found.
- Created feature/p1-01-authentication from verified P0-02. No merge or duplication
  of P0-02. Planned/auth decisions before coding: tasks/P1-01.md and ADR-011.
- Added operator-only create/reset/soft-disable CLI, Argon2id, 8-hour opaque hashed
  sessions, login/me/logout/password APIs, CSRF/Origin protection and DB attempt
  windows. Password/reset/deactivation revoke sessions. No company/role authority.
- Auth audit records subject UUID/event/source/correlation/time. Trigger rejects
  UPDATE/DELETE/TRUNCATE; privileged DDL tampering is not prevented by dev setup.
  Migration refuses populated/offline downgrade; empty roundtrip/drift checks pass.
- Added compact account UI and MFA/security-approval plan. No signup/admin listing,
  MFA implementation, memberships/RLS/RBAC, approval or accounting workflows.
- Native HTTP smoke passed login/me/logout/replay through Vite/API on a generated
  disposable preview DB; browser verified bootstrap API connected and labelled form.
- Implementation `3e4bc828b5d0fbb9570b710576ceb51643fc6cb9` pushed to the stacked
  branch; [PR #2](https://github.com/jpdoestech/manpower-erp/pull/2) is open into
  feature/p0-02-infrastructure. PR #1 remains open into main. Neither was merged.
- Hosted [push CI 41759481411](https://github.com/jpdoestech/manpower-erp/actions/runs/41759481411)
  and [PR CI 41759551633](https://github.com/jpdoestech/manpower-erp/actions/runs/41759551633)
  pass backend/frontend/compose for the implementation. Native servers/PG cluster
  stopped, preview/test databases dropped, temporary credentials removed; input
  database still has zero public tables. No production data/deploy touched.

## P1-01 verification evidence (2026-11-04)

Host: Python 3.13.12, uv 0.13.7, Node 24.14.1/npm 11.19.1, PostgreSQL 18.3.
Backend commands run from backend using `..\.tools\Scripts\uv`; test DATABASE_URL
points to loopback 55432. New integration databases are generated and dropped by
the existing disposable fixture; no existing data or production migrations touched.

| Command | Result |
|---|---|
| `git fetch --all --prune`, `git branch -avv`, `git log --all --oneline --decorate -15`, `git ls-remote origin 'refs/pull/*'` | PASS; main b3517d3, P0-02 4fd3914, PR #1 head matches, no pre-existing uncommitted work |
| Prerequisite `uv sync --locked`, Ruff format/check, `mypy app tests alembic`, `pytest -q`, `pip-audit` | PASS; 36 tests, 13 typed/formatted files, audit clean |
| P1-01 `uv run --locked ruff format --check .`, `uv run --locked ruff check .` | PASS after formatting |
| `uv run --locked mypy app tests alembic` | PASS; 23 source files |
| `uv run --locked pytest -q` | PASS; 73 tests in 25.50s, no warnings |
| `uv run --locked pip-audit` / `uv lock --check` | PASS; no known vulnerabilities; graph locked |
| `npm run format:check`, `npm run lint`, `npm run typecheck` | PASS; 11 formatted/linted files; tsc exits 0 |
| `npm test` | PASS; 9 tests (5 original + 4 account-flow tests) |
| `npm run build` | PASS; 17 modules, Vite 8.3.5 |
| `npm audit --audit-level=low` | PASS; 0 vulnerabilities; frontend dependency graph unchanged |
| `python backend/tests/smoke_identity.py` with generated preview credentials in process env | PASS; HTTP login/me/logout/replay via http://127.0.0.1:5173; no credential output |
| `.\.tools\docker-compose.exe config --quiet` with process-local test password | PASS; includes safe cookie/origin configuration |
| `.\.tools\actionlint\actionlint.exe .github/workflows/ci.yml` | PASS; includes auth smoke before/after container recreation |
| `git diff --check` | PASS |
| Push CI 41759481411: backend job 126343491301, frontend 126343490882, compose 126343491154 | PASS; all three jobs |
| PR CI 41759551633: backend job 126343707641, frontend 126343707745, compose 126343707340 | PASS; all three jobs, compose 1m27s |

Hosted gates include clean/repeated upgrade/drift/empty downgrade/re-upgrade, all
backend/frontend checks and audits, and Docker HTTP authentication before and after
container recreation. Original bootstrap, dependency outage/recovery and persistent
cluster identifier checks also pass. CI evidence verified in authenticated GitHub
UI; no credentials were extracted for API polling. Documentation-only evidence
changes follow the verified implementation commit.

All previous Python lock versions retained (tomllib comparison to 4fd3914).
Only argon2-cffi 25.1.0, argon2-cffi-bindings 26.1.0, cffi 2.1.1, pycparser 3.12 added.
No frontend dependency added. Current-head migration tests independently verify
identity tables, repeat/check, empty downgrade/re-upgrade and populated refusal.
Historical no-schema baseline regression stays explicitly on 0001_infrastructure.
Tests also cover concurrent throttling, cookie/CSRF/Origin, cross-user self-only
identity, token replay/expiry/deactivation/reset/change and log redaction.

Initial issues corrected: the original frontend mock reused one Response body for
multiple requests; changed to fresh route-specific responses without weakening
bootstrap assertions. Ruff/import/test typing cleaned up. A transient Windows file
mapping blocked one CSS format write; rerun passed. No failed check counted as pass.

## Current next task / limits

Review stacked PR #2; merge nothing automatically. After PR #1 is reviewed/merged,
retarget #2 to main for separate security acceptance. P1-01 remains REVIEW under
ROADMAP's human-acceptance gate for high-risk changes. Recommend P1-02 only after
that gate and separate task authorization. PR #1 remains open into main.
Local Windows Docker engine unavailable; hosted Linux container/auth/persistence/
outage gates pass. MFA, breach-password blocklist, retention/edge throttling,
production roles/RLS/IdP/recovery and calibrated policies remain security review work.
No production readiness or financial-control certification. No production deployment.
Non-failing inherited CI annotations: checkout@v4 Node 20 metadata is deprecated
and GitHub forces it onto Node 24; ubuntu-latest is migrating to Ubuntu 26. These
are recorded for focused CI maintenance, with no unrelated action/runner upgrade
in this authentication slice. Dependency audits report zero known vulnerabilities.

## P1-01 changed files

- Auth: backend/app/identity/{__init__,models,security,service,routes,cli}.py;
  backend/app/main.py, backend/app/observability.py, backend/pyproject.toml, uv.lock.
- Migrations/tests: backend/alembic/env.py, versions/0002_identity.py;
  backend/tests/test_api.py, test_migrations.py, test_identity.py,
  test_identity_security.py, smoke_identity.py.
- UI: frontend/src/AuthPanel.tsx, AuthPanel.test.tsx, App.tsx, App.test.tsx, style.css.
- Delivery/docs: .env.example, compose.yaml, .github/workflows/ci.yml, README.md,
  docs/OPERATIONS.md, SECURITY_RBAC.md, adr/ADR-011-authentication.md;
  tasks/P1-01.md, P0-02.md, DECISIONS.md and STATUS.md.

## Historical P0-02 outcome
- P0-02 requested; clean main `b3517d3` matched origin and the reported scaffold.
  Created `feature/p0-02-infrastructure`; plan/tests are in `tasks/P0-02.md`.
  Reviewed all mandatory docs, source, lockfiles, Compose and CI; detailed ADRs
  recorded before implementing infrastructure. P0-01 evidence below is historical.
- Added SQLAlchemy 2.1.7/Alembic 1.20.1; all existing locked versions retained.
  The baseline creates only Alembic history; clean/repeated upgrade, drift check,
  safe downgrade/re-upgrade and unrelated-row preservation pass on disposable DBs.
- Added request sessions/pool disposal, live/ready separation, safe consistent
  errors, UUID correlation and whitelisted JSON logs. Frontend behavior unchanged.
- Implementation commit `b8e3f9e1b0a5f6d5ee7a293602cffa4ed4c33806` pushed to
  `feature/p0-02-infrastructure`; [PR #1](https://github.com/jpdoestech/manpower-erp/pull/1)
  remains open for review into main. No merge performed.
- Hosted [push CI 41752561626](https://github.com/jpdoestech/manpower-erp/actions/runs/41752561626)
  and [PR CI 41752609488](https://github.com/jpdoestech/manpower-erp/actions/runs/41752609488)
  both completed successfully on 2026-11-04. Backend, frontend and compose jobs all
  passed in both runs, including migrations and outage/recovery/persistence.
- P0-02 is DONE against its acceptance gates. Local isolated PostgreSQL cluster
  stopped; generated test databases cleaned up; input database has zero public
  tables. No production changes or P1-01 implementation performed.

## Historical P0-02 handoff / limits

Review PR #1; do not merge automatically. Recommend **P1-01** only on a separate
user request. No P1-01 work started.
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
| Hosted backend job 126320930700, push run 41752561626 | PASS; frozen install, format/lint/types, 32 unit/API tests, 4 PostgreSQL integration tests, migration CLI upgrade/repeat/check/downgrade/re-upgrade/check, audit |
| Hosted frontend job 126320929113, push run 41752561626 | PASS; install, format/lint/types, 5 tests, build, audit |
| Hosted compose job 126320929498, push run 41752561626 | PASS; clean build/boot, migration ordering, HTML/proxy/live/ready checks, DB stop → live 200/ready 503, DB restart/readiness recovery, migration check, persistent cluster identifier after container recreation; test volumes removed |
| PR run 41752609488 (jobs 126321088423/126321088735/126321088836) | PASS; compose/backend/frontend on PR merge ref |

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

Hosted CI/PR evidence is linked above. Only documentation evidence changes follow
the verified implementation commit. No production migration/deploy or auto-merge.
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
| P0-02 | 2026-11-04 | b8e3f9e; feature branch; PR #1 | P0-02 commands above; push/PR CI 41752561626/41752609488 | PASS; local and all hosted acceptance gates | Automated checks; PR review pending, no human review claimed |
| P1-01 | 2026-11-04 | 3e4bc82; stacked PR #2 | Current P1-01 evidence, CI 41759481411/41759551633 | All local/hosted gates pass; REVIEW for human security acceptance | No human review claimed |

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
