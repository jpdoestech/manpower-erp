# ADR-001 — Modular monolith and PostgreSQL

Date: 2026-11-04. Status: ADOPTED for infrastructure; deployment approval pending.

Context: one ERP with strong transactional accounting boundaries, no business
modules yet. Alternatives: microservices, a single-language rewrite, existing
React/TypeScript + FastAPI + PostgreSQL. Decision: retain the existing stack as a
modular monolith; one API deployable and transactional PostgreSQL database.

Future domain modules listed in ARCHITECTURE own their services/models; route
handlers delegate workflow changes to services, which own transaction boundaries.
Cross-module financial writes must remain in one database transaction where
atomicity is required. Do not add empty module packages, queues or adapters now.
Use SQLAlchemy 2.x with psycopg and request-scoped sessions; no global session or
implicit request commit. Dispose each worker's connection pool on shutdown.

Consequences: lower operational cost, explicit module boundaries needed as code
grows. PostgreSQL supplies transactional DDL, NUMERIC, constraints and future RLS.
Microservices would increase failure/consistency complexity without a current need.

Approver: implementation engineer under P0-02 authorization. Hosting, capacity,
backup/restore, credentials and production deployment need release-owner/security
approval. No production environment is selected or provisioned.
Evidence: `backend/app/database.py`, `backend/alembic/`, `compose.yaml`.
