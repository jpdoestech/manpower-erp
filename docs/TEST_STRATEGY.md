# Test Strategy and Quality Gates

## Test layers
Unit: money/rounding, permissions, formula DAG, workflow transitions. Integration: DB constraints, migrations, transaction posting and idempotency. API: tenant isolation, role scope, pagination and exports. E2E: full billing and AR workflows. Regression: historical versions and tax changes. Security: IDOR, privilege escalation, injection, session controls. Performance: high-volume payroll import and billing tables.

## Canonical scenarios
1. Two independent companies, overlapping external client names, no data leakage.
2. Approver denied on own proposal even if dual-role.
3. One client uses admin fee on selected entries, another fixed-fee only.
4. Formula cycle and divide-by-zero rejected or policy-controlled.
5. Published template v1 still reconstructs historical invoice after v2 is active.
6. Billing mismatch flagged before invoice issuance.
7. Invoice retry creates exactly one GL journal and AR open item.
8. Partial payment and withheld amount reconcile to AR and cash.
9. Negative credits, reversals, and closed period restrictions work.
10. Aging detail + summary toggles work independently; branch subtotals/grand total tie to invoice balances.

## CI minimum
Formatting, lint, type checking, unit tests, integration tests with test PostgreSQL, dependency audit, migration check, authorization regression. Require reviewed fixtures for financial changes; do not claim compliance certification based only on tests.

## UAT gates
Finance staff verifies billing samples against manually approved Excel computations; CPA signs off tax rules; operational user tests reports and exports; security reviewer verifies tenant isolation; release owner approves rollback and restore procedure.
