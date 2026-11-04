# ADR-013 — Organizational identities, engagements and bootstrap scope

2026-11-04. PROPOSED ONLY; P1-02 implementation blocked on P1-01 human security
acceptance. This does not amend any implemented access rights or database schema.

Context: the user authorizes the hierarchy ERP Platform > Company > Head Office >
Branch > Client > Service Contract > Deployment/Service Site. Clients may serve
multiple authorized branches. Existing authentication grants no company authority.

Proposed model: independent legal companies own head offices/branches, client legal
identities and dated client/branch engagements. Contracts reference an engagement;
sites reference a contract. Share client identity within a company across branch
engagements rather than copying it per contract/site. Do not share a global client
directory or disclose another company's identifier matches in this slice. A later
explicit cross-company registry would require a separate privacy/sharing decision.

All company-owned relationships carry company_id and scope-preserving composite
foreign keys; uniqueness is scoped appropriately. Keep stable identities, dated
relationships, immutable referenced parents, archive controls and restrictive FKs.
Never cascade-delete organization history. Future transaction tables must reference
the historical organization/relationship, not infer it from today's parent tree.

Tax-registration profiles record asserted classification, evidence, effective dates
and review state in retained versions. VAT/Non-VAT/claimed exemption is metadata,
not permission to apply a tax rate or proof of exemption. CPA review and future
tax-rule approvals remain mandatory; no regulatory classification is invented.

Proposed bootstrap authorization: explicit audited user/company organization-admin
grants established by a protected operator process. Default deny; technical Super
Admin alone and client-supplied company headers confer no organization access.
No UI/API for self-grants or global administrative bypass. Current grant checks in
services plus company-filtered queries and database scope constraints are required.
ADR-002's runtime-role/RLS controls must be resolved and tested before claiming
database isolation; current development owner credentials do not establish it.
This is a narrow capability, not P1-03's role/permission/delegation engine.

Alternatives considered: one parent tree with copied clients (duplicates identity),
global clients with implicit visibility (cross-company leakage), any logged-in user
or technical-admin bypass (excess authority), or full RBAC now (outside P1-02).

Tradeoffs: company-scoped legal identities may repeat the same external entity
between independent companies, preserving the authorization boundary. Historical
relationships and audited grants add constraints but prevent silent reassignment.
Runtime-role setup affects local config and migration ownership and needs explicit
verification; it must not weaken existing authentication or expose credentials.

Acceptance/implementation plan: tasks/P1-02.md. Security reviewer acceptance of
P1-01 is outstanding; final schema/runtime grants and any future cross-company
sharing remain subject to review. No production deployment is authorized.
