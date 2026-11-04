# Codex Operating Contract — Philippine Manpower Accounting ERP

## Mission
Implement a secure multi-company ERP for Philippine manpower service contractors with company > head office > branch > client > service contract > deployment/site, flexible client billing, Philippine accounting, and controlled tax configurations.

## Mandatory session sequence
1. Read this file, `docs/PRODUCT_BLUEPRINT.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY_RBAC.md`, `docs/ACCOUNTING_INVARIANTS.md`, `docs/COMPLIANCE_REGISTER.md`, `tasks/ROADMAP.md`, `tasks/STATUS.md`, and `tasks/DECISIONS.md`.
2. Inspect actual repository code and Git status; never infer implementation solely from task reports.
3. Pick the next unblocked task. Write/update its plan and acceptance tests before coding.
4. Execute one small vertical slice: migration -> domain -> service -> API -> permission -> UI -> tests -> docs.
5. Run linters, type checks, unit/integration tests and migration checks; record exact commands/results.
6. Update `tasks/STATUS.md` with completed work, evidence, open risks, next task, and changed files. Never mark a task Done with failing or missing mandatory tests.
7. Never commit secrets. Do not push, deploy, overwrite production data, or generate fiscal documents in production without explicit authorization.

## Non-negotiable engineering rules
- Company isolation on every company-owned record, query, export, background job and API; deny by default.
- Branch/client/contract resource scoping; permissions enforced server-side; frontend hiding is insufficient.
- Separation of duties: creator cannot approve own item, including users holding both roles; authorization rechecked at approval time.
- Approved configuration is immutable; changes create a new effective-dated version. Posted financial documents are never edited in place.
- Journal entries always balance; monetary calculations use Decimal/NUMERIC, never floating point.
- Document posting must be idempotent; duplicate API retries must not duplicate invoice or ledger entries.
- Use stable relational columns for identity; dynamic billing fields belong in versioned definitions and values, not DDL-per-client.
- No arbitrary eval/exec/SQL execution for formulas. Use a typed, sandboxed DSL with dependency graph and cycle detection.
- Every accounting/tax rule records its source, scope, valid-from/to dates and approval; uncertain legal matters stay blocked for accountant review.
- Use migrations and reversible deployment plans; protect historical reporting and preserve immutable audit trails.

## Definition of Done
Acceptance tests documented; security and tenant-isolation tests pass; financial reconciliation verified when relevant; migrations reviewed; observability/logging added; role/access matrix updated; docs and STATUS current; no unresolved critical bugs.

## If blocked
Document what is unknown and the safest assumption in `tasks/STATUS.md`; do not invent tax rates, authority, account mappings, or final BIR classifications. Continue with a non-blocked task.

## Suggested first instruction to Codex
Read AGENTS.md and all referenced documents. Inspect repository. Execute ONLY task P0-01 from ROADMAP, produce a short implementation plan, then implement and test it. Do not start other tasks. Update STATUS.md and provide evidence.
