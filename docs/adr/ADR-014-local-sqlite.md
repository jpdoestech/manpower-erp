# ADR-014 — Opt-in local SQLite, PostgreSQL transactional authority

Status: implementation authorized by CR-002; acceptance pending phase A review.
Automated evidence: implementation 1ff2629, PR #6, all 10 branch/PR checks pass.
Date: 2026-11-04. No security/CPA or deployment acceptance is inferred.

Keep the modular monolith and PostgreSQL production authority (ADR-001/009).
Allow explicitly selected SQLite for local/test identity development, using the
same SQLAlchemy metadata and reviewed linear Alembic history. Never select it as
a fallback. Restrict files to repository `.local`, outside cloud/temp/network
storage. Reject staging/production SQLite. Do not distribute real employee data.

Use SQLite FK enforcement, WAL, bounded busy waiting and explicit BEGIN IMMEDIATE
for every transaction. Serializing even reads is deliberately conservative for
local identity/admin/recovery controls: SQLite ignores PostgreSQL FOR UPDATE and
has no advisory locks. PostgreSQL keeps its current locking/pooling behavior.
No automatic retries of account operations or financial concurrency equivalence.

Use portable UUIDs and UTC-aware timestamps at the ORM boundary. Match current
identity constraints and immutable UPDATE/DELETE audit guards on SQLite; TRUNCATE
is unavailable there. Keep PostgreSQL constraints/triggers unchanged. Future
financial Decimal persistence requires an explicit exact SQLite representation
and dual-dialect tests before any accounting model exists; SQLite NUMERIC affinity
alone is insufficient. No new financial or organization schema in CR-002A.

Migration adaptations are dialect-only, including inline nullable SQLite FKs;
existing PostgreSQL databases retain revision IDs and physical schema. Test clean
installs, populated upgrades, drift, rollback and downgrade refusal. Do not replace
migrations with metadata.create_all. A populated downgrade remains prohibited.

Supabase is a PostgreSQL transport mode requiring TLS; real provider integration,
least-privilege roles/pooler validation and hosting are C/D gates. Until C exists,
AUTH_PROVIDER=supabase must fail explicitly. No default company grants change.
Rejecting unsupported configuration is safer than a fake authentication adapter.

Alternatives: Docker-only development conflicts with the Windows request; replacing
PostgreSQL with SQLite weakens financial concurrency; separate schemas drift.
Cost: serialized local reads and dialect tests. Keep PostgreSQL CI authoritative.
