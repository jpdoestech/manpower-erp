# SQLite / PostgreSQL compatibility contract

Implemented schema: global identity, sessions, throttles, immutable authentication
events, independent account changes and hashed single-use recovery. Company,
branch, billing, payroll, GL and AR models do not exist yet.

| Concern | SQLite local | PostgreSQL |
|---|---|---|
| UUID | SQLAlchemy Uuid CHAR(32), canonical hex guards | Native UUID, same identities |
| Timestamps | UTC text storage; UTCDateTime restores aware UTC | TIMESTAMPTZ; normalize to UTC |
| Boolean/length | Local triggers reject invalid current identity fields | Native Boolean/VARCHAR bounds |
| Username | Equivalent ASCII GLOB/length/NUL check | Existing regex constraint retained |
| FK / uniqueness | FK pragma each connection, existing keys/indexes | Existing relational constraints |
| Audit immutability | UPDATE/DELETE row triggers, recursive triggers prevent REPLACE bypass; no TRUNCATE | Existing UPDATE/DELETE/TRUNCATE statement trigger |
| Throttle | SQLite atomic on-conflict upsert | Existing PostgreSQL on-conflict upsert |
| Account serialization | BEGIN IMMEDIATE for all transactions | Existing advisory transaction lock / FOR UPDATE |
| Transaction errors | Explicit begin, close/rollback; 10-second busy wait | Existing pool/pre-ping/timeouts and rollback |
| Migrations | Shared revisions, dialect-only inline nullable FK additions | Existing physical schema unchanged; 0004 is a no-op |

No create_all, schema reset, automatic retry or unsafe migration fallback. Revision
0004 validates existing SQLite data before adding length/Boolean triggers. Failed
DDL rolls back atomically. Existing 0002/0003 have additive SQLite branches; their
PostgreSQL paths and revision IDs are retained. Downgrades refuse identity/audit
or account-control data/grants that would be lost. Supported SQLite versions have
native DROP COLUMN; these revisions need no copy/rebuild. Future batch rebuilds
must explicitly preserve triggers, indexes, FKs and historical rows.

Schema drift checks do not inspect trigger bodies: direct mutation/constraint
tests are mandatory alongside `alembic check`. No SQLite test proves PostgreSQL
concurrency, row security or production readiness. Local file owners can bypass
DDL guards, just as the current PostgreSQL development owner can; production
least-privilege migrator/runtime roles remain a D/security gate.

## Deferred features and required tests

| Future surface | Current evidence | Required before implementing |
|---|---|---|
| Company/scoped RBAC | NOT IMPLEMENTED | Both dialects: deny-by-default cross-scope FK/API/export tests |
| Financial amounts | NOT IMPLEMENTED | Exact Decimal persistence/calculation/round-trip; approved precision and balance tests |
| Posting/numbering/idempotency | NOT IMPLEMENTED | Real PostgreSQL concurrent retries and immutable postings; local sequential equivalents |
| Billing/payroll/AR simulations | NOT IMPLEMENTED | Both dialects: version/date/rollback/reconciliation fixtures |
| JSON / sequences / schemas | Not used by current models | Explicit portable mapping and migration fixtures if introduced |
| Supabase Auth | NOT IMPLEMENTED (C) | Real JWT/JWKS/mapping/revocation tests; no implicit scopes |
| Supabase hosted DB/poolers | Configuration only (D) | TLS, role separation, direct/session/transaction pooler checks |
| Transfer/self-hosting | NOT IMPLEMENTED (E) | Versioned dry-run/export/import verification, preserve UUID/audit/Decimal |

Do not use SQLite NUMERIC affinity as an exact financial representation. Future
financial models must choose an exact local encoding (for example fixed-scale
integer or validated decimal text) and test against PostgreSQL NUMERIC. This phase
does not settle CPA precision or implement financial data types prematurely.

References: [SQLAlchemy SQLite transactions/types](https://docs.sqlalchemy.org/en/21/dialects/sqlite.html),
[Alembic batch migrations](https://alembic.sqlalchemy.org/en/latest/batch.html),
[SQLite WAL constraints and advisory](https://www.sqlite.org/wal.html).
