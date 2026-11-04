# Authentication provider strategy — CR-002C proposal

2026-11-04. **PROPOSED; NOT IMPLEMENTED OR SECURITY-ACCEPTED.**
Read ADR-011/012/014/015/016 with proposed ADR-017 and tasks/CR-002C.md.
All ERP behavior below is a recommendation, not a statement of existing support.

## Boundaries and supported combinations

| ERP database | Identity provider | Intended use |
|---|---|---|
| SQLite, explicit local/test | local | Existing offline Windows workflow; unchanged |
| PostgreSQL, including self-hosted | local | Existing local/CI path; production still requires release review |
| PostgreSQL, Supabase-hosted or self-hosted | supabase | New cloud provider path, after acceptance |
| SQLite test fixtures | supabase test adapter | Deterministic contract tests only, not cloud deployment |
| SQLite on Vercel/staging/production | either | Rejected, never a fallback |

AUTH_PROVIDER and DATABASE_MODE are independent explicit server settings. The
current provider rejects anything except local; database mode supabase is TLS
transport only. A failed cloud login must never try the local password database.
Native BAT child settings force local+SQLite and need no Supabase account/network.
New cloud settings must remain unused in local mode; tests assert no outbound calls.

## Recommended browser/session flow

Use FastAPI as the only session/refresh owner. React talks to same-origin /api;
the browser holds the current opaque HttpOnly ERP cookie, not Supabase tokens.
Retain host-only Path=/api, SameSite=Strict, Secure outside explicit loopback,
no-store responses, Origin checks, HMAC CSRF and existing local absolute expiry.
No Supabase database/storage access directly from the browser in this slice.

1. Public safe metadata identifies configured login presentation only. Local
   username/password payloads remain unchanged. Cloud mode uses a separate typed
   email/password payload for the approved provider flow. The server chooses its
   configured adapter; client provider/issuer/role fields cannot override it.
2. Backend limits attempts before provider calls. Successful cloud password proof
   produces tokens privately; verify JWT, live provider session/user and approved
   ERP link before creating any ERP cookie. Unknown/unapproved users get generic
   denial and no automatic ERP user. Supabase email is not the ERP username/key.
3. Rotate presented ERP session as today. Bind new session to internal user UUID,
   provider+issuer+subject+provider session ID and immutable mapping. Store only
   the opaque ERP cookie digest; never return provider tokens in SessionView.
4. Each protected request rechecks ERP user/session/link activation/revocation,
   verified provider access-token validity, approved live provider state and any
   required assurance. Expired proof cannot be replaced by trusting decoded claims.
   No company access follows from any of these steps.
5. Refresh is an explicit CSRF/Origin-protected POST, not a mutation hidden inside
   GET /me. After reload, a minimal no-store session-state endpoint may validate
   the still-live ERP cookie and return CSRF plus needs_refresh only; it returns
   no user data, grants or authenticated business principal before provider proof.
   This avoids a CSRF bootstrap deadlock when cloud access JWT has expired.
6. Logout must still revoke the ERP session when provider access has expired or the
   provider is unavailable. An own-session-only resolver supports logout/refresh,
   never company/admin actions. Persist local revocation first; record failed remote
   sign-out for controlled reconciliation, clear cookie and deny ERP replay.
7. Keep the existing eight-hour ERP absolute limit across refreshes; do not silently
   renew it indefinitely. UI reload/expiry states revalidate through backend /me;
   no fake session and no stale privileged page while proof is unavailable.

Provider tokens must be recoverable for refresh: hashes alone are insufficient.
Use reviewed authenticated encryption with a maintained library and externally
managed versioned keys, bound by associated data to issuer/link/session/field.
No plaintext token columns, environment dump, localStorage/sessionStorage, shared
SDK global user state, credentials in URLs or VITE_* secrets. Encryption keys stay
outside the DB and backups; rotation/re-encryption and key-loss response must be
tested. Do not invent bespoke encryption or silently store refresh tokens in clear.
Local mode never requires this encryption key or changes password hashing.

