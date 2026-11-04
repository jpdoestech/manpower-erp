# Codex Roadmap — Small, Testable Vertical Slices

Status values: TODO, IN_PROGRESS, BLOCKED, REVIEW, DONE. Each task gets a PR/change set; no more than one task in progress per agent unless explicitly coordinated. Dependencies must be DONE before task starts.

| ID | Task | Depends on | Acceptance gate |
|---|---|---|---|
| P0-01 | Bootstrap repository, lint/test/CI, env example, Docker local dev | — | Fresh checkout boots and CI passes |
| P0-02 | ADRs, migrations framework, healthcheck, observability | P0-01 | Migration up/down on disposable DB; healthcheck works |
| P1-01 | Auth, user, session, MFA plan | P0-02 | Authentication unit/integration tests |
| P1-02 | Company/head-office/branch/client/contract/site models | P1-01 | Scope FK and CRUD integrity tests |
| P1-03 | Scoped RBAC and approval framework | P1-02 | Maker/self-approval and cross-tenant tests |
| P2-01 | CoA, periods, journal drafts, double-entry validator | P1-03 | Unbalanced posting rejected |
| P2-02 | GL posting, reversal, idempotency, locking | P2-01 | Repeated requests post exactly once |
| P3-01 | Entry definitions/template versioning + approval | P1-03 | New client column without schema migration |
| P3-02 | Formula DSL + dependency DAG + trace | P3-01 | Cycles/unsafe expressions rejected |
| P3-03 | Billing simulation, fee rules and variance validation | P3-02 | Fixtures for 4 billing models |
| P4-01 | Payroll import and allocation controls | P1-03 | Invalid files quarantined; reconciliation |
| P4-02 | Disbursement monitoring and variance | P4-01,P3-03 | Trace each release to source |
| P5-01 | Billing draft workflow and invoice issuance | P3-03,P2-02 | Issuance once, immutable snapshots |
| P5-02 | Tax-rule versions and invoice tax mapping | P5-01 | CPA-reviewed fixtures; no hardcoded tax assumptions |
| P6-01 | AR subledger and receivable aging | P5-01,P2-02 | Buckets reconcile with GL |
| P6-02 | Receipts, withholding allocations, credits | P6-01 | Partial payment and CWT tests |
| P6-03 | Detail/summary reports, branch subtotal/grand total | P6-02 | Totals tie to AR; switches independent |
| P7-01 | AP/cash/bank reconciliation | P2-02 | Controls and bank reconciliation fixtures |
| P7-02 | Trial Balance / financial statements / closing | P7-01,P6-03 | Tie out and period locks |
| P8-01 | Hardening, backups, performance, UAT, deployment | all critical | Signed UAT, restore drill, security review |

## Task lifecycle
TODO -> IN_PROGRESS (write task plan/tests) -> REVIEW (tests plus evidence) -> DONE (human acceptance for high-risk changes). BLOCKED includes reason and next action.

## Priority note
P2 (GL foundation) and P3 (billing configuration) may progress as separate workstreams after P1, but financial posting integration requires both ready. Tax compliance work is cross-cutting and begins in design, not after release.
