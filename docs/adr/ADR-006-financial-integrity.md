# ADR-006 — Immutable finance, precision and rounding

Date: 2026-11-04. Status: DESIGN ADOPTED for integrity; rounding policy BLOCKED
pending finance-owner/CPA approval. No financial schema or computation in P0-02.

Alternatives: mutable posted balances with float arithmetic, or immutable source
documents/journals with Decimal/NUMERIC. Choose the latter. Posted entries and
approved snapshots cannot be edited in place; authorized corrections create linked
reversal/adjustment records. Explicit company/period/source/version references,
balanced journals, uniqueness/idempotency constraints and transactional posting
protect ledger consistency. AR remains reconcilable to the GL control account.

All monetary input uses decimal strings → Decimal → PostgreSQL NUMERIC; never
binary float. NUMERIC(20,4) is the architecture's proposed intermediate precision,
not a universally approved storage/rounding rule. Reject out-of-range values rather
than silently truncate. Preserve original precision and declared calculation stages.

Do not select an implicit rounding mode or quantize financial values until the CPA
approves currency scale, intermediate precision, rounding mode, tie behavior,
per-line vs aggregate/tax rounding, residual allocation and negative/reversal cases.
Version and snapshot that policy with effective dates and manually approved fixtures.
Tax applicability, rates, GL mapping and document numbering remain separately
blocked for their owners (future ADR-007/008), not inferred from this architecture.

Consequences: immutable history and reproducibility need explicit correction paths
and reconciliation tests in P2 onward. Database privileges/constraints must reinforce
immutability; API checks alone are insufficient. No accounting-policy approval is
asserted. Evidence: ACCOUNTING_INVARIANTS and future finance acceptance tests.
