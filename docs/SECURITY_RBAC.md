# RBAC, Scope and Separation of Duties

## P1-01 implemented access surface

CR-002C planning adds no access surface. Proposed ADR-017/provider strategy keeps
internal ERP UUID/current grants separate from external identity. Cloud links,
reauthentication/refresh/recovery and company deny-all foundations require explicit
review; JWT claims/email/technical admin confer no organizational authority. No
Supabase authentication, cloud MFA, provider-session revocation or tenant model
is implemented. P1-01 human security acceptance remains pending.

UI-001 changes presentation only. Validated existing sessions render the shell;
password/recovery/logout transport and server checks remain unchanged. No company
contexts are fabricated; selector is unavailable pending scope APIs. System
Administration is disabled pending server capability evidence. Static module
previews and component reference carry no permission or data. Only theme is stored
locally. Security acceptance remains pending; see ADR-016/frontend architecture.

CR-002A preserves this matrix on opt-in local SQLite: FK enforcement, immutable
audit UPDATE/DELETE triggers, serialized account transactions, hash-only secrets,
live capability/session rechecks, CSRF and independent approval remain required.
SQLite is local/test only, with an unencrypted ignored file and patched WAL
runtime; no company grants, MFA or human security acceptance are added. Unsupported
AUTH_PROVIDER values fail until C; Supabase DB configuration is no Auth adapter.
File/DDL owners can bypass guards; never store real employee/fiscal data locally.
CR-002B local restore retains audit/identity UUIDs, adds a local restore event and
revokes snapshot sessions/recovery tokens/pending account requests. It never grants
new roles. Unencrypted ignored backups require OS-user custody (ADR-015); this is
local recovery, not production financial rollback or human security acceptance.

CR-001 adds the narrow identity-administration surfaces below (ADR-012).
Business/scoped RBAC and financial approval remain unimplemented.

| Added surface | Required authority / control | Scope |
|---|---|---|
| CLI bootstrap-admins | Trusted server/DB operator, hidden prompts, distinct new accounts, one-time transactional guard | Two technical Super Admins; no company permissions |
| GET /api/auth/admin/requests | Current active Super Admin session; bounded pages of 50 pending requests | Global identity metadata only |
| POST /api/auth/admin/requests | Current active Super Admin, CSRF/Origin, current password, attempt limits | Request register/activate/deactivate/reset_password/unlock |
| POST /api/auth/admin/requests/{id}/approve | Same controls, independent approver, active requester rechecked, unexpired/unapproved request | Approver differs from requester AND target; no financial authority |
| POST /api/auth/reset-password | Possession of unexpired single-use random token, Origin validation, limits | Set target's password; revoke sessions/tokens, no automatic login |

Existing users default to non-admin. API registration is inactive until independent
approval; reset/activation approval returns one secret for verified private handoff.
Only hashes persist. Name-based timed lockout is shared with reauthentication;
approved unlock clears only that name's window. Recovery has a separate fixed
bucket (5/15 minutes); global 60/minute protection remains. High traffic/edge DoS
policy remains a production review item. Out-of-band DB operators already possess
privileged access; protect CLI/database custody separately. No public signup,
role-grant API, company memberships, MFA verification or company data access.

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
| Operator identity CLI | Server/database operator only; hidden password prompts | Create/reset/soft-disable identity; one-time technical admin bootstrap, no company grants |
| /docs, /redoc, /openapi.json | Public development API documentation | None |
| Business routes | Not implemented; 404 | Client headers grant no access |

Global user/session/auth-event identities exist. No company membership, company-owned
business record, financial approval, export or background job exists yet. Login grants
no company or financial permission. Explicit technical capability is required for
identity administration. Scoped RBAC/tenant models remain P1-02/03;
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
