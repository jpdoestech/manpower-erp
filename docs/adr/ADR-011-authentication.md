# ADR-011 — Password identity and opaque sessions; MFA plan

2026-11-04. Status: ADOPTED for local P1-01; human security acceptance pending.

CR-001 follow-up: [ADR-012](ADR-012-account-controls.md) supersedes the CLI-only
administration/reset-token exclusions below. Earlier implementation details are
retained here as the original baseline; session/MFA decisions remain in effect.

Options: external IdP, JWT bearer tokens, or server-managed opaque sessions.
Choose local Argon2id passwords and DB-backed opaque cookie sessions for this slice;
one first-party web app needs immediate revocation, not distributed bearer claims.
Keep existing FastAPI/PostgreSQL/React stack. Add argon2-cffi for audited hashing;
do not implement password hashing cryptography. Argon2id minimum 19 MiB/t=2/p=1;
15–128 character passphrases without silent truncation or composition constraints.
Sources: [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html),
[authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html),
[sessions](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

Global UUID user identities are separate from future company memberships/grants.
Successful login grants only self-session access; no company/admin/approval authority.
Operators create/reset/deactivate through a hidden-prompt CLI; no self-registration,
default account, roles payload or public user-management API. Immutable IDs and
soft-disable preserve references for future financial audit trails. Auth events
record subject UUID, event/source, request correlation and time, without credentials
or raw login names. A PostgreSQL trigger rejects UPDATE/DELETE/TRUNCATE. Privileged
DB owners can bypass triggers using DDL; production permissions and tamper
protection require later review. This is not a tamper-proof financial audit ledger.

Tokens have 256 random bits, only SHA-256 digest stored, 8-hour fixed expiry with
no sliding extension. Cookie is host-only, Path=/api, HttpOnly, SameSite=Strict,
Secure by default. HTTP opt-out allowed only for an explicit loopback origin.
Login rotates/revokes the presented session; logout, password reset/change and
deactivation invalidate sessions. Current user exposes its UUID/name and a CSRF
value derived by HMAC-SHA256(key=random session token, message=csrf); it never
exposes the session token. Mutations validate browser Origin and protected mutations
compare CSRF in constant time. Authentication responses are no-store. No CORS
relaxation or localStorage credentials. Missing Origin is allowed for native clients
which still need credentials/CSRF; an untrusted Origin is denied.

DB attempt windows coordinate workers: 5 attempts/name/15 min and 60 total/minute;
short upsert transactions precede password work. Generic 401 errors and dummy
verification avoid straightforward account enumeration. Hash-only throttle keys
and windows need retention/edge DoS controls before production. Limits, 8-hour expiry
and hash cost are initial development controls, subject to measured security review.

MFA PLAN (not implemented): prefer WebAuthn/passkeys or approved IdP; evaluate TOTP
fallback, encrypted secret custody, single-use hashed recovery codes, challenge
expiry/replay protection and rate limits. Enrollment/replacement/reset must require
reauthentication and verified recovery; MFA state must be server-held on sessions.
Before approval/posting privileges exist, define recent step-up requirements and
ensure every sensitive service checks assurance as well as current scoped grants.
Password-only sessions must never be silently treated as MFA verified. Stakeholders
must approve enforcement populations, recovery/helpdesk separation, reset audits,
break-glass, password blocklist, idle/absolute timeouts and deployment/TLS policy.

Consequences: local CLI ownership is an operational trust boundary; no finance,
RBAC or production assurance claim. New identity downgrade must refuse populated
tables; production migration/recovery requires explicit approval. Evidence:
tasks/P1-01.md, identity tests, migration, UI tests and future CI/PR results.
