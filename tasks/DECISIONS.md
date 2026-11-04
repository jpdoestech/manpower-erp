# Decision Log (ADRs Index)

| ID | Decision | Status | Rationale | Owner |
|---|---|---|---|---|
| ADR-001 | React/TypeScript, FastAPI, PostgreSQL modular monolith | ADOPTED FOR INFRASTRUCTURE | Follow existing stack; production deployment remains undecided | Tech lead |
| ADR-002 | Strict legal-company data isolation | DESIGN ADOPTED; IMPLEMENTATION P1 | Cross-tenant disclosure is unacceptable | Security lead |
| ADR-003 | Versioned relational billing metadata rather than DDL-per-client | DESIGN ADOPTED; IMPLEMENTATION P3 | Historical fidelity and safe extensions | Architect |
| ADR-004 | Safe typed DSL, no arbitrary code evaluation | REQUIRED | Prevent computation and code injection | Architect |
| ADR-005 | Scoped Maker–Checker, no self-approval | DESIGN ADOPTED; IMPLEMENTATION P1 | Financial control | Finance owner |
| ADR-006 | Immutable posted ledger, corrective entries | DESIGN ADOPTED; ROUNDING PENDING CPA | Accounting integrity | Finance owner |
| ADR-009 | Explicit transactional Alembic migrations | ADOPTED | Reviewed linear revisions; no worker-startup DDL | Tech lead |
| ADR-010 | Safe health, error and JSON diagnostic contracts | ADOPTED | Useful observability without payload/credential disclosure | Tech lead |
| ADR-011 | Global identity, Argon2id passwords, opaque sessions and MFA plan | ADOPTED FOR P1-01; SECURITY REVIEW PENDING | Immediate revocation, no implied company grants | Security lead |
| ADR-012 | Technical administrators, independent account approval and single-use recovery | LOCAL/HOSTED VERIFIED; HUMAN SECURITY REVIEW PENDING | Add missing P1-01 controls without company RBAC | Security lead |

CR-001: [ADR-012](../docs/adr/ADR-012-account-controls.md) changes ADR-011's
CLI-only boundary under the user's expanded P1-01 request. Additive migration,
false-by-default technical capability, protected two-admin bootstrap, independent
account changes and 15-minute hash-only recovery. Manual verified token delivery,
MFA enforcement, operator dual custody and production settings need security-owner
acceptance. Full multi-company grants remain P1-02/P1-03. See the
[follow-up plan/evidence](P1-01-account-controls.md); no CPA/production decision made.
Implementation `5ca0ad3` in [PR #3](https://github.com/jpdoestech/manpower-erp/pull/3)
passes all six branch/PR checks, including 50 unit/API and 42 PostgreSQL tests,
current-head migration CLI and Linux Docker auth/health/persistence gates.
Verified [push CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41765130592)
and [PR CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41765194928).

P1-01 plan: [ADR-011](../docs/adr/ADR-011-authentication.md). Identity is separate
from company membership and approval authority. MFA/recovery/blocklist/production
policy remains pending security/stakeholder approval. P0-02 was reverified at exact
head 4fd3914 before starting P1-01 on a stacked branch; PR #1 is not merged.
P1-01 implementation `3e4bc82` is in [PR #2](https://github.com/jpdoestech/manpower-erp/pull/2).
Local gates (73 backend/9 frontend tests) and hosted [push CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41759481411)
and [PR CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41759551633) pass.
ADR-011 remains pending human security acceptance; no production assurance implied.

## P0-02 architecture records (2026-11-04)

Detailed decisions, alternatives, tradeoffs and approval boundaries were written
before implementation. Existing IDs remain stable; ADR-007 numbering and ADR-008
tax configuration are reserved for their scheduled owner reviews.

- [ADR-001](../docs/adr/ADR-001-stack.md): modular monolith, PostgreSQL,
  SQLAlchemy 2.x and request-owned sessions. Existing runtime versions retained.
- [ADR-002](../docs/adr/ADR-002-company-isolation.md): shared-schema company scope,
  same-company foreign keys and planned RLS; organization/client hierarchy needs
  stakeholder confirmation before P1-02 schema. No tenant schema implemented here.
- [ADR-003](../docs/adr/ADR-003-billing-versions.md): typed, effective-dated immutable
  billing versions/snapshots; finance approval of applicability still required.
- [ADR-005](../docs/adr/ADR-005-maker-checker.md): deny by default, scoped current
  grants, self-approval prevention; role/delegation/MFA policy approval pending.
- [ADR-006](../docs/adr/ADR-006-financial-integrity.md): immutable posted finance,
  Decimal/NUMERIC; rounding precision/mode/stages remain BLOCKED for CPA approval.
- [ADR-009](../docs/adr/ADR-009-migrations.md): explicit Alembic job, no-op baseline,
  disposable upgrade/downgrade/drift tests and separate production runtime/migrator.
- [ADR-010](../docs/adr/ADR-010-api-diagnostics.md): live/ready, UUID correlation,
  safe error envelopes and whitelisted JSON logs; log-derived metrics design.

Only infrastructure decisions are implemented in P0-02. No stakeholder, CPA,
security/UAT or production deployment approval is implied by these records.
Infrastructure evidence: implementation `b8e3f9e`, [PR #1](https://github.com/jpdoestech/manpower-erp/pull/1),
passing [push CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41752561626)
and [PR CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41752609488).

## New decision format
ID / Date / Context / Options / Decision / Tradeoffs / Consequences / Approver / Links to implementation and tests.

## ADR-001 / 2026-11-04 / Local bootstrap

Context: governance-only repository; P0-01 explicitly authorizes minimal local
app/API/database and CI. Options: recommended React/FastAPI/PostgreSQL stack,
or a single-language rewrite. Decision: use the recommended stack with Node 24,
Python 3.13, PostgreSQL 18, Vite, npm lockfile and uv 0.13.7/uv.lock.
No ORM, queue, storage adapter or domain framework until a task needs it.

Tooling: Ruff/mypy/pytest for Python; Biome/tsc/Vitest for TypeScript. Biome
replaces the initial ESLint/Prettier attempt: its minimatch dependency tree had
11 moderate audit findings; removing that tree leaves a clean npm audit without
breaking transitive overrides. Use httpx2 for the current Starlette test client;
httpx triggers a deprecation warning. Lockfiles record actual resolved versions.

Tradeoffs: two runtimes, but no replacement architecture to maintain. Compose
serves Vite for local development; it is not a production web server. Python/Node
major/minor base image tags receive patches and are not byte-reproducible OS
images; language dependency graphs are locked. Pin deployment image digests in
the release task after security review. API bootstrap is static public metadata,
not a database readiness or compliance claim. Only tests access PostgreSQL for
now; no schema/migrations before P0-02.

Approver: implementation engineer under the user's P0-01 authorization; no
production architecture or regulatory approval asserted.
Evidence: `tasks/P0-01.md`, `backend/pyproject.toml`, `frontend/package.json`,
`compose.yaml`, `backend/tests/`, `frontend/src/App.test.tsx`, CI workflow.
