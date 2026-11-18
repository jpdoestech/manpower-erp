# ADR-013 — Organizational identities, engagements and bootstrap scope

2026-11-18 head-office/branch development amendment adds composite company/parent
foreign keys, immutable identities/start dates, bounded effective periods and
append-only hierarchy snapshots. An explicit false-by-default manage_hierarchy
flag extends a single company grant through the protected operator process.
Existing registry grants confer no hierarchy access until that operation.
API and PostgreSQL RLS require both the active grant and capability. Company-row
locking serializes hierarchy changes and registry deactivation. Parent period
changes cannot exclude child history, and a head office with active branches
cannot be inactivated. Runtime column privileges prevent parent reassignment.
SQLite retains serialized transactions and shared service validation. Hierarchy
events and restrictive references preserve old relationships. These are
development decisions under continued-build authority, pending human review.

2026-11-18 implementation amendment under explicit continued-development authority.
Company registry and narrowly scoped operator grants are implemented for review.
Remaining hierarchy and tax-profile design below remains proposed. Human security
acceptance is pending.

The first slice uses stable company UUID/code, mutable registry name/status with
optimistic version checks, explicit per-user company grants, and an append-only
company event log. The API cannot provision or modify grants. Technical admin
capability confers no company access. Operator provisioning events record a null
application actor and an explicit operator event kind, with the target user as
subject. Operator OS/DB custody is the trust boundary for these operations.

PostgreSQL RLS derives the user from a transaction-local value set by FastAPI after
session validation. Runtime must be a non-owner without BYPASSRLS or grant DML.
Schema owners remain trusted migrators/provisioning operators. SQLite uses the
same mandatory service filters within its existing serialized transactions.
Tests verify ungranted reads, scoped reads/updates and context reset across pooled
transactions as a non-owner. This establishes the company registry boundary only.
Scoped hierarchy permissions and financial approval remain future tasks.

Restore revokes all restored company grants while preserving companies and audit
history. A trusted operator must regrant reviewed access after local recovery.

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
