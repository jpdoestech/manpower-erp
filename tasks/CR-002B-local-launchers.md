# CR-002B — Requested setup/start slice

Plan written before code, 2026-11-04. User explicitly requests local BAT setup
and start following verified A (65246ba, PR #6, 10/10 checks). This authorizes the
setup/start slice now; it does not manufacture formal A or P1-01 acceptance.
Branch feature/cr-002b-local-setup-start preserves #6 ancestry. No merges.

Files: root setup-local.bat/start-local.bat, scripts/windows/local.py,
scripts/tests/test_native_launchers.py, CI, README, LOCAL_WINDOWS_SETUP,
DATABASE_MODES, CR-002/STATUS/DECISIONS and this report.

Implement only two requested commands: pinned managed Python/uv dependency setup,
npm ci, safe SQLite migrations/check, optional ordinary-user hidden-password CLI;
loopback API/Vite startup, port collision refusal, readiness before browser,
owned-process cleanup on Enter/Ctrl+C/failure. Existing Docker BATs stay unchanged.
Force local SQLite settings in child environment, ignoring ambient production URLs;
do not overwrite .env, reset accounts/data, grant admins or install system services.
Use existing uv on PATH or .tools; missing tools fail with actionable guidance.

Acceptance: actual cmd BAT invocation, paths outside cwd, missing setup/tool/error
handling, environment overrides never mutate parent/.env, safe repeated setup,
actual SQLite migration and native HTTP startup/login/logout, collision refusal,
both owned ports released on shutdown. Windows CI exercises real tools/servers
with no browser/account prompts. Helper unit tests cover failures and cleanup;
Ruff/mypy include scripts, retain all existing CI/backend/frontend regressions.

Stop after setup/start; no stop/reset/backup/restore/data-transfer commands or
Supabase/Vercel/business modules. Full CR-002B remains partial until its remaining
original requirements and acceptance are delivered. Exact results follow below.

## Local verification

From backend, uv 0.13.7 / Python 3.13.18:

- `uv run --locked ruff format --config pyproject.toml --check . ../scripts`:
  33 files already formatted.
- `uv run --locked ruff check --config pyproject.toml . ../scripts`: pass.
- `uv run --locked mypy app tests alembic ../scripts`: 33 files, no issues.
- `uv run --locked pytest -q -m "not integration"`: 101 passed, 42 deselected,
  18.95s.
- With `ERP_NATIVE_SMOKE=1`, `uv run --locked python -m unittest discover -s ../scripts/tests -p 'test_*launchers.py' -v`:
  **17 passed, 84.196s, no skips** (9 native / 8 existing Docker-stub tests).

The real BAT test copies the source under an isolated `.local/native bat & test-*`
checkout, outside the invoking cwd. Installs actual managed Python/dependencies,
migrates, inserts one synthetic ordinary identity, reruns setup and signs in over
the real Vite/Uvicorn HTTP path. Verifies me, CSRF logout and revoked-session 401,
refuses a second start without stopping the first, then sends Enter and verifies
both ports free. Existing sentinel .env is byte-for-byte preserved; test files and
owned processes cleaned. No developer database or existing account is touched.

From frontend: `npm run format:check`, `npm run lint`, `npm run typecheck`,
`npm test` (13 passed / 3 files, 9.61s), `npm run build`: pass.
Root `.tools/actionlint/actionlint.exe` and `git diff --check`: pass.
Initial line formatting and strict typing issues were fixed; first real smoke
also passed before expanding preservation/collision checks. No tests suppressed.

Not run locally in this slice: PostgreSQL integration/Docker boot, real hidden
TTY password entry, normal browser opening or X-button termination. Existing
application/migrations/dependencies are unchanged; hosted PostgreSQL/Docker gates
must pass after push. Enter/Ctrl+C is the documented shutdown path. CI result and
PR are verified below. Broader B is partial; formal A/P1-01 acceptance unchanged.

## Hosted verification

Implementation `d38a034db6e233dd6653d8b357d8d2010cb908c1`,
[PR #7](https://github.com/jpdoestech/manpower-erp/pull/7) stacked on #6, passes
**10/10** matching-head checks:
[push run 41797323446](https://github.com/jpdoestech/manpower-erp/actions/runs/41797323446),
[PR run 41797507702](https://github.com/jpdoestech/manpower-erp/actions/runs/41797507702).
Windows: 101 SQLite/unit tests in 14.18s, 9 native launcher tests in 42.257s with
no skips, existing 8 BAT tests in the separate launcher job. Linux: 101 unit/
SQLite tests in 9.43s, 42 actual PostgreSQL tests in 12.44s; migration CLI
up/repeat/check/down/up/check, dependency audits and Docker auth/health/dependency
recovery/persistence pass. Frontend gates also pass. Evidence docs follow verified
implementation. Requested slice REVIEW; full B remains partial. No merge/deploy.
