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

### Head offices and branches

Revision 0006 adds the operational hierarchy. Existing registry grants receive
manage_hierarchy=false. A trusted operator must enable the additional capability
for each intended user/company pair in the same privately configured terminal.

```powershell
.\.venv\Scripts\python.exe -m app.organizations.cli grant-hierarchy COMPANY_UUID your_username
.\.venv\Scripts\python.exe -m app.organizations.cli revoke-hierarchy COMPANY_UUID your_username
```

An active registry grant and active account are required to enable hierarchy
access. Revoking registry access also clears hierarchy access. Local restore
clears both capabilities while retaining organization records and audit history.

After setup-local.bat applies migrations, run start-local.bat and choose Head
Offices or Branches. Find/select a company from the authorized options. Use Add
head office first, then Add branch and select its head office. The selectors and
record lists support search and pagination. Edit names, administrative status and
end dates through version-checked dialogs. All end-date values are explicit on
edits, including null for an open period.

Company, parent, code and effective start date are fixed after creation. A branch
period must fit within its head-office period. Creating records requires an active
company. A new branch requires an active, unexpired head office. An active record
cannot have an end date before today's date in Asia/Manila. Future start dates are
allowed for planned records. Administrative active status and the displayed
effective period are separate fields.

Inactivate branches before their head office. To shorten a head-office period,
first give every child a compatible bounded period, including inactive children.
Concurrent parent closure and child creation serialize on the company record.
Hierarchy audit snapshots retain each old/new value. Physical deletion of a
record referenced by audit or children is restricted. A populated hierarchy
downgrade is refused. Existing company data survives upgrade with hierarchy
capabilities disabled by default.

The private runtime SQL now targets 0006 and grants only the required hierarchy
operations. Runtime cannot modify company/parent/code/start-date columns or grants.
RLS uses trusted server-owned transaction context and explicit capability checks.
The database owner and operators remain privileged. Branch-scoped roles and
Maker-Checker workflows remain P1-03 work.

Alembic revision 0005_company_registry creates the company, grant and event tables
with restrictive references. Empty downgrade removes these tables. A downgrade
with any organization history fails before DDL. Existing authentication history
retains its prior downgrade guards. This revision installs company RLS policies.

The private schema runbook and runtime grants now target 0006. Runtime receives
company SELECT, selected registry-column UPDATE, grant SELECT and company event
INSERT with the timestamp return column. Provisioning owners are privileged and
must be kept separate from FastAPI credentials. Each API transaction sets its
authenticated user context locally. Pool commit/rollback clears that context.
Frontend state and supplied company/role headers do not grant access.

Client relationships, contracts/sites, tax profiles, global workspace context
switching and scoped RBAC remain outstanding. Registry grants authorize the
registry. The separate hierarchy capability authorizes head offices and branches.
Human review and hosted configuration acceptance remain pending.