The bridge is an ERP design choice. Supabase's browser/SSR guide assumes client
access to provider tokens; its cookie guidance is not a drop-in design for this
server-only bridge. See [Supabase advanced guide](https://supabase.com/docs/guides/auth/server-side/advanced-guide).

## JWT verifier contract

Only a maintained, pinned, reviewed JWT/crypto library verifies signatures. The
adapter accepts tokens only from the configured Supabase Auth endpoint; it does
not expose a generic token-decoding login endpoint or enable bearer bypasses.

- Exact configured HTTPS issuer and trusted project JWKS URL; derive only from
  validated server configuration. Never discover URLs from unverified iss, jku,
  x5u or kid. No redirects to another origin, private-network URLs or HTTP fallback.
- Explicit algorithm/key pairing, proposed ES256 initially. RS256 only under
  reviewed configuration. Reject none, HS256/legacy shared secrets, algorithm
  confusion, unexpected key usage/type/curve and ambiguous duplicate kid entries.
- Require bounded token/header sizes; validate signature before trusting claims.
  Require typed iss/aud/exp/iat/sub/session_id/aal and non-anonymous user proof;
  verify nbf if present. Reject boolean/nonfinite/string timestamps, future iat,
  expiry, unknown assurance, missing session/user and unapproved audience.
  Proposed clock leeway <=30s and maximum token age/lifetime require review.
- Require Supabase sub/session_id UUIDs and exact binding to linked provider
  subject/session; these are not the internal ERP user ID. Authenticated provider
  role is a token-class check only, not an ERP role. Reject anonymous, API,
  service-role and secret keys as user credentials. Ignore user/app metadata for
  ERP privileges even if signed. MFA assurance must be verified and fresh for the
  operation; aal1 is never promoted to aal2 by UI state.
- Bounded HTTPS fetch, response/key count limits, cache age and negative-kid
  cooldown. Proposed initial limits: 2s network timeout, 64KiB body, 16 keys,
  60s local freshness and one rate-limited unknown-kid refresh. Validate against
  the real project before adoption. Expired cache/outage/invalid JWKS fails closed;
  fresh keys still require live provider-session checks. No infinite stale-key use.
- Warm-worker caches are performance only. Rotation tests cover overlap, new kid,
  removed key, multiple workers and cold start. Emergency issuer/key deny-list and
  configuration generation must be durable or force a verified worker rollout;
  clearing one worker's memory is not fleet-wide revocation. Upstream cache delay
  cannot be wished away by a shorter local TTL.

Supabase publishes asymmetric project keys at its JWKS endpoint; its documentation
describes edge/client caching and emergency rotation concerns. The limits and
fail-closed policy above are ERP proposals, not provider guarantees.
[JWT contract](https://supabase.com/docs/guides/auth/jwts),
[key rotation](https://supabase.com/docs/guides/auth/signing-keys),
[claims](https://supabase.com/docs/guides/auth/jwt-fields).

## Durable refresh and revocation

One server owns a provider session's refresh state. Persist encrypted token pair,
provider session ID, expiry, generation and bounded refresh-attempt state. Use
short DB compare-and-swap/lease transactions for worker/tab coordination; never
hold SQLite BEGIN IMMEDIATE or a PostgreSQL approval lock during network I/O.
Never automatically retry an ambiguous provider mutation as if it were read-only.

Claim a generation, call provider with bounded timeout, verify returned issuer/
subject/session, then atomically replace encrypted tokens only for that generation.
Logout/deactivation wins races: recheck session/link/user before publishing success.
If the provider rotated but DB commit/response was lost, invalidate the ERP bridge
and require fresh proof or reviewed reconciliation; do not resurrect old tokens or
promise a distributed atomic commit. Persist attempts without raw token material.

Supabase rotates refresh tokens with documented reuse exceptions; do not assume
that every second refresh is rejected immediately. Test documented grace/parent
recovery behavior and reuse outside it with the real configured project. Provider
JWTs can outlive sign-out; the session_id/auth.sessions relationship offers a
provider-session check, but the ERP must prove a narrowly privileged access method.
[Provider session semantics](https://supabase.com/docs/guides/auth/sessions).

Proposed strict policy: live session existence plus provider user eligibility on
every protected cloud request; timeout/denial fails closed. A JWT or getUser alone
does not prove session existence. Select a reviewed narrowly privileged provider
check/function or trusted equivalent; never grant the ERP runtime unrestricted
auth schema/table access, reuse a migration owner or expose a privileged key to UI.
If this cannot be implemented, C-D4 remains blocked pending an explicit alternate
revocation-latency policy. No claim of immediate external revocation is permitted.
Immediate ERP revocation remains required regardless of external availability.
Session-row existence must also be distinguished from enforced provider timeout
policy: validate time-box/inactivity eligibility and any delayed cleanup behavior
with the chosen project. A surviving row is not proof that every configured limit
has been enforced. ERP absolute expiry stays authoritative for ERP access.

## Internal identity mapping and migration safety

Recommended external link: stable UUID, provider, canonical exact issuer, subject,
internal user_id FK, independent request/approval references, approved/revoked
timestamps and safe audit correlation. Unique (provider, issuer, subject), one
approved subject per user per issuer in this slice; no routine reassignment.
Identifiers/approved binding immutable; relinking is a new independently reviewed
operation with retained history, not an email update. Disable retains references.

Existing User.password_hash is NOT NULL. Recommended expand migration makes it
nullable for external-only identities; local login/change/CLI must explicitly deny
missing local credentials, never manufacture a usable password or cloud fallback.
Existing non-null hashes, UUIDs and audit rows remain byte-for-byte intact. Local
reset must not implicitly enable a credential on an external-only user. A later
local-credential enrollment/cutover requires separately approved proof and audit.

Provider link/session tables use portable UUID/UTC/FK constraints and restrictive
deletion. An external identity is pending/inactive until independent approval.
No automatic local-to-cloud migration, email linking, new Super Admin grant or
FK from financial data to Supabase auth.users. Internal user UUID remains authority
for history and future membership, regardless of provider or DB host.

SQLite may need a reviewed auth_users table rebuild to relax nullability. Explicitly
recreate every index/FK/identity-length and immutable-audit guard; test failures and
populated preservation, not just Alembic drift. Refuse populated downgrade that
would lose links/provider history or external-only users. Restore validation must
recognize the new revision/guards; restoring revokes all cloud bridge/refresh/
proof state and pending remote operations without calling cloud automatically.
Old snapshots remain subject to B's current-revision-only recovery rule; cross-
revision transfer is E, not a silent relaxation of backup acceptance.

## Provider-independent services, authorization and account controls

Keep a narrow principal value with internal user UUID, ERP session identity,
provider identity and verified assurance/proof time. Provider adapters own login,
verification, reauthentication, refresh and remote credential/revocation effects.
Business authorization consumes the internal principal/current DB policy; raw JWT,
remote SDK User, email or claims must not become a business permission interface.
CSRF/cookie handling stays at the authentication boundary, not every domain service.

Future scope input is typed Company / Head Office / Branch / Client / Contract,
resolved from the resource and current ERP grants. The resolver for C denies all
company actions because no memberships exist; it must not accept company IDs from
tokens, headers or selector state as proof. Technical Super Admin remains identity
administration only. Cross-company data/FK/RLS certification awaits P1-02/P1-03.
Do not create a general RBAC framework or synthetic company rows to claim isolation.

Inventory administration.reauthenticate/require_admin, local CLI/bootstrap,
password/reset, session revocation and approvals before provider branching.
Current password verification is local-specific and cannot be reused against
Supabase-only accounts. Cloud proof must verify the same approved subject and
recent method/assurance; any temporary provider reauthentication session must be
reconciled/revoked and must not silently create another ERP session.

Preserve independent requester/approver/target checks and live actor/grant checks.
Cloud provisioning/link/bootstrap needs a reviewed one-time protected procedure
for two distinct administrators; an IdP dashboard role never grants ERP capability.
Existing admins cannot be cloned/rebootstrapped by switching AUTH_PROVIDER.
Recommended initial recovery retains independently approved, hash-only single-use
ERP recovery tokens and private verified delivery. Cloud redemption binds the
approved mapping and applies password change through a protected backend provider
operation; no public email discovery or implicit signup. Provider-specific reset/
MFA/deactivation semantics and privileged-key isolation require review and live tests.
Local recovery stays unchanged. Email/PKCE/social expansion is a separate decision.
Supabase documents a privileged server-side user update API; selecting its secret
custody and proving reset/revocation outcomes remain acceptance work, not authority
to use it now. [Admin update API](https://supabase.com/docs/reference/python/auth-admin-updateuserbyid).

External effects cannot share an atomic transaction with the ERP DB. Add only
necessary durable auth-operation intent/outcome state for approved provider work.
ERP deactivation/session denial commits first; activation/linking stays inactive
until approval and verified provider outcome. Consume reset tokens and reserve
intent before remote mutation; ambiguity requires new proof/reconciliation, never
token replay. Do not mark an account request applied just because it was approved.
Retries recheck authority and match idempotent target/operation, retaining audit
history. No untracked daemon job or blanket success on provider timeout.

## Hosting, configuration and future self-hosting

Recommended first topology: React on Vercel, same-origin /api routed to FastAPI
with durable PostgreSQL. Same-origin cookie/CSRF behavior must be proven for exact
approved hostnames, forwarding, cache headers and Set-Cookie; no wildcard preview
origins or trusting forwarded/client host headers as issuer/authority. Isolate
preview test-project secrets from production. Future Vercel Python ASGI Functions
are possible, but lifecycle/connection/timeout packaging is a D verification item.
[Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python),
[environment separation](https://vercel.com/docs/environment-variables).

Proposed server config contract: explicit AUTH_PROVIDER, fixed Supabase URL/issuer,
audience/algorithm, JWKS policy, Origin/cookie settings, encryption key identifier
and private credentials by reference. Public UI receives only safe provider label/
capability metadata. Do not commit live project URLs/keys or introduce required
cloud variables into SQLite setup. Runtime migrations never run per request/start.

No provider token state, session locks or rate limits in temporary filesystem or
process memory. Use PostgreSQL transactions for authoritative multiworker state;
bound all network calls and close clients/pools with the actual runtime lifecycle.
Do not depend on a background loop surviving a serverless request. D tests runtime
roles without ownership/BYPASSRLS, TLS verify-full, pooler modes/prepared statements
and concurrency budgets before deploying; C claims no live Vercel compatibility.

ERP PostgreSQL may be self-hosted while identity remains Supabase. A future local
or self-hosted IdP adapter keeps internal UUID/grants/audit; do not transfer Supabase
password hashes or auto-link by email. Preserve provider history, revoke old sessions,
review new issuer/proof, and use an explicit transfer/credential-enrollment plan in E.
Migration of database location must not implicitly change identity provider.

## Diagnostics and acceptance

ADR-010 structured logs remain whitelisted: event kind, internal IDs/correlation,
bounded provider/error category and latency; no raw JWT/refresh/password/email,
headers, query codes, provider error body, key, SQL params or unverified claims.
Audit link/approval/revoke/refresh failure/operator effects without secrets. Enforce
durable limits on login/refresh/recovery/JWKS misses with generic client failures.
Do not hold the global admin lock for provider network calls. Retention and incident
ownership remain security/DPO decisions. Required tests/gates are CR-002C C-A1–12.
Live provider integration and human acceptance cannot be replaced by fixtures.
Library evaluation reference: [PyJWT verification usage](https://pyjwt.readthedocs.io/en/stable/usage.html).
Library examples/defaults do not replace the explicit ERP claim/key policy above.
