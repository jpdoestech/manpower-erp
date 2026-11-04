# P1-01 follow-up — administrator account controls

2026-11-04. REVIEW; local checks pass, hosted CI and security acceptance pending. Branch
`feature/p1-01-account-controls` starts at `dc7fca3`, stacked on open PR #2.

## Audit and requirement change CR-001 (before code)

Fetched all branches. Clean tree: main b3517d3, P0-02 4fd3914, P1-01 dc7fca3.
Actual P0-01/P0-02 source, migration baseline, health/diagnostic tests and CI match
their acceptance criteria. PR #2 at dc7fca3 currently shows 6/6 successful checks.
Existing P1-01 implements password/session/CLI/UI foundations, not the expanded
administrator/bootstrap/recovery requirements in the latest user request.

CR-001 changes the earlier CLI-only account-management boundary. Classification:
permission and additive schema/API change, development-only, effective this slice;
no company, billing, GL/AR, imports or historical financial documents affected.
ADR-012 supersedes only those exclusions in ADR-011. Full organization/RBAC stays
P1-02/P1-03. No production rollout or inferred human security approval.

## Implementation plan / affected files

1. ADR-012, SECURITY_RBAC, OPERATIONS, PRODUCT_BLUEPRINT, DECISIONS and this report:
   document a narrow global technical Super Admin capability, separate from future
   organizational grants, plus two-person account approval and recovery delivery.
2. Identity models + additive migration 0003: false-by-default capability, account
   requests and hashed, expiring, single-use reset tokens. Preserve all users/audit;
   refuse downgrade with new history/admin grants. No business schema or dependency.
3. Identity administration service/routes: active Super Admin only, CSRF/Origin,
   bounded requests and current-password reauthentication. Register inactive users;
   a distinct current admin approves activation/deactivation/reset/unlock. Reject
   requester/target self-approval, replay and approvals by revoked actors; recheck
   both actors in the transaction. Audit actor/subject/request/approval linkage.
4. Protected operator CLI bootstrap: hidden confirmed passwords for two distinct
   new technical admins, one transaction, no defaults/flags/public endpoint;
   serialize bootstrap and refuse when any Super Admin already exists. Existing
   operator commands remain a documented privileged database trust boundary.
5. Recovery: approval returns a 256-bit token once for verified out-of-band handoff;
   store its hash only, 15-minute expiry, invalidate older tokens, serialize redemption,
   revoke sessions on issuance/redemption/password changes/deactivation. Generic
   invalid/used/expired errors and durable attempt limits. No email integration or
   token URL/query/localStorage. Add a labelled recovery form to existing account UI.
6. Tests, OpenAPI contracts, migration fixtures, existing CI gates and contributor docs:
   preserve existing behavior; run all gates and push a separate stacked PR.

## Acceptance / testing strategy

- Re-run all existing backend/frontend tests and migration/diagnostic gates.
- Real disposable PostgreSQL: clean/repeat/drift/empty downgrade/re-upgrade; migrate
  an existing 0002 user/session/audit intact, capability defaults false; populated
  0003 downgrade refuses without data loss.
- Bootstrap atomicity, hidden prompts, duplicate/concurrent/repeated denial; only
  intended admins gain technical capability, no company authority.
- Anonymous/ordinary/forged-role admin access denied; CSRF/Origin/current-password
  checks and throttling; inactive/revoked actors fail at approval time; self/target
  approval and duplicate approvals denied, including concurrent redemption.
- Registration remains inactive until independent approval; deactivate revokes
  sessions, unlock clears only that name's timed lockout (never global throttle).
- Recovery hash/expiry/single use/replacement/inactive account denial; no plaintext
  token/password in database, audit or logs; immutable audit linkage retained.
- UI recovery success/failure and clearing secrets; original login/logout/password
  tests preserved. No administrative UI needed: authenticated documented API is
  the initial operator surface; no full RBAC/company UI.
- Ruff format/lint, strict mypy, pytest unit/integration/migrations, Biome/tsc,
  frontend tests/build, dependency audits, Compose config, actionlint, diff check.
