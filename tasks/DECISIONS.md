# Decision Log (ADRs Index)

| ID | Decision | Status | Rationale | Owner |
|---|---|---|---|---|
| ADR-001 | React/TypeScript, FastAPI, PostgreSQL modular monolith as initial recommendation | PROPOSED | Pragmatic web-first architecture; validate against deployment constraints | Tech lead |
| ADR-002 | Strict legal-company data isolation | REQUIRED | Cross-tenant disclosure is unacceptable | Security lead |
| ADR-003 | Versioned relational billing metadata rather than DDL-per-client | REQUIRED | Historical fidelity and safe extensions | Architect |
| ADR-004 | Safe typed DSL, no arbitrary code evaluation | REQUIRED | Prevent computation and code injection | Architect |
| ADR-005 | Scoped Maker–Checker, no self-approval | REQUIRED | Financial control | Finance owner |
| ADR-006 | Immutable posted ledger, corrective entries | REQUIRED | Accounting integrity | Finance owner |

## New decision format
ID / Date / Context / Options / Decision / Tradeoffs / Consequences / Approver / Links to implementation and tests.
