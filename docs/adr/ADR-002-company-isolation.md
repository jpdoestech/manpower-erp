# ADR-002 — Company isolation and operational hierarchy

Date: 2026-11-04. Status: DESIGN ADOPTED; implementation deferred to P1-02/P1-03.

Context: independent legal companies share the ERP; client entities can be reused
across approved branches/contracts. Alternatives: database per company, schema per
company, or shared schema with enforced company dimensions. Choose shared schema
with explicit company scope in every company-owned row, query, job and export.

The navigation hierarchy is Company → Head Office → Branch → Client → Contract →
Service Site. This is not an unrestricted single-parent tree: the reusable client
legal registry is linked to company/branch engagements; contracts/sites reference
the approved engagement. A cross-company registry reference confers no access to
another company's commercial data. A branch's head office and every parent scope
must belong to the same company. Confirm exact legal establishment/registration
semantics with stakeholders before P1-02 schema approval.

Future tenant tables require company_id and stable IDs with composite unique keys
and company-preserving foreign keys. Services must filter by server-resolved
membership and branch/client/contract grants; never trust X-Company-ID as authority.
Plan PostgreSQL RLS as defense in depth using transaction-local context, runtime
roles without BYPASSRLS/superuser/ownership and FORCE RLS where needed. No pooled
session state may leak between requests. Cross-tenant/admin jobs need explicit,
audited authorization, not blanket bypass credentials.

Consequences: fewer databases to operate; composite-FK/RLS tests become mandatory
with the first company model. No tenant tables/RLS policies exist in P0-02, so
isolation is a design commitment, not a certified implementation.

Approvals pending: stakeholder organization/client sharing semantics; security
review of runtime role, RLS and grant resolution in P1. Evidence: SECURITY_RBAC,
ARCHITECTURE, P0-02's public-only route tests.