- Hosted backend/frontend/Compose must pass for pushed source before any success
  claim. Keep REVIEW for human security acceptance. No merge/deploy/P1-02.

## Local results before push

Host/runtime versions and disposable loopback PostgreSQL cluster are the same as
the baseline in STATUS. No dependency or lockfile versions changed. Commands from
backend use `..\.tools\Scripts\uv` 0.13.7 with explicit test-only DATABASE_URL.

| Executed command | Result |
|---|---|
| `git fetch --all --prune`, branch/history/status inspection | PASS; three original local/remote branches, seven commits; clean tree; dc7fca3 baseline |
| GitHub PR #1/#2 current-head UI | PASS; 4fd3914/dc7fca3 each 6/6 checks, both open/unmerged |
| `uv run --locked ruff format --check .`, `ruff check .` | PASS; 26 files |
| `uv run --locked mypy app tests alembic` | PASS; 26 source files |
| `uv run --locked pytest -q --tb=short` | PASS; 92 tests in 55.76s, no warnings |
| `uv run --locked pytest -q tests/test_account_controls.py --tb=short` after activation hardening | PASS; 19 tests in 30.63s; deactivated credentials no longer work upon reactivation |
| `uv lock --check`, `uv run --locked pip-audit` | PASS; lock unchanged, no known vulnerabilities |
| `npm run format:check`, `npm run lint`, `npm run typecheck` | PASS; 13 files, tsc exits 0 |
| `npm test` | PASS; 13 tests (9 preserved + 4 recovery cases) |
| `npm run build` | PASS; 18 modules, Vite 8.3.5 |
| `npm audit --audit-level=low` | PASS; zero vulnerabilities |
| `.tools/docker-compose.exe config --quiet` with process-local synthetic password | PASS |
| `.tools/actionlint/actionlint.exe .github/workflows/ci.yml`, `git diff --check` | PASS |

Migration tests exercise clean/repeated head install, drift, empty rollback/re-upgrade,
populated rollback refusal and 0002 user/session/audit preservation. Existing P0
health/logging/connection/validation regressions remain passing. Concurrent bootstrap,
approval and token redemption are tested on real PostgreSQL, not mocks. Existing CI
already runs all new tests/current-head migrations plus Docker health/auth/persistence;
no additional workflow/dependency is needed. Local Docker engine remains unavailable;
hosted execution is pending, not counted as passed.

Initial run: 14 failed/75 passed. The new fixture reused a cookie when logging in a
second admin (correctly revoking the first), and one baseline expected the old head.
Fixed the fixture to model separate browsers and updated the head assertion without
weakening old tests. Formatting/type failures were corrected. Final results above
supersede those failures. Review also added password invalidation on reactivation.

## Changed files / limitations

- backend/app/identity/{administration,models,service,routes,cli}.py;
  backend/alembic/versions/0003_account_controls.py.
- backend/tests/{test_account_controls,test_api,test_identity,test_migrations}.py.
- frontend/src/{AuthPanel.tsx,RecoveryForm.tsx,RecoveryForm.test.tsx}.
- README.md, docs/{OPERATIONS,PRODUCT_BLUEPRINT,SECURITY_RBAC}.md,
  docs/adr/{ADR-011-authentication,ADR-012-account-controls}.md.
- tasks/{P1-01,P1-01-account-controls,ROADMAP,STATUS,DECISIONS}.md.

Administration uses authenticated API initially; recovery has a small labelled UI.
No email delivery, MFA verification, company scopes, general RBAC, financial approval,
or production deployment. Technical admin pair is fixed: no role-promotion API.
Production total-admin-loss recovery and DB-operator dual custody need review.
Manual identity verification/token handoff, fixed limits, runtime DB permissions and
MFA enforcement remain human security gates. Original CLI is privileged operator
access; it is not claimed to enforce application approval against a DB owner.
No refresh tokens exist; opaque sessions rotate on login and expire absolutely.

Next: commit/push, stacked PR into feature/p1-01-authentication, verify hosted gates;
retain REVIEW until human security acceptance. P1-02 only after that gate and a
separate authorization. No merge or production data changes.
