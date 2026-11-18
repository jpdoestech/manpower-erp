# Company registry development slice

Company Management lists only companies explicitly assigned to the signed-in
account. Search, active/inactive filters and pages operate inside that scope.
Edit the registry name or active status in the dialog. A stale edit returns a
conflict and asks you to refresh. Inactivation retains identity and audit history.

## Local operator setup

Run `setup-local.bat` to apply the additive migration. Existing local accounts
and their audit history are retained. Use a local synthetic account for testing.
Then open PowerShell at the repository root and run the following, replacing
`your_username` with the existing test account username.

```powershell
$env:APP_ENV='local'
$env:DATABASE_MODE='sqlite'
$env:DATABASE_URL='sqlite:///./.local/manpower_erp.db'
Set-Location backend
.\.venv\Scripts\python.exe -m app.organizations.cli create DEMO 'Demo Company' your_username
```

The command prints the company UUID. Grant or revoke registry access using that
UUID and an active account, from the same configured operator terminal.

```powershell
.\.venv\Scripts\python.exe -m app.organizations.cli grant COMPANY_UUID another_username
.\.venv\Scripts\python.exe -m app.organizations.cli revoke COMPANY_UUID another_username
```

Run `start-local.bat` from the repository root and sign in. Choose Company
Management. Company provisioning requires trusted OS and database access.
Protect that terminal and the SQLite file. Restoring a local backup revokes
all restored company grants. Review and regrant access explicitly after restore.

## PostgreSQL operations

Alembic revision 0005_company_registry creates the company, grant and event tables
with restrictive references. Empty downgrade removes these tables. A downgrade
with any organization history fails before DDL. Existing authentication history
retains its prior downgrade guards. This revision installs company RLS policies.

The private schema runbook and runtime grants now target 0005. Runtime receives
company SELECT, selected registry-column UPDATE, grant SELECT and company event
INSERT with the timestamp return column. Provisioning owners are privileged and
must be kept separate from FastAPI credentials. Each API transaction sets its
authenticated user context locally. Pool commit/rollback clears that context.
Frontend state and supplied company/role headers do not grant access.

Head offices, branches, client relationships, contracts/sites, tax profiles,
company-context switching and scoped RBAC remain outstanding. Company grants
authorize the registry only. Human review and hosted configuration acceptance
remain pending.
