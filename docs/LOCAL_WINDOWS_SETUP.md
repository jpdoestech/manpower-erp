# Windows local setup — SQLite, no Docker

From the repository root, double-click **setup-local.bat** once, then
**start-local.bat** whenever you want to use the app. No PostgreSQL server or
Docker is needed. The older setup.bat/run.bat still select the Docker workflow.

Prerequisites: Windows, Node.js 24 with npm, uv 0.13.7 and internet for the initial
locked dependency downloads. No administrator launch is required. If uv is not
already in `.tools/Scripts/uv.exe` or on PATH, install it using an existing Python:

```powershell
python -m pip install uv==0.13.7
```

Reopen the launcher after installing tools. Setup installs managed Python 3.13.18
under the ignored `.tools/python` directory, synchronizes locked backend
dependencies, runs npm ci, upgrades SQLite through Alembic and verifies schema
drift. It asks whether to create an ordinary local test account. Choose Y, enter
a username, then a hidden confirmed password of 15–128 characters. Choose N on
repeat setups to retain accounts. No default credentials or administrator/company
permissions are created; an existing username is never silently reset.

```bat
setup-local.bat
start-local.bat
```

Start opens http://127.0.0.1:5173 only after the API database readiness check
passes through the Vite proxy. Sign in with the account created during setup.
Keep the launcher window open. Press **Enter or Ctrl+C in that window** to stop
its API/web processes; data remains in `.local/manpower_erp.db`. Use this stop
path before closing the terminal. API docs: http://127.0.0.1:8000/docs.

Both commands work when launched from another working directory. They select
fixed local SQLite/auth settings in child processes and preserve existing `.env`
and parent environment. Start refuses occupied 8000/5173 ports and does not kill
their owner. Check `.local/logs/api.log` and `web.log` if startup fails; logs are
overwritten on each start. Do not run setup while another local instance is open.
No service installation, reset, deletion, backup/restore or persisted PID control.

For unattended verification, `setup-local.bat --no-account` skips provisioning;
`start-local.bat --no-browser` suppresses browser opening but still waits for
Enter to stop. These do not bypass authentication. To run the application tests:

```powershell
cd backend
..\.tools\Scripts\uv.exe run --locked pytest -q -m "not integration"
cd ..\frontend
npm test
```

Use synthetic data only. SQLite files are unencrypted. P1-01 human security review
remains pending; organization/accounting modules are not available. This is the
user-requested setup/start slice of CR-002B; the remaining stop/test/check/migrate/
reset/backup/restore BAT tools have not been implemented. No Supabase/Vercel change.
