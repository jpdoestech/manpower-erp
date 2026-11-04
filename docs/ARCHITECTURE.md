# Architecture and Data Governance

## Recommended stack (subject to ADR confirmation)

P0-02 decisions are documented in `docs/adr/` and indexed in `tasks/DECISIONS.md`.
SQLAlchemy/Alembic, session lifecycle, health and diagnostic contracts are the
implemented infrastructure; the domain/security policies below remain design
requirements until their roadmap slices. See `docs/OPERATIONS.md` for commands.
React + TypeScript frontend, Python FastAPI backend, PostgreSQL, managed object storage, background task queue, Docker-based local development. Start as a modular monolith with well-defined module boundaries.

## Modules

CR-002A / ADR-014 adds opt-in local SQLite with shared ORM/Alembic history,
UTC-aware timestamps and conservative serialized local identity transactions.
PostgreSQL remains the production and concurrency authority. Configuration is
explicit; staging/production SQLite is rejected. See DATABASE_MODES.md and
SQLITE_POSTGRES_COMPATIBILITY.md. No company/financial schema is introduced.
Supabase Auth adapters, cloud roles/poolers/Vercel and transfer are C/D/E work.

P1-02 planning is recorded in `tasks/P1-02.md` and proposed ADR-013. It separates
legal companies/client identities from dated branch engagements, contracts/sites,
with company-preserving FKs and explicit bootstrap scope grants. No organization
schema/API/UI exists yet: P1-01 remains REVIEW pending human security acceptance.
ADR-013 is not adopted or implemented; no company access or tax treatment is implied.
identity, organizations, contracts, billing_configuration, billing_execution, payroll_imports, disbursements, approvals, invoicing, general_ledger, receivables, collections, payables, cash_bank, tax, documents, analytics, audit.

## Data model constraints
All company-owned tables: company_id, id, created_at, created_by, updated_at, row version where appropriate. Scoped tables also carry branch_id/client_id/contract_id where operationally appropriate. Avoid redundant dimensions where integrity cannot be enforced: use foreign-key scope validation and well-tested resolver queries. All financial tables reference source document and posting lifecycle. Use NUMERIC(20,4) for intermediate amounts or accounting-specific precision; quantize final posted currency amounts according to approved rounding policy.

Billing definitions and values must be relational/versioned rather than physical column creation per client. Contract, template, formula, tax and GL-mapping versions must be snapshotted on approved/posted documents.

## API and transaction principles
- Consistent REST resource names; published OpenAPI schemas; typed request/response contracts.
- Server-side authorization before reading or mutating scoped records.
- Transactional outbox for reliable side effects after DB commits.
- Idempotency keys and uniqueness constraints for financial posting and import submission.
- Workflow transitions in domain services; no direct status change by generic CRUD.
- Optimistic locking for drafts and approvals; DB row locking for numbering/posting.
- Pagination/filtering; no unrestricted bulk exports.
- Structured audit logging with actor, tenant, entity, before/after metadata, request correlation, approval ID.

## Infrastructure controls
Dev/staging/prod separation; encrypted secrets; automated tests in CI; database migrations in CI; incremental backups and restore drills; logging and alerting for failed posting/imports. Never treat client-controlled request headers as tenant authority.

## Required Architecture Decision Records
ADR-001 Stack; ADR-002 Multi-tenant isolation; ADR-003 Billing versioning; ADR-004 Formula DSL; ADR-005 Approval engine; ADR-006 Financial posting and source-of-truth; ADR-007 Document numbering; ADR-008 Tax configuration. Record alternatives and tradeoffs.
