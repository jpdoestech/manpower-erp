# CR-002B completion — Windows SQLite tools

Pre-code plan, 2026-11-04. Explicit user completion request authorizes the remaining
B tools. Start feature/cr-002b-completion at verified 9e44c96 / PR #8. Fresh fetch:
#6 (65246ba), #7 (17e5bfb), #8 (9e44c96) open/unmerged, each 10/10 checks; preserve
stack ancestry and account diagnostics. No formal P1-01 acceptance inferred.

Current gap: two BATs exist; seven missing. Current start owns child handles only;
no safe external stop protocol. Backups/reset/restore absent. User's existing API/
Vite occupy loopback 8000/5173; do not interrupt them or touch their active DB.

## Implementation / files

- Add root stop-local, test-local, backup-local-db, restore-local-db,
  reset-local-db, migrate-local, check-local BATs using existing local.py.
- Add a small Windows file-lock/cooperative-stop module: per-checkout held lock
  and random instance marker; stop requests that instance only, no PID-file kill.
  Existing handles still own child cleanup. Stale/unmanaged listeners cause safe
  refusal. Old supervisors without protocol must be stopped with their own Enter.
- Add SQLite tools module: fixed checkout DB, reject symlinks/path escapes;
  `.local-backups` outside active `.local`; SQLite backup API for live snapshots,
  integrity/FK/current-schema validation. Offline operations coordinate locks and
  refuse listeners. Restore/reset require exact typed confirmation and pre-change
  backup, prepare/validate candidate, checkpoint/close WAL safely, atomic replace.
  Never delete active sidecars manually. Failures retain original/recovery backup.
  Restore retains identity/audit UUIDs but revokes restored sessions/recovery tokens,
  expires pending account requests and appends a local restore audit event, so a
  snapshot cannot revive previously revoked authentication capabilities.
- Test-local runs backend non-integration, Windows helper tests (nested native
  network smoke disabled), frontend tests, without Docker/PG. Check-local reports
  versions, SQLite integrity/migrations, safe API status (stopped is supported).
- Extend scripts/tests and Windows CI to exercise real nine-command flow in an
  isolated fresh source copy, preserving synthetic UUIDs/audit/sessions. Keep
  existing backend security cases and actual PostgreSQL regressions.
- Update AGENTS, README, LOCAL_WINDOWS_SETUP, DATABASE_MODES, CR-002,
  STATUS/DECISIONS, applicable architecture guidance and this evidence file.
  Add CR-002C technical plan only; no Supabase integration or business modules.

## Acceptance / testing

Unit tests: safe/stale ownership, repeated stop, no unrelated PID termination;
path/symlink/backup/version/corruption/FK rejection; cancellation unchanged data;
live backup consistency, restore/reset preservation/recovery, migration failure
rollback. Refuse active restore/reset/migrate, preserve .env/ambient PG settings.
Real Windows CI: setup twice, ordinary CLI synthetic account, start, HTTP login/
logout/CSRF, live backup, check, external stop, restore, reset/restore round trip,
offline migration twice and test-local. Confirmation is supplied explicitly by the
test on its own disposable data, never --force. Real local fixed-port smoke is
unrun while user app occupies ports; safe isolated DB/helper tests continue.

Run Ruff/mypy, Biome/TypeScript, backend SQLite/security/migration tests, Windows
launcher tests, frontend tests/build, dependency audits, actionlint/Compose config;
verify hosted real PostgreSQL + Docker + Windows gates. Report exact commands,
counts, skips and limits. Financial duplicate posting is N/A (no financial schema);
existing single-use recovery/approval/concurrent bootstrap cases cover applicable
identity duplicates. No production credentials/data/deployment or automatic merge.

Rollback: no schema change. Prior BATs/backend remain compatible. File tools are
opt-in; preserve immutable timestamped backups on failure and before every reset/
restore. Restore supports current revision snapshots only. Never auto-downgrade
or import arbitrary databases. B remains REVIEW until acceptance; C implementation
must wait for acceptance even after its plan is prepared.

## Local checks so far

- Backend `uv run --locked pytest -q -m "not integration"`: 110 passed /
  42 deselected, 67.22s. Existing SQLite auth cases cover ordinary/duplicate users,
  confirmation, expiration, reset single-use, activation/deactivation, independent
  approvals, CSRF, concurrent duplicates, migrations/rollback.
- Ruff format/lint and strict mypy including all scripts: 37 files, pass.
- Windows helper/BAT safety suite: 28 passed / one opt-in fixed-port smoke skipped
  (29 discovered); final test-local wrapper run follows below. Local app ports are
  occupied by the user's existing instance, left untouched.
- Frontend format/lint/TypeScript, 13 tests (21.16s), build and npm audit pass;
  pip-audit reports no known vulnerabilities. Actionlint/Compose config and
  whitespace checks pass. No local PostgreSQL/Docker boot is claimed in this task.

Initial fixture SQLite connections were not explicitly closed, causing two
Windows cleanup errors; fixed with closing contexts. A test-only missing import
was corrected. Failed synthetic fixture DB files were cleaned by exact literal
paths; no active/developer DB was targeted. Later full test-local execution found
13 diagnostic fixture errors because it inherited the active SQLite mode while
those mock tests supply a PostgreSQL URL. Test subprocesses now receive no active
DB/auth configuration, with a regression assertion; no database guard weakened.
The first wrapper run failed (97 passed/13 setup errors); rerun is in progress.

Latest restore safeguard retains historical UUIDs but revokes snapshot sessions/
recovery tokens, expires pending requests and appends a local restore audit event.
The focused live-writer backup/restore/guard test passed (21.244s). No financial
schema or posting requirements are claimed; those acceptance cases remain N/A.
Hosted full nine-command fresh-Windows and PostgreSQL evidence remains pending.

