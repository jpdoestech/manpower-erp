# ADR-017 — Provider-independent identity with a protected Supabase session bridge

2026-11-04. **PROPOSED ONLY. No implementation/security acceptance granted.**
The user authorizes technical planning; CR-002B and P1-01 review gates remain.

## Context and options

Existing local authentication uses Argon2id, hashed opaque sessions, Origin/CSRF,
independent technical administration and recovery. UI-001 consumes that contract;
SQLite native tooling must stay offline and PostgreSQL remains production authority.
Supabase database transport exists; Supabase Auth does not.

Options: replace local auth (violates requirements); browser-persisted provider
tokens/direct database access (changes custody and authorization boundary); or
explicit provider adapters behind the existing FastAPI session surface.

Recommend adapters plus a backend-owned opaque-cookie bridge. Cloud JWTs use
strict project-pinned asymmetric verification and live provider/ERP state checks;
encrypted server-side refresh custody and durable multiworker rotation replace
neither local hashes nor local cookie semantics. No raw JWT business-route bypass.
Browser SDK token persistence is not the default; any different flow needs review.

## Proposed invariants

- Authentication provider is independent of DB host/dialect. No silent fallback.
- Internal ERP UUIDs remain history/membership keys. Explicit independently approved
  provider+issuer+subject mappings, no email matching or automatic administrator.
- Authorization resolves current ERP grants/scopes with deny by default; no provider
  metadata, company selector or technical admin blanket business access.
- Cloud external-only users have no local password credential. Review nullable-hash
  migration/SQLite guard preservation; never invent passwords or auto-enable local
  recovery for an external-only account.
- Immediate ERP revocation, approved live external-session check, finite expiry;
  no signature-only claim of logout/revocation enforcement. Refresh races and lost
  remote responses cannot resurrect a revoked session.
- Existing Maker–Checker and audit invariants apply to provider linking/provisioning
  and recovery. Approval and remote application are different durable outcomes.
- Same-origin cookie/CSRF architecture, durable PostgreSQL and bounded calls permit
  later Vercel/self-host hosting. D/E retain deployment/transfer acceptance.

## Tradeoffs / blockers

The bridge avoids browser token persistence but introduces encrypted secret custody,
key rotation and refresh coordination. Live provider checks trade availability and
latency for revocation assurance; their least-privilege mechanism is not proven yet.
External mutations need reconciliation because ERP and Supabase cannot commit one
transaction. These are prerequisites, not accepted shortcuts.

Required decisions C-D1–7 and gates G1–7: tasks/CR-002C.md. Technical details and
primary sources: docs/AUTH_PROVIDER_STRATEGY.md. Verification of existing work:
tasks/CR-002C-READINESS.md. No new dependency, migration or runtime interface exists.

Approver/reviewer/date/reference: **not supplied**. No signatures or approvals
invented. ADR-011/012/014/015/016 remain in effect; this proposed ADR supersedes
none until actually reviewed/adopted. Implementation stays NOT STARTED.
