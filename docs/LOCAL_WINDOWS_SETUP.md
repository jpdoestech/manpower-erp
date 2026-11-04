# Windows SQLite development tools

No Docker or locally installed PostgreSQL is needed. Requires Windows, Node 24/npm,
uv 0.13.7 and internet for initial locked downloads. Setup installs managed Python
3.13.18 under ignored `.tools/python`; existing `.tools/Scripts/uv.exe` or uv on
PATH is used. With an existing Python, install uv via `python -m pip install uv==0.13.7`.
Reopen launchers after installing prerequisites. No administrator launch required.

| Root command | Behavior |
|---|---|
| `setup-local.bat` | Locked dependencies/npm ci, SQLite upgrade/check, optional ordinary account; preserves .env/data |
| `start-local.bat` | Loopback API/Vite, database readiness then browser; keep window open |
| `stop-local.bat` | Cooperatively stop this checkout's managed instance; repeated stop is safe |
| `test-local.bat` | Backend unit/SQLite, Windows helper/BAT tests, frontend tests; no PG/Docker |
| `backup-local-db.bat` | Validated SQLite backup API snapshot, safe while app runs |
| `restore-local-db.bat [backup-filename]` | Validate and restore trusted current-revision snapshot, offline and confirmed |
| `reset-local-db.bat` | Empty migrated SQLite database, offline and confirmed, recovery backup first |
| `migrate-local.bat` | Upgrade/repeat/schema check, offline; preserves data |
| `check-local.bat` | Tool versions, integrity/FKs/guards/revision/schema and API readiness; stopped API is reported normally |

All commands locate the checkout regardless of invoking directory, force fixed
local SQLite/auth child settings and return nonzero on failure. Existing parent
environment and `.env` are preserved; cloud/PostgreSQL URLs are never selected by
these tools. Existing `setup.bat` / `run.bat` remain the separate Docker workflow.

## First run and ordinary account

Double-click setup-local.bat. Choose Y to create an ordinary test account, enter a
username and hidden confirmed password of 15–128 characters. Choose N on later
setups to retain accounts. No default credentials, automatic admin/company grants
or silent username resets. A username such as admin grants no special privilege.
The diagnostics distinguish mismatch, invalid input, missing interactive hidden
input and database errors; never pipe a real password into a launcher.

Double-click start-local.bat. Open http://127.0.0.1:5173 and sign in; API docs are
at http://127.0.0.1:8000/docs. The current UI is the authentication foundation;
organization/accounting dashboards are not implemented. Keep the launcher open.
Press Enter/Ctrl+C there, or use stop-local.bat, to stop its owned servers.

## Ownership and concurrency

A held Windows lock plus random instance marker identifies a managed supervisor;
no persisted PID authorizes killing. External stop requests only that marker. Child
cleanup uses original live process handles. Unmanaged occupied ports cause refusal,
never a process-name/port-wide taskkill. Old running launchers from before this
protocol must be stopped with Enter in their own window before starting the new
version. Closing a window forcibly/crashing the supervisor is not a recovery path:
if listeners remain unmanaged, stop them through their original owning terminal.

Setup/migrate/reset/restore require the app stopped and coordinate lifecycle/data
locks. Backup can run live and captures committed WAL data with SQLite's backup
API. Stop has a bounded wait; retry or use the owner window if startup is still busy.
Logs are `.local/logs/api.log` and `web.log`, overwritten on start. Check errors
without sharing credentials or database/backup contents.

## Backup, restore and reset

Active database: `.local/manpower_erp.db`. Backups: **`.local-backups`**, outside
that active directory, with unique UTC timestamp/UUID filenames. Both directories
and database sidecars are ignored by Git. Backups contain unencrypted account
hashes/audit/history; keep them private on a local disk, outside network/cloud-sync
folders. No automatic retention/deletion or production recovery guarantee.

```bat
backup-local-db.bat
stop-local.bat
restore-local-db.bat backup-YYYYMMDD-HHMMSS-UUID.sqlite3
migrate-local.bat
check-local.bat
start-local.bat
```

Use the exact filename printed by backup. With no argument, restore lists recent
backups and prompts for a filename. Directory paths, junctions/symlinks/hardlinks,
corrupt files, missing guards/FKs and incompatible revisions are rejected. Trust
only snapshots generated for this checkout; arbitrary external import is phase E.

Restore requires **RESTORE LOCAL DATA**; reset requires **RESET LOCAL DATA**.
Other input cancels with exit 2. Both operations preserve a validated pre-change
snapshot before preparing/checking a candidate and atomically replacing the fixed
local database. Failures preserve original data or the recovery snapshot. WAL is
checkpointed/closed by SQLite; active sidecars are never manually discarded.
All non-ERP SQLite clients must also be closed for offline file operations.
Corrupt/incompatible active data that cannot be backed up safely is refused; no
forced erase switch exists. Keep the recovery filename printed by the tool.

Restore preserves identity/history UUIDs, appends a local restore audit event,
revokes restored sessions/password-reset tokens and expires pending account-change
requests. Sign in again; request fresh recovery/approval actions as needed. Password
hashes and existing account capabilities reflect the selected snapshot. The
pre-change backup retains newer history. Reset creates no accounts or credentials.

## Verification and boundaries

`test-local.bat` runs isolated SQLite tests and helper tests without touching the
active development DB. The network/fresh-checkout smoke is deliberately disabled
inside this command to avoid recursion and interfering with running local ports;
Windows CI enables it once on a fresh runner, exercising all nine BATs. Security
cases include account creation/confirmation/duplicates, login/logout, expiration,
independent reset/activation/deactivation and CSRF. PostgreSQL concurrency requires
its separate real CI database; SQLite does not establish financial concurrency.

Formatting/lint/type/build/audit commands remain in README/CI and task evidence.
Exit codes: 0 success (including already stopped/offline API check), 1 failure,
2 cancelled reset/restore. No Supabase/Auth adapter or deployment change here.
P1-01 human security acceptance remains pending. CR-002C has a technical plan only
and requires CR-002B acceptance before implementation.
