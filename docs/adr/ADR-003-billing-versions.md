# ADR-003 — Versioned client billing configuration

Date: 2026-11-04. Status: DESIGN ADOPTED; implementation is P3, not P0-02.

Context: contracts under one client can have different billing rules and dates.
Alternatives: DDL per client, mutable JSON formulas, relational/versioned metadata.
Choose typed relational definitions and immutable approved effective-dated template,
formula, tax and GL mapping versions; no DDL per client and no arbitrary eval/SQL.

Drafts may be edited under scoped grants. Approved/published versions are replaced
by new versions through Maker–Checker. Prevent ambiguous overlapping applicability.
Issued documents snapshot exact versions and computed inputs/outputs so historical
results do not change. Client-level defaults do not override contract/site scope
without an approved resolved version. ADR-004's typed sandboxed DSL remains required.

Consequences: more version/snapshot records, but reproducible reporting and no
runtime schema churn. Model approval intervals and corrections before migration.
Finance owner must approve eligibility, effective-date/overlap rules, tax/GL mapping
and rounding fixtures. Nothing in this ADR approves a rate or implements billing.
Evidence: BILLING_STUDIO_SPEC, ACCOUNTING_INVARIANTS, future P3 acceptance tests.
