# ADR-012 — Technical administrators and controlled account recovery

2026-11-04. Adopted for P1-01 CR-001 development; human security review pending.
Supersedes ADR-011's CLI-only account administration/reset-token exclusions.

Use one false-by-default `is_super_admin` identity capability. It authorizes only
global identity administration; never company data, scoped grants or accounting
approvals. Company memberships and scoped RBAC remain P1-02/P1-03. No client header
or request-supplied capability is trusted. Existing users gain no privileges.

Bootstrap two distinct new administrators through a one-time, hidden-prompt,
server/database operator CLI. Serialize the database transaction; refuse repeat
bootstrap even if existing admins are disabled. No automatic startup provisioning,
default credentials, public signup, environment password or production execution.
Database operators remain explicitly privileged; existing CLI recovery is a
break-glass operational boundary, not an application authorization bypass claim.

Registration creates an inactive identity. Activation, deactivation, reset-token
issuance and lockout release require a request and another active Super Admin's
approval. Approver differs from requester AND target; self-service password changes
with the current password are credential proof, not approval. Reauthenticate each
administrative mutation, rate-limit it, and recheck both actors under transaction
locks at approval. Requests expire in 24 hours. Serialize administrative transitions
using a fixed PostgreSQL transaction advisory lock, also used for bootstrap and
recovery; no user-supplied SQL. Retain request/approver IDs as audit evidence.

Activation/reset approval returns one random token to the approving administrator
for verified private delivery to the account owner. Only its SHA-256 digest is
stored; expires in 15 minutes, single use, older tokens invalidated. Issuance and
redemption revoke sessions. Password changes/operator reset/deactivation invalidate
outstanding reset tokens. No emailed links, token query parameters or token storage
in the browser. API/UI reset failures are generic. Out-of-band identity verification
and delivery remain a human responsibility; email/self-service discovery is absent.

Retain the durable per-name timed attempt lockout; approved unlock clears only that
name's window. Global protection remains. Maintain at least two active technical
admins when deactivating through the API. DB-owner recovery still needs operational
dual custody/monitoring before production; this cannot police a database owner.

Opaque sessions keep the existing eight-hour absolute expiry; no refresh token is
introduced, so refresh-token rotation is inapplicable. Login already rotates the
presented session. MFA remains ADR-011's server-held assurance/challenge plan;
password reauthentication is not MFA. Production MFA enforcement, recovery delivery,
break-glass custody, limits/retention and deployment remain stakeholder/security
approval gates, not a reason to invent business permissions or implement P1-03.

Tradeoffs: manual recovery delivery and a global administration lock are sufficient
for this small development identity surface. Replace delivery with an approved
verified channel and measure contention before scaling. Migration is additive;
rollback refuses new history/grants rather than silently erasing security evidence.
Evidence: tasks/P1-01-account-controls.md and automated identity tests.
