# Decision Log (ADRs Index)

| ID | Decision | Status | Rationale | Owner |
|---|---|---|---|---|
| ADR-001 | React/TypeScript, FastAPI, PostgreSQL modular monolith | ADOPTED FOR LOCAL BOOTSTRAP | Follow recommended stack; production deployment remains undecided | Tech lead |
| ADR-002 | Strict legal-company data isolation | REQUIRED | Cross-tenant disclosure is unacceptable | Security lead |
| ADR-003 | Versioned relational billing metadata rather than DDL-per-client | REQUIRED | Historical fidelity and safe extensions | Architect |
| ADR-004 | Safe typed DSL, no arbitrary code evaluation | REQUIRED | Prevent computation and code injection | Architect |
| ADR-005 | Scoped Maker–Checker, no self-approval | REQUIRED | Financial control | Finance owner |
| ADR-006 | Immutable posted ledger, corrective entries | REQUIRED | Accounting integrity | Finance owner |

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