Actual test-local.bat rerun exits 0: 110 backend tests (61.67s), 29 launcher/
safety tests passed with one opt-in full smoke skipped (30 discovered), and 13
frontend tests (11.26s). Existing user servers remain untouched. Initial staged
whitespace check caught wrapper trailing spaces; corrected in 166cdba. Initial
push hit transient DNS failure, then succeeded without credential/config changes.

First hosted run (166cdba) passes frontend, Compose and existing BAT gates but
fails Linux mypy on Windows-only native API types. Explicit top-level platform
implementations now pass strict mypy for both Windows and Linux (37 files), and
Windows CI type-checks the helper as well. The full Windows flow reached its final
test-local step; its nested legacy BAT tests failed because the disposable source
copy omitted Docker fixture files. Copy those existing fixture inputs too; no
Docker execution introduced. No failing check is accepted or suppressed.

Second hosted source 905ad83 passes Linux backend (110 unit/SQLite, 42 PostgreSQL,
migration CLI/audit), Compose/frontend and existing BAT gates. Windows verifies
setup/start/check/backup/repeated stop/restore/reset/repeated migration, then its
last frontend test command fails: npm's .cmd shim splits the ampersand in the
isolated checkout path. Invoke the same installed Vitest CLI via Node directly,
matching the existing Vite launcher. Keep the spaces/ampersand fixture intact.

The direct Node/Vitest regression passes 13 tests (4.63s) in an actual isolated
checkout path containing spaces and an ampersand, npm ci/audit 0 vulnerabilities.

## Changed files (completion scope)

Added: backup-local-db.bat, check-local.bat, migrate-local.bat, reset-local-db.bat,
restore-local-db.bat, stop-local.bat, test-local.bat;
scripts/windows/database_tools.py, scripts/windows/runtime.py;
scripts/tests/test_database_launchers.py; docs/adr/ADR-015-local-recovery.md;
tasks/CR-002B-completion.md, tasks/CR-002C.md.

Modified: scripts/windows/local.py, scripts/tests/test_native_launchers.py,
.github/workflows/ci.yml, .gitignore, AGENTS.md, README.md,
docs/ARCHITECTURE.md, docs/DATABASE_MODES.md, docs/LOCAL_WINDOWS_SETUP.md,
docs/SECURITY_RBAC.md, tasks/CR-002.md, tasks/DECISIONS.md,
tasks/ROADMAP.md, tasks/STATUS.md. Existing setup-local/start-local BATs are reused
unchanged, and backend/frontend application/schema/dependency locks are unchanged.

## Final verified implementation — REVIEW

Source **22b437b2abe75ae19a95d5040785a7efd2d3e5a6** in
[PR #9](https://github.com/jpdoestech/manpower-erp/pull/9), stacked on #8, passes
**10/10** branch/PR checks:
[push 41840454394](https://github.com/jpdoestech/manpower-erp/actions/runs/41840454394),
[PR 41840462879](https://github.com/jpdoestech/manpower-erp/actions/runs/41840462879).

| Verification | Exact command / result |
|---|---|
| SQLite/backend (Windows CI) | `uv run --locked pytest -q -m "not integration"`: 110 passed / 42 deselected, 14.39s |
| PostgreSQL (Linux CI) | `uv run --locked pytest -q -m integration`: 42 passed / 110 deselected, 12.54s; real PostgreSQL service |
| Backend/unit (Linux CI) | Same non-integration command: 110 passed, 9.55s |
| Windows fresh workflow + safety | `ERP_NATIVE_SMOKE=1`, `uv run --locked python -m unittest discover -s ../scripts/tests -p "test_*launchers.py" -v`: 30 passed, 198.484s, no skips |
| Existing BAT regressions | Separate Windows job: 8 passed, 4.737s (included in the 30 above) |
| Type checking | `uv run --locked mypy app tests alembic ../scripts`: 37 files; Windows scripts check: 6 files; both pass |
| Formatting/lint | Existing Ruff format/check across backend/scripts, Biome and TypeScript gates pass |
| Frontend | 13 tests and production build pass; local final direct-Node path regression: 13 passed, 4.63s |
| Migrations | SQLite clean/repeat/failure recovery and native migrate twice pass; PG CLI up/repeat/check/down/up/check passes |
| Security/static | pip-audit/npm audit: no known vulnerabilities; actionlint, Compose config and whitespace pass |

Native CI prints verified command names for setup (twice), start/readiness, check,
live backup, stop (twice), restore, reset, restore, migrate (twice), check and test.
It checks real HTTP ordinary-user login/me/CSRF logout, repeated-start refusal,
restored identity/audit/session UUIDs and guard presence, backup while a writer
holds uncommitted changes, restore token/session revocation, failed migration/
replacement recovery, cancellation and unsafe path/FK/guard/version rejection.
No real password, default administrator or self-approval bypass is used.

User's original listeners retain the same PIDs (8000:23068, 5173:27032); no local
full fixed-port smoke or destructive operation touched that instance. Real hidden
TTY entry, browser opening, forced X/OS-crash cleanup and corrupt-active-DB manual
salvage remain unrun/outside supported automatic recovery. Use Enter/stop for
managed shutdown; old launchers use their own Enter once. Backups are unencrypted,
trusted/current-revision/local only; network/cloud-sync storage is unsupported.

Implementation is complete and automated gates pass; **B acceptance remains
pending**, so status is REVIEW. Evidence-only docs follow this verified source.
P1-01 human security acceptance remains pending; no merges/deployments/production
data changes. Recommended next task: **CR-002C**, plan prepared in CR-002C.md;
implement only after B acceptance. No C SDK/verifier/mapping/grants were added.
