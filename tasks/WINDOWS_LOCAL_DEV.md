# Windows local setup and run launchers

2026-11-04. User-authorized contributor tooling only; no dependent P1-02 work.
Branch feature/windows-local-launchers from d8d1cd6; separate PR stacked on #4.
P1-01 remains REVIEW and P1-02 remains BLOCKED on human security acceptance.

## Plan before implementation

- Add root setup.bat and run.bat, using the existing pinned Docker Compose stack.
  Require Docker Desktop's local default context and Linux engine; explicitly pin
  compose.yaml, .env and project name. No installer, remote context or production.
- Setup creates .env only when absent, with a cryptographically generated local DB
  password and matching native URL. Never overwrite, echo or execute .env contents.
  Existing files remain unchanged; invalid/blank settings stop with safe guidance.
- Reuse run.bat to validate Docker/Compose/engine/config and build/start/wait for
  the existing DB -> migration -> API -> web dependencies. Setup optionally invokes
  existing ordinary-user CLI with username read inside Python and hidden password
  prompts. No default user/password, Super Admin bootstrap or company grants.
- Normal run opens the fixed loopback app URL after successful readiness. Keep
  double-click error output visible, return failure codes, and work from any cwd
  including repository paths with spaces/metacharacters. Never delete volumes.
- Update README/OPERATIONS and STATUS; retain scripts' CRLF checkout via existing
  .gitattributes. Correct earlier chat test instructions: API image excludes pytest;
  use documented native/CI test commands instead of container pytest.
- Add stdlib Windows command-runner tests using a Docker stub and actual cmd.exe/
  PowerShell. Add a Windows CI job; existing Linux backend/frontend/Compose gates
  continue to prove runtime/migrations, not real Docker Desktop execution locally.

## Acceptance / checks

Tests must cover missing Docker/Compose/Linux engine; absent or invalid config;
setup secret generation without output leakage; preservation of existing .env;
success command ordering and cwd; failed build/readiness without success claims;
optional ordinary-user provisioning invocation and failure propagation. Use a
temporary fixture checkout and stub, never the real .env or existing DB/accounts.
Verify shell input remains data, no secret logging, no destructive volume flags,
and local default context/explicit Compose file are used consistently.

Run Windows stdlib test suite, relevant Ruff checks for the test code, Compose
configuration, actionlint and git diff --check. Push descriptive commits and a
separate PR; verify hosted Windows and existing Linux gates. Do not claim a real
local Docker Desktop boot when the Docker executable/engine is unavailable.

## Local implementation and evidence

Implemented root setup.bat/run.bat, CRLF checkout, Windows command tests, Windows CI
job and inclusion of the new tests in backend lint/type gates. Existing application,
schema, dependencies, account permissions and security acceptance are unchanged.
README/OPERATIONS explain double-click setup/run, optional ordinary test account,
preserved .env/data, local prerequisites, correct test commands and stop behavior.

| Exact command | Result |
|---|---|
| `backend/.venv/Scripts/python.exe -m unittest discover -s scripts/tests -p test_windows_launchers.py -v` from root | PASS; 8 tests, 3.682s; actual cmd.exe/PowerShell, temporary checkout and Docker stub |
| `uv run --locked ruff format --config pyproject.toml --check . ../scripts/tests` from backend | PASS; 27 files |
| `uv run --locked ruff check --config pyproject.toml . ../scripts/tests` from backend | PASS |
| `uv run --locked mypy app tests alembic ../scripts/tests` from backend | PASS; 27 source files |
| `.tools/docker-compose.exe config --quiet` with process-local synthetic password | PASS; actual Compose configuration, no real daemon |
| `.tools/actionlint/actionlint.exe .github/workflows/ci.yml` | PASS |
| `git diff --check` | PASS |

Tests verify new secret/native URL matching without secret output; repeat setup and
invalid existing config preserve bytes; foreign launch cwd and spaces/metacharacters
work; absent template/Docker/Compose/Linux engine/config prevent startup; failed
startup is not reported ready; optional existing CLI invocation and its failure
propagate. Flags pin default context/file/env/project despite overriding environment
settings. No real database/account, Docker daemon or browser is used by these tests.

Early harness quoting/one misplaced assertion and lint invocation issues were
corrected; final checks above pass. Ruff must run from documented backend cwd as
CI does; running it from root classifies existing imports differently. No unrelated
backend import rewrite was made. The API runtime image still excludes tests/dev
dependencies; previous chat's container pytest command was incorrect and corrected.

Local Docker Desktop boot, interactive Docker password TTY and normal browser-open
path remain unrun; only the setup caller's suppressed-browser path is exercised.
Hosted Windows tests and Linux backend/frontend/migration/Compose CI must pass after
push. No application test rerun locally claimed; unchanged runtime gates run in CI.

Changed files: setup.bat, run.bat, scripts/tests/test_windows_launchers.py,
.gitattributes, .github/workflows/ci.yml, README.md, docs/OPERATIONS.md,
tasks/WINDOWS_LOCAL_DEV.md, STATUS.md, DECISIONS.md. No .env or credentials tracked.

First hosted source run 41781977728: Linux backend/frontend/Compose passed;
Windows had 7 passing cases and one fixture failure. The runner ships Docker in
System32, so the missing-Docker case still discovered a real CLI. Corrected only
the fixture by retaining a copied system where.exe on an isolated PATH and removing
its Docker stub; launchers were unchanged. Do not count that failed run as passing.

## Hosted verification / delivery

Corrected source `ec348a73748ddfd0c40a23bcd8df46104475317f` passes **8/8 checks**:

- [Push run 41782345240](https://github.com/jpdoestech/manpower-erp/actions/runs/41782345240): Windows launchers, backend, frontend and Compose all successful.
- [PR run 41782348413](https://github.com/jpdoestech/manpower-erp/actions/runs/41782348413): the same four jobs all successful.
- Hosted Windows job 126416555152 reports **8 tests in 4.563s, OK**. Local suite
  after the final fixture correction reports **8 tests in 3.613s, OK**; Ruff/mypy
  pass for all 27 files. Only the fixture changed after original launcher delivery.
- Existing Linux gates cover application tests, types/lint/build/audits, clean
  migration CLI roundtrip and container authentication/health/outage/persistence.

[PR #5](https://github.com/jpdoestech/manpower-erp/pull/5) is stacked on #4 at
d8d1cd6; no merge performed. Evidence-only documentation follows the verified
source. Real local Docker Desktop, interactive Docker password TTY and browser
opening remain unrun; do not infer production or human security acceptance.
