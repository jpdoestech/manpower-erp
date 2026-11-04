# RBAC, Scope and Separation of Duties

## P1-01 implemented access surface

| Surface | Anonymous access | Company/role authority |
|---|---|---|
| Web bootstrap page | Public local development page | None |
| GET /api/bootstrap | Public static product name and bootstrap stage | None |
| GET /api/health/live | Public process status; no DB call | None |
| GET /api/health/ready | Public 200/503 connectivity status; no DB details | None |
| POST /api/auth/login | Credentials, bounded attempts, Origin check | Identity only; no company grants |
| GET /api/auth/me | Valid active unexpired cookie session required | Own UUID/username/CSRF only |
| POST /api/auth/logout | Valid session + CSRF + Origin check | Revoke own presented session |
| POST /api/auth/password | Valid session + CSRF + current password + Origin check | Own password; revoke all own sessions |
| Operator identity CLI | Server/database operator only; hidden password prompts | Create/reset/soft-disable identity; no role grants |
| /docs, /redoc, /openapi.json | Public development API documentation | None |
| Business routes | Not implemented; 404 | Client headers grant no access |

Global user/session/auth-event identities exist. No company membership, company-owned
business record, approval, export or background job exists yet. Authentication grants
no company, admin or financial permission. Scoped RBAC/tenant models remain P1-02/03;
current boundary tests do not certify future tenant isolation. No signup/user-list API.
Compose publishes only on loopback. P0-02 adds whitelisted JSON request diagnostics
and UUID correlation; IDs and client headers grant no authority. Safe error responses
omit validation input, exception messages and credentials. Shipped entrypoints turn
off raw Uvicorn access logs. No broad CORS policy was introduced. DB configuration
is server environment only; no arbitrary SQL/formula API exists. Alembic's version
table is infrastructure, not a company-owned business record.

Dev Compose retains P0-01's DB owner credentials. Production migrator/runtime roles,
RLS and durable workflow audit need their scheduled security work; diagnostic
logs and P1-01 authentication events do not implement financial audit controls.
Passwords use Argon2id; only session-token hashes are stored. Sessions expire in eight
hours and are revoked by logout/password reset/change/deactivation. Events contain
subject UUID, kind/source, correlation and time; no credentials/login names. They are
protected against UPDATE/DELETE/TRUNCATE by a PostgreSQL trigger, not tamper-proof
against privileged DDL by the development DB owner.
No MFA assurance is asserted. ADR-011 documents MFA/recovery/step-up planning and
production prerequisites. Human security acceptance is required for P1-01.
Never put real employee or fiscal data in
this development scaffold. See ADR-002/005/009/010 and `OPERATIONS.md`.

## Access layers
Identity -> membership(s) in legal companies -> role grants scoped to company/head office/branch/client/contract -> resource action -> workflow constraints. Explicit deny supersedes grant. Default deny.

## Personas
Platform Super Admin (technical access, no assumed accounting approvals); Company Admin; Head Office Admin; HO Accountant; Branch Admin; Branch Accounting Maker; Branch Accounting Approver; Collections Maker; Viewer; Commenter; auditor read-only.

## Representative permission keys
org.read, org.manage; client.read, client.manage; contract.manage; billing_definition.propose, billing_definition.approve, billing_definition.publish; billing_template.propose, billing_template.approve; billing_draft.create, billing_draft.edit, billing_draft.submit, billing.approve; invoice.issue; journal.propose, journal.approve, journal.post, journal.reverse; payment.record, payment.approve, payment.allocate; tax_rule.propose, tax_rule.approve; reports.read, reports.export; user.grant_role.

## Workflow enforcement
Creator != approver on same transaction; requester != publisher when configuration affects accounting. Re-evaluate role and scope at transition time; do not rely on captured client UI state. Approval delegation needs validity period and audit. Self-service role escalation prohibited. Separate privileged break-glass procedures with monitoring and expiration.

## Tests required for every module
- Company A user gets 403/404 as appropriate on Company B API, report and file.
- Branch A user cannot access Branch B unless explicitly granted.
- User with Maker+Approver cannot approve self-authored document.
- Expired/revoked grants are immediately ineffective.
- Horizontal IDOR, list filtering, exports and async job scope checks.
- Audit records persist on reject/approve/reverse/publish.
