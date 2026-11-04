# ADR-005 — Scoped RBAC and Maker–Checker

Date: 2026-11-04. Status: DESIGN ADOPTED; implementation deferred to P1-01/P1-03.

Context: users can hold multiple roles and grants can change before approval.
Alternatives: UI role checks, static role snapshots, server-side scoped authorization.
Choose identity → active company membership → scoped grants → action → workflow
constraints, with explicit deny overriding grants and default deny throughout.

Every transition rechecks current role, membership, scope, expiry/revocation and
resource state inside its transaction. Creator cannot approve the same item even
with both roles; requester cannot publish their own accounting-affecting config.
Delegation must be explicit, time-bound and audited. No self-service escalation.
Technical administrators receive no implied finance approval rights.

Consequences: authorization belongs in service transitions and every query/export/
job, with safe audit events for accept/reject outcomes. UI hiding is convenience
only. Concurrency/locking and immutable identity metadata must preserve this rule.

Approvals pending: stakeholder permission matrix, delegation/break-glass rules,
identity/MFA policy and security review. P0-02 provides public health/metadata only;
it does not implement auth, grant checks or approval audit storage.
Evidence: SECURITY_RBAC, future P1 tenant/self-approval/revocation tests.
