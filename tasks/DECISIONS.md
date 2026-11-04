# Decision Log (ADRs Index)

UI-001 (explicit request, 2026-11-04): [ADR-016](../docs/adr/ADR-016-ui.md)
retains React/TypeScript/Vite and native HTML + shared CSS tokens after evaluating
Tailwind/headless alternatives. Add dev-only Playwright/axe for real viewport,
keyboard and accessibility regressions. AuthPanel remains session/CSRF authority;
context/admin controls stay unavailable without backend scope/capability evidence.
Phone/tablet/laptop/large-screen layouts share primitives, with touch targets and
safe-area navigation. No business logic, role grant or pending acceptance bypass.

CR-002B completion (explicit request, 2026-11-04):
[ADR-015](../docs/adr/ADR-015-local-recovery.md) uses held Windows locks and scoped
cooperative stop instead of PID-file authority; SQLite backup API and validated,
confirmed offline candidate replacement with pre-change recovery snapshots.
Restore revokes ephemeral authentication capabilities and records a local audit
event while retaining historical UUIDs. No PostgreSQL/auth policy weakening or
production recovery assertion. C is planned only in CR-002C.md; its implementation
requires B acceptance. Pending P1-01 human reviews are unchanged.
Source 22b437b in [PR #9](https://github.com/jpdoestech/manpower-erp/pull/9)
passes all 10 matching-head branch/PR checks, including the complete fresh Windows
nine-command workflow and real PG regressions. ADR-015 implementation is verified;
B remains REVIEW pending acceptance. No C implementation or human approval inferred.

2026-11-04 subsequent user request explicitly authorizes Docker-free setup/start
BATs now. Implement only that B slice, stacked on verified A (65246ba), without
manufacturing formal A/P1-01 acceptance. Keep Docker launchers intact; add
setup-local.bat/start-local.bat and one standard-library Python helper. Force
local child configuration, retain .env/data, no default account/admin grants,
wait for readiness, stop only owned live processes. Full B and C/D/E stay pending.
Requested slice `d38a034` in [PR #7](https://github.com/jpdoestech/manpower-erp/pull/7)
passes 10/10 branch/PR checks, including real native Windows BAT smoke. It is
ready for review; no formal A/P1-01 acceptance or production assurance is inferred.

CR-002A: [ADR-014](../docs/adr/ADR-014-local-sqlite.md) authorizes explicit local
SQLite compatibility while retaining PostgreSQL production constraints/locking.
No security/CPA/deployment approval is implied. A requires review before B;
P1-01 human acceptance remains pending. Python 3.13.18 is pinned because the old
local 3.13.12 bundled SQLite 3.50.4 affected by the upstream WAL-reset advisory;
require a patched runtime, keep application dependency locks unchanged.

ADR-014 implementation `1ff2629` passes 10/10 branch/PR checks in
[PR #6](https://github.com/jpdoestech/manpower-erp/pull/6). SQLite and PostgreSQL
migrations/security regressions pass; this is automated evidence, not phase-A or
P1-01 human acceptance. Phase A remains REVIEW; B/C/D/E have not started.

Windows contributor tooling (user request, 2026-11-04): keep existing Compose
runtimes and add setup.bat/run.bat instead of another native installer/service
manager. Pin local default Docker context/file/project, generate a DB secret only
when .env is absent, and reuse existing hidden-prompt ordinary-account CLI. No
default account, Super Admin/company grant or volume deletion. Plan/limits:
WINDOWS_LOCAL_DEV.md. This does not change pending human acceptance or ADR-013.

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
| ADR-013 | Company identities, dated branch engagements and explicit bootstrap scopes | PROPOSED ONLY; P1-02 PREREQUISITE BLOCKED | Shared client identity with company isolation; no implicit technical-admin access | Security/architecture reviewers |

User confirmation: no human P1-01 security acceptance exists yet. The formal
[security acceptance checklist](SECURITY_ACCEPTANCE_P1-01.md) has independent
PR #2/#3 records both PENDING HUMAN REVIEW; no reviewer/date/approval/reference is
invented. ADR-011/012 remain pending human acceptance, ADR-013 remains proposed,
and P1-02 remains blocked at prerequisite. Only actual qualified reviewer evidence
and verified conditions may change those decisions; passing CI alone cannot.

P1-02 proposal: [ADR-013](../docs/adr/ADR-013-organizations.md) and
[task plan](P1-02.md). Fresh fetch/CI diagnostics confirm all three prerequisite PRs
are open/unmerged with matching-head 6/6 checks. P1-01 #2/#3 have no recorded reviews
and remain REVIEW. No security acceptance is inferred from CI or the P1-02 request.
No organization schema/runtime permission has been adopted or implemented.

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
