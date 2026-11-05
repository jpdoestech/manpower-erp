# ADR-015 — Windows local lifecycle and SQLite recovery

Status: authorized CR-002B implementation; review/acceptance pending. 2026-11-04.

Extend the existing native helper and BATs. Keep current backend/frontend/auth and
PostgreSQL behavior. No cloud deployment or financial/business schema.

A held Windows file lock proves a checkout's live supervisor. A random instance
marker scopes cooperative stop requests; no persisted PID can authorize killing.
Only original live Popen handles authorize child-tree cleanup. Unmanaged listeners,
stale state, links and concurrent offline tools cause safe refusal. Old launchers
without the protocol must stop using their own Enter before upgrading runtime.

Backups use SQLite's backup API, including committed WAL state, under a tools lock.
Store snapshots outside active .local in ignored .local-backups. Validate integrity,
FKs, revision and required identity/audit guard presence. Restore further runs the
current migration/schema check against an isolated candidate before replacement.

Reset/restore are offline, fixed-target, typed-confirmation operations. Preserve a
validated pre-change recovery snapshot, prepare/verify a candidate, checkpoint and
close connections, then atomically replace. Never manually delete active sidecars.
Cancellation/failure preserves active data or a verified recovery backup; no
automatic downgrade, arbitrary database import or cloud URL selection.

Restore preserves identities/historical audit UUIDs and appends a local restore
event; it revokes restored sessions/password-reset tokens and expires pending
account-change requests. A snapshot must not revive revoked authentication powers.
Passwords/capabilities otherwise reflect the selected local snapshot. Recovery
snapshots retain the pre-restore history. This is synthetic local recovery, not a
production accounting rollback or a financial audit design.

Cost: local filesystem custody and exclusive offline windows; backups contain
unencrypted sensitive hashes/history and are never committed/shared. Only current
revision trusted local snapshots are supported. Corrupt/incompatible active data
that cannot produce a validated recovery snapshot is refused rather than erased.
Mapped network/cloud-sync storage remains an operator restriction.

Alternatives: PID-file taskkill risks PID reuse/unrelated processes; copying live
SQLite files loses WAL state; in-place restore weakens failure recovery. Production
role separation, encrypted backup policy and self-host transfer remain D/E reviews.
