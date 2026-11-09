# Project Status — Codex Must Maintain

Last updated: 2026-11-05
Current requested milestone: controlled integration readiness and local foundation RC
Current task status: REVIEW; local regression gates pass, fresh RC CI required, human acceptance pending, CR-002C NOT STARTED
Repository inspected: YES; connector verifies all original remote heads including main b3517d3; CLI fetch fails; RC starts at 2232702
Implemented code: existing P0/P1 foundations plus technical account administration/recovery follow-up; no company/finance modules
Validated requirements: UI-001 8c0f50c has 10/10 hosted checks; 110 unit/SQLite, 42 PG, 27 frontend, 27 browser and 30 Windows safety tests pass

## Integration readiness — release/rc-2026-11-05

Staging preparation (2026-11-05): user explicitly authorized development/staging
database/Auth-first work and reports a Supabase GitHub connection. Separate branch
chore/supabase-staging-preflight adds the plan and staging guide; local ignored
configuration leaves Windows SQLite/local auth untouched. Read-only JWKS, Auth
health and settings GETs return HTTP 200; one ES256 key; public signup enabled.
DATABASE_URL remains empty, so PostgreSQL/TLS/grants/migrations are NOT TESTED.
No schema, account, provider setting, dependency or production resource changed.
The dashboard automation configuration is unverified. Alembic stays the sole ERP
migration authority; private schema/Data API exposure and runtime/migrator roles
must be proven before hosted ERP migration. Details and exact command/exit status:
SUPABASE_STAGING_PREFLIGHT.md and docs/SUPABASE_STAGING_SETUP.md. No human approval
or completed CR-002C implementation is inferred. Next: privately save the staging
connection, verify read-only access, then test the protected migration configuration.

Staging follow-up: connection URL is now populated and project-matching; missing
verify-full was added only to ignored configuration. Both default and system CA
probes exit 1; the system CA store does not trust the database certificate. Awaiting
the provider database CA in .local/supabase-ca.crt. No authenticated DB queries,
migrations or cloud mutations succeeded; prior empty-URL evidence above is history.

Latest staging result (supersedes connection blockers above): supplied CA parses;
explicit sslrootcert plus verify-full yields successful read-only TLS connection,
probe exit 0. No six ERP identity tables, Alembic version table or erp_private
schema found. Connected role has BYPASSRLS and must not be used by API runtime.
anon/authenticated have public USAGE and 32 public default table privilege entries
in total; exact creating-role/effective exposure requires tests before migration.
No cloud writes or user-data reads. Next: implement/test protected schema and
separate roles on disposable PG before staging DDL. Auth integration/security
acceptance still pending. Changed evidence: SUPABASE_STAGING_PREFLIGHT.md,
docs/SUPABASE_STAGING_SETUP.md and STATUS; private CA/config remain ignored.

2026-11-09 private schema rehearsal in PR #13: added prepare, grant and verification
SQL under `scripts/postgres/` and the staging runbook. On disposable PostgreSQL
18.3, migration/retry/drift checks, empty reinstall, populated downgrade denial,
restricted-role API login/logout and API-role denial passed. SQLite/backend
110 passed, PostgreSQL 42 passed, Ruff and mypy passed. Exact commands and
expected denials are in `SUPABASE_STAGING_PREFLIGHT.md`. Main remains `b3517d3`
and #2/#3/#9/#12 have no submitted reviews. Hosted schema/roles are unchanged.
Next step is acceptance of the inherited identity foundation and review of the
staging runbook before applying it. CR-002C provider implementation remains gated.

Latest CR-002C start-request recheck (2026-11-05): git fetch --all --prune now
succeeds, but remote main is still b3517d3 and PRs #1–#12 remain open/unmerged;
#12 is draft at 9efaa48. Fresh reviews AND issue-comment reads for #2/#3/#9/#12
are empty. Both P1-01 records retain PENDING HUMAN REVIEW and all eighteen items
unchecked; CR-002B acceptance is not recorded. main protected=false and ruleset
list empty persist; detailed protection read is still 403. ADR-017 remains
PROPOSED ONLY, with no supplied security decision/approver/reference. The new
conditional execution request is not evidence that those decisions were made.

At 9efaa48 the RC retains 10/10 passing CI checks. Runtime, dependencies, database
and human acceptance records are unchanged; no new SQLite/PG execution is claimed
for this gate-only recheck. CR-002C remains NOT STARTED, including dependency
installation/contract adoption. Owner/security actions in the integration
checklist must be completed and verified before the first approved slice starts.

RC branch starts at 2232702 and includes the complete implemented stack without
merging or rewriting any original PR. Main remains b3517d3. All PRs #1–#11 are
open/unmerged (#4/#11 draft), zero submitted reviews/threads, current-base
mergeability true. All head-matching checks pass (6/6 for #1–#4, 8/8 for #5,
10/10 for #6–#11). Proved exact base/head ancestry, 25 disjoint incremental commits
and no duplicate stable patch IDs. Recommended history-preserving order: #1 ->
#2 -> #3 -> #4 -> #5 -> #6 -> #7 -> #8 -> #9 -> #10 -> #11, retarget/recheck after
each accepted predecessor. RC is validation, not a security-review bypass.

CLI fetch repeatedly failed on GitHub port 443. The connector independently lists
all 12 original remote branches and confirms every PR/main head against local
refs; failed fetches are not represented as success. RC branch was published via
the authorized GitHub connector; no other branch was changed.

Local fresh evidence: test-local.bat exits 0 (110 backend/SQLite/auth tests,
launcher/database safety with opt-in smoke skipped, 27 frontend); 42 actual PG
tests and migration CLI up/repeat/check/down/up/check pass on a new loopback test
cluster, now stopped; 27 responsive browser checks pass across nine profiles;
format/lint/types/build/lock checks/audits/Compose config/actionlint pass.
Real fresh Windows nine-tool workflow also passes separately (one test, 447.604s,
no skip): setup twice, HTTP login/me/CSRF logout, readiness, check, live backup,
repeated stop, restore/reset/restore, repeated migrations and test-local. Ports
were free before/after this fixture; original workspace DB untouched. New RC
hosted PostgreSQL/Compose/Windows/frontend CI must pass at the candidate head;
current evidence is recorded with the candidate PR. No runtime or schema change.

Candidate is draft [PR #12](https://github.com/jpdoestech/manpower-erp/pull/12).
Additional integration hold: remote main metadata reports protected=false, no
rulesets are returned, and detailed protection read is 403 for the connector.
Owner must verify/enforce required reviews/checks and bypass policy before landing;
no protection configuration was changed. Exact current-head CI evidence stays
attached to the candidate PR; no earlier PR's checks substitute for it.

Evidence/conditions: INTEGRATION_READINESS.md. Human actions:
docs/INTEGRATION_REVIEW_CHECKLIST.md. Source security record unchanged: all eighteen
A/B items and both #2/#3 decisions remain PENDING HUMAN REVIEW. A/B/UI acceptance,
MFA/recovery/operator/production decisions remain pending; no milestones DONE.
CR-002C still needs B/inherited acceptance, both P1-01 decisions/conditions,
accepted ancestry and ADR-017 provider custody/revocation/linking/admin decisions,
authorized disposable project/test configuration and actual start authorization.
No main merge, production data change/deployment or Supabase code. Changed files:
INTEGRATION_READINESS.md, INTEGRATION_REVIEW_CHECKLIST.md, STATUS and ROADMAP.

## CR-002C — Technical plan only; prerequisites not accepted

Planning branch docs/cr-002c-provider-plan starts at PR #10 e4608e1. Fresh fetch
finds main b3517d3 and PRs #1–#10 still open/unmerged (#4 draft). #9 fbaa78c and
#10 e4608e1 each have 10/10 passing checks, re-fetched at exact heads. Submitted
reviews for #2/#3/#9/#10 are empty; P1-01 decisions stay PENDING HUMAN REVIEW,
CR-002A/B and UI-001 remain REVIEW. No integration or human approval invented.

Acceptance/source review: CR-002C-READINESS.md. Local fresh verification:
110 backend unit/SQLite tests pass (33.91s), 27 frontend tests pass (16.50s),
27 Chromium browser checks across nine 320–2560px profiles pass (1.3m). Reused
exact-head CI confirms PG 42/migration CLI, Windows 30/all nine native commands,
Compose recovery/persistence and audits/linters/types/build. No developer data or
running local listeners changed. Physical-device/TTY/production limits remain.

Expanded CR-002C.md with G1–7 prerequisites, C-D1–7 proposed decisions, eight
implementation slices and C-A1–12 acceptance requirements. Added proposed
ADR-017 and AUTH_PROVIDER_STRATEGY.md: preserve offline local cookie auth,
server-owned Supabase bridge/JWT verification, approved identity mappings,
encrypted refresh custody/live revocation, independent account operations,
deny-all company foundation and Vercel/self-host compatibility boundaries.
No runtime code, SDK/dependency, mapping migration, keys/project or provider tests.

Blocking requirements: actual B/inherited acceptance and both P1-01 security
reviews with conditions; approve custody/key/revocation/linking/admin MFA/recovery
decisions; identify valid integration ancestry and a disposable authorized provider
test project. UI review stays pending without inventing a new security gate.
Next action is human technical/acceptance review of this plan, not automatic C
implementation, PR merge, deployment or P1-02 work. Changed files: CR-002C.md,
CR-002C-READINESS.md, AUTH_PROVIDER_STRATEGY.md, proposed ADR-017, ROADMAP,
DECISIONS, STATUS, CR-002 phase index and architecture/security plan pointers.

## UI-001 — Independent responsive frontend foundation

Explicitly authorized separate branch feature/ui-001-design-system from verified
fbaa78c (#9). Fresh fetch finds main b3517d3 and PRs #1–#9 open/unmerged (#4 draft).
Connector reviews for #2/#3/#9 are empty; no human acceptance is manufactured.

Implemented native reusable controls, keyboard tabs/modal dialogs, table/states,
toast/skeleton patterns; validated-session shell with collapsible sidebar,
breadcrumbs, account controls, theme, static module search and notification
placeholder. Phones use bottom navigation/modal drawer and module lists; tablets,
laptops and desktop use responsive rails/sidebar, cards and compact tables.
Unavailable scope selector and administration never grant access. No backend,
schema, credentials, production setting, business logic or auth provider change.

Local frontend: 27 unit/component/auth tests, 27 browser checks across nine
320–2560px profiles, formatting/lint/types/build/audit pass. Browser axe scans
and focus/keyboard checks pass; phone/light and desktop/dark screenshots inspected.
Backend 110 unit/SQLite tests pass (21.00s); Ruff/mypy pass (37 files). Exact
commands, changed files and initial corrected failures: UI-001.md. Actual
test-local.bat exits 0: 110 backend, launcher safety/migrations (one opt-in startup
skip), 27 frontend. Local pip-audit hit PyPI DNS/timeout twice; hosted audit passes.
Original local API/web listeners remain 8000:23068 and 5173:27032; no reset/stop.

Design/architecture docs and ADR-016 are added; CR-002B/P1-01 acceptance is still
pending. No merges or deployment. Physical devices, Safari/Firefox and human
screen-reader/usability review remain unverified. UI-001 not marked DONE.

Verified implementation 8c0f50c in [PR #10](https://github.com/jpdoestech/manpower-erp/pull/10)
passes all 10 push/PR checks: [push 41853148408](https://github.com/jpdoestech/manpower-erp/actions/runs/41853148408),
[PR 41853350250](https://github.com/jpdoestech/manpower-erp/actions/runs/41853350250).
Real PG: 42 integration tests (12.28s), migration CLI, pip audit pass. Fresh
Windows: all nine BAT commands, HTTP authentication and 30 safety tests pass
(200.394s, no skips). Frontend 27 unit/auth and 27 browser checks, build/audit,
existing Compose health/auth/dependency-recovery/persistence all pass. Evidence-only
docs follow this source. Next: UI review; CR-002C implementation remains gated by
B acceptance and required authentication review. No automatic next task.

## CR-002B — Completed tools, acceptance pending

Completion follow-up: feature/cr-002b-completion starts at verified 9e44c96 (#8).
Fresh fetch/connector audit: #6/#7/#8 open/unmerged, no reviews, each 10/10 checks.
Pre-code plan and evidence: CR-002B-completion.md; ADR-015 local recovery design.
Added seven missing BATs, Windows lock/cooperative stop and SQLite snapshot/
confirmed replacement helpers. Preserved latest CLI diagnostics and all app/PG
behavior. Existing user API/web remain running and untouched; fixed-port real
local smoke is skipped, actual nine-tool smoke is required on Windows CI.
CR-002C.md is a technical plan only. P1-01 human acceptance remains pending.

Verified source 22b437b in [PR #9](https://github.com/jpdoestech/manpower-erp/pull/9)
passes all 10 branch/PR checks:
[push 41840454394](https://github.com/jpdoestech/manpower-erp/actions/runs/41840454394),
[PR 41840462879](https://github.com/jpdoestech/manpower-erp/actions/runs/41840462879).
Hosted Windows: 110 unit/SQLite tests (14.39s), 30 launcher/database safety tests
including real nine-tool fresh flow (198.484s, no skips). Hosted PostgreSQL:
42 integration tests (12.54s), migration CLI and Docker regressions pass. Frontend
13 tests/build, Ruff/Biome/TypeScript, mypy both platforms, audits and static checks
pass. Exact commands, initial failures/fixes, 27 changed files and backup/restore
proof: CR-002B-completion.md. Local test-local.bat exits 0 (110 backend, 29 safety
passes/one opt-in smoke skipped, 13 frontend); user's live app/DB untouched.

All nine native commands are documented in LOCAL_WINDOWS_SETUP.md. Restore/reset
are confirmed/offline/recoverable; restored authentication capabilities are revoked.
Existing listeners keep their original PIDs. Unencrypted current-revision snapshots,
unmanaged/crashed owners, manual corrupt-DB salvage and interactive TTY/browser
limits are documented. B is REVIEW, not accepted; C remains plan-only until
acceptance. No production changes, merges or manufactured security decisions.

Local provisioning follow-up: user reported a generic failure after password
confirmation. Supplied password satisfies length policy; read-only local check
shows revision 0004, no admin-name account and no FK violations. Original cause
is unconfirmed because CLI suppressed the category. Add sanitized actionable
operator errors and a synthetic exact-15-character SQLite CLI regression;
plan/evidence: LOCAL_ACCOUNT_DIAGNOSTICS.md. No user account/password modified,
no password policy or API/security change. Local 110 non-integration tests pass
(24.55s); Ruff format/lint and strict mypy pass (34 files). Source `91cc2d4`
passes all 10 branch/PR checks in [PR #8](https://github.com/jpdoestech/manpower-erp/pull/8),
including PostgreSQL/migration, real Windows native smoke, frontend and Docker.
[Push run 41824392925](https://github.com/jpdoestech/manpower-erp/actions/runs/41824392925),
[PR run 41824514925](https://github.com/jpdoestech/manpower-erp/actions/runs/41824514925).
Original interactive cause remains unconfirmed; no user credentials/account were
used or changed. Rerun setup in an interactive terminal for the precise category.

Added setup-local.bat/start-local.bat and scripts/windows/local.py. Setup uses
existing uv 0.13.7, repository-managed Python 3.13.18, locked dependencies/npm ci,
SQLite migrations/check and optional hidden-password ordinary-account CLI. Start
uses fixed local child settings, loopback servers, refuses port collisions, waits
for readiness before browser opening and stops only owned processes on Enter/
Ctrl+C/failure. Existing .env, accounts/data and Docker BATs remain unchanged.
Plan/tests/evidence: CR-002B-local-launchers.md. Docs: LOCAL_WINDOWS_SETUP.md.

Local: all 17 Windows launcher tests pass (84.196s), including 9 native tests with
actual double setup, populated-account preservation, real HTTP login/me/logout,
second-launch refusal and owned shutdown/port release; existing 8 Docker-stub
tests pass. Ruff format/lint and strict mypy pass (33 files); 101 backend unit/
SQLite tests and 13 frontend tests pass, frontend format/lint/types/build pass,
actionlint and whitespace checks pass. CI now includes real native Windows smoke
and lint/type coverage for the helper. Source `d38a034` passes 10/10 matching-head
branch/PR checks in [PR #7](https://github.com/jpdoestech/manpower-erp/pull/7),
stacked on #6. [Push 41797323446](https://github.com/jpdoestech/manpower-erp/actions/runs/41797323446),
[PR 41797507702](https://github.com/jpdoestech/manpower-erp/actions/runs/41797507702).
Hosted Windows: 101 SQLite/unit tests (14.18s), 9 native launcher tests (42.257s,
no skips); separate job verifies 8 existing BAT tests. Linux: 101 unit/SQLite
tests (9.43s), 42 PostgreSQL integration tests (12.44s), migration CLI, audits and
Docker auth/health/persistence gates pass. Evidence-only docs follow this source.

No backend/frontend application or migration change. Local PG/Docker execution,
interactive hidden-password prompts, default browser opening and closing the
window with X remain unrun in this slice; hosted PG/Docker regression is required.
Use Enter/Ctrl+C for supported shutdown. No reset/backup/restore or full B claim.
Formal A/P1-01 security acceptance remains pending; no automatic merge/deployment.

## CR-002A — SQLite / PostgreSQL compatibility (prior phase evidence)

Subsequent request authorizes setup-local.bat/start-local.bat now; narrow B plan:
CR-002B-local-launchers.md. Existing formal A and P1-01 review decisions remain
pending. Full B's additional tools are not included in this setup/start request.

Explicit user-requested architectural prerequisite; starts from verified PR #5
head 19a0ba7, preserving all feature ancestry. Pre-code plan: CR-002.md, ADR-014.
Fresh fetch and matching-head diagnostics: PRs #1–#4 6/6; #5 8/8 successful checks.
Browser confirms #1–#3 open, #4 draft, #5 open; stacked bases unchanged, no merges.
P1-01 #2/#3 remain PENDING HUMAN REVIEW; P1-02 remains blocked.

Implemented opt-in local/test SQLite, explicit database/provider validation,
safe .local path/WAL/FK/busy settings, UTC mapping and serialized transactions.
Shared identity migrations retain PostgreSQL paths; 0004 adds SQLite-only strict
length/Boolean/UUID guards, PostgreSQL no-op. Preserve immutable audit including
REPLACE, existing independent account approval, recovery, sessions/CSRF and limits.
Python 3.13.18 pin replaces old minor-only preference because local 3.13.12 bundled
SQLite 3.50.4 with upstream WAL-reset risk; patched managed SQLite 3.53.1 verified.
Application dependency locks unchanged. Native commands in DATABASE_MODES.md.

Local final evidence: 101 non-integration tests, 42 actual PostgreSQL integration
tests on disposable databases, 13 frontend tests, 8 existing BAT stub tests pass.
Ruff format/lint, strict mypy (31 files), frontend format/lint/typecheck/build,
pip-audit/npm audit (no known vulnerabilities), actionlint, Compose config and
whitespace checks pass. Native Uvicorn/Vite HTTP smoke with SQLite passes health,
readiness/bootstrap/page/login/me/CSRF logout. Detailed commands/limits: CR-002.md.
Source `1ff2629` in [PR #6](https://github.com/jpdoestech/manpower-erp/pull/6)
passes all 10 branch/PR checks: Windows launchers/SQLite, backend, frontend,
Compose. [Push run 41790302931](https://github.com/jpdoestech/manpower-erp/actions/runs/41790302931)
and [PR run 41790357270](https://github.com/jpdoestech/manpower-erp/actions/runs/41790357270).
Hosted Linux: 101 Docker-free tests (9.61s), 42 PostgreSQL tests (12.48s), clean
migration CLI upgrade/repeat/check/downgrade/reinstall/check and audits pass.
Hosted Windows SQLite: 101 tests, 14.73s. Docker passes auth/health/dependency-down/
recovery/persistence gates. Local PostgreSQL source public tables and remaining
generated test DB counts are both zero; test cluster stopped. Repeat native
SQLite HTTP smoke after final guards exits 0.

Changed files: database/UTC type/identity models/service/security, Alembic env and
0002/0003/0004, configuration/PG fixture/head tests plus SQLite acceptance tests,
Python preference, CI, .gitignore/.env.sqlite.example, AGENTS/README,
ARCHITECTURE/OPERATIONS/SECURITY_RBAC, DATABASE_MODES,
SQLITE_POSTGRES_COMPATIBILITY, ADR-014 and task plan/roadmap/status/decisions.
No business/UI module change. CR-002B/C/D/E NOT STARTED; root BATs still require
Docker. Supabase TLS configuration is transport-only; live DB roles/poolers and
Auth/Vercel/transfer are unverified/unimplemented phase gates. No production data
or deployment. SQLite files are unencrypted; file owners can bypass DDL guards.
Phase A is REVIEW; human acceptance is required before B, not inferred from CI.
Overall CR-002 is not DONE. Evidence-only documentation follows verified source.

## Windows local launchers — separate authorized contributor task

User requested setup/run BAT files. Created feature/windows-local-launchers from
d8d1cd6, with a separate PR planned; P1-02 remains blocked and no dependent feature
implementation is authorized. Pre-code plan/tests: tasks/WINDOWS_LOCAL_DEV.md.
Added setup.bat/run.bat around existing local Compose startup, safe one-time .env
generation, optional existing ordinary-user CLI, visible errors and readiness.
No application/migration/authorization logic changed. Windows shell regression
tests and CI job added. Local 8 tests pass using real cmd/PowerShell with a Docker
stub; Ruff format/lint and strict mypy pass (27 files), Compose config, actionlint
and whitespace checks pass. Exact commands, corrected initial failures and limits
are in tasks/WINDOWS_LOCAL_DEV.md. Local Docker Desktop
boot/interactive Docker password TTY/browser opening remain unrun; no live startup
claim. Existing human-review and P1-02 prerequisite states are unchanged.
Initial hosted Linux gates passed; Windows failed because the missing-Docker test
still discovered the runner's System32 Docker CLI. Fixture tool discovery isolated;
launchers unchanged. Corrected source ec348a7 passes 8/8 branch/PR checks in
[push run 41782345240](https://github.com/jpdoestech/manpower-erp/actions/runs/41782345240)
and [PR run 41782348413](https://github.com/jpdoestech/manpower-erp/actions/runs/41782348413).
Windows reports 8 tests in 4.563s; local final suite 8 tests in 3.613s. Existing
Linux backend/frontend/migrations/Compose and audits pass. [PR #5](https://github.com/jpdoestech/manpower-erp/pull/5)
is stacked on #4; no merge. Evidence docs only follow verified source. Local real
Docker/TTY/browser paths remain unrun; human acceptance records stay pending.

## P1-02 prerequisite audit and plan

The user explicitly confirmed P1-01 security acceptance has not been granted or
recorded. Added `tasks/SECURITY_ACCEPTANCE_P1-01.md`: separate pinned PR #2/#3
review records are PENDING HUMAN REVIEW, all checklist items unchecked, identities/
dates/decisions/conditions/GitHub references unfilled. It covers authentication,
sessions, CSRF, provisioning/recovery, technical admins, audit, company-access
boundaries and outstanding MFA/recovery/operator/production risks. Human evidence
is required before changing either decision; automated checks do not open the gate.
P1-02 plan remains in draft PR #4, with no schema/API/UI/grants implemented.
This update is documentation only; no new local application/security tests claimed.
Local document validation passes: two pending decision records, 18 unchecked items,
no checked items, referenced local evidence files exist; `git diff --check` passes.

Latest request authorizes P1-02 subject to verified prerequisites; explicitly says
not to bypass security acceptance or merge automatically. Fetch confirms unchanged
main b3517d3 and feature heads 4fd3914/dc7fca3/37dbd7f. Working tree was clean.
Inspected all three PRs and mandatory docs, actual API/security/migration/test/CI
surfaces. Fresh connected-account diagnostics report 6/6 successful checks at each
exact head. PR #1 targets main; #2 targets P0-02; #3 targets P1-01 foundation. All
remain open/unmerged. P1-01 #2/#3 show No reviews; STATUS/ADRs still require human
security acceptance. Task authorization is separate from prerequisite acceptance.

Ancestry verifies the complete P0/P1 stack in 37dbd7f but not in origin/main. No
integration or merge performed. Created feature/p1-02-organizations from 37dbd7f
for audit/plan documents only. `tasks/P1-02.md` contains the pre-code plan, acceptance
cases, intended files, exact prerequisite CI links and missing approval evidence.
ADR-013 is PROPOSED ONLY; architecture/index updated without changing adopted
company/security/tax policy. Asked for the recorded P1-01 reviewer/decision.

No organization schema/migration/API/UI, grant or P1-02 automated test exists yet.
No production work or P1-03. Matching-head hosted prerequisite results reused;
no fresh local application-test run is claimed for these documentation edits.
Next safe action: record actual P1-01 security acceptance, verify chosen base after
fresh fetch, then implement P1-02 and its full automated gates. P1-03 follows only
after completed/accepted P1-02 and separate authorization.

## Current P1-01 CR-001 follow-up

Latest user request expands account controls. Actual source inspection confirms
P0-01/P0-02 acceptance implementations and original P1-01 foundation; main still
contains only P0-01. PRs #1/#2 remain open/unmerged. No duplicate bootstrap/infra.
New branch feature/p1-01-account-controls from dc7fca3, stacked on #2. Pre-code
plan/acceptance: tasks/P1-01-account-controls.md; CR-001/ADR-012 recorded before code.

Additive migration 0003, technical admin bootstrap, independent account requests,
single-use recovery and UI implemented. Final local gates: 92 tests in 55.76s;
after reactivation-password hardening, 19 account-control cases pass in 30.63s.
Frontend 13 tests, Ruff format/lint, strict mypy (26 files), Biome/tsc, build,
lock check, pip/npm audits, Compose configuration, actionlint and diff check pass.
Migration tests preserve 0002 user/session/audit rows and verify clean/repeat/drift/
safe downgrade/re-upgrade plus history/grant refusal. Concurrent approval/recovery/
bootstrap and server authorization tests pass. No dependency versions changed.

Exact commands, initial failures/corrections, changed-file ledger and limitations:
[P1-01-account-controls.md](P1-01-account-controls.md). Implementation commit
`5ca0ad3ab96e1e0fb3ea68f83ddc6302d5c061c3` in [PR #3](https://github.com/jpdoestech/manpower-erp/pull/3)
passes all six exact-head GitHub checks: [push CI 41765130592](https://github.com/jpdoestech/manpower-erp/actions/runs/41765130592)
and [PR CI 41765194928](https://github.com/jpdoestech/manpower-erp/actions/runs/41765194928).
PR backend logs: 50 unit/API passed (1.66s), 42 PostgreSQL integration passed
(13.79s). All source tests pass after final hardening. Migration CLI and Linux
Docker boot/authentication/outage/recovery/persistence pass. Existing Node/runner
annotations are non-failing maintenance notices. No lock/dependency changes.
Local probe via psycopg verifies 0 input public tables and 0 generated DBs remaining;
PostgreSQL stopped. Native psql unavailable; equivalent probe succeeded. Local
Windows Docker execution unavailable. Human security acceptance remains required. Initial
admin operator pair/manual private token delivery/MFA/production recovery and
permissions require review. No company grants, P1-02, merge or production deployment.
PR #3 stacks on #2; #1/#2 remain open. Next: review P1-01, then separately authorize
P1-02 after acceptance. Documentation-only evidence follows the verified source.

## Historical P1-01 foundation outcome (before CR-001)

- User explicitly authorized verify-and-continue. Fetch confirmed two existing local/
  remote branches, five commits, clean worktree, open PR #1 and no open issues.
  P0-02 existed in full on 4fd3914; main still ends at P0-01. GitHub UI confirms
  exact-head 6/6 checks; fresh local prerequisite run passed 36 tests, Ruff/mypy,
  pip-audit. Reviewed migrations, health/live-ready, logs/correlation/redaction,
  sessions, docs and CI against acceptance; no missing P0-02 code found.
- Created feature/p1-01-authentication from verified P0-02. No merge or duplication
  of P0-02. Planned/auth decisions before coding: tasks/P1-01.md and ADR-011.
- Added operator-only create/reset/soft-disable CLI, Argon2id, 8-hour opaque hashed
  sessions, login/me/logout/password APIs, CSRF/Origin protection and DB attempt
  windows. Password/reset/deactivation revoke sessions. No company/role authority.
- Auth audit records subject UUID/event/source/correlation/time. Trigger rejects
  UPDATE/DELETE/TRUNCATE; privileged DDL tampering is not prevented by dev setup.
  Migration refuses populated/offline downgrade; empty roundtrip/drift checks pass.
- Added compact account UI and MFA/security-approval plan. No signup/admin listing,
  MFA implementation, memberships/RLS/RBAC, approval or accounting workflows.
- Native HTTP smoke passed login/me/logout/replay through Vite/API on a generated
  disposable preview DB; browser verified bootstrap API connected and labelled form.
- Implementation `3e4bc828b5d0fbb9570b710576ceb51643fc6cb9` pushed to the stacked
  branch; [PR #2](https://github.com/jpdoestech/manpower-erp/pull/2) is open into
  feature/p0-02-infrastructure. PR #1 remains open into main. Neither was merged.
- Hosted [push CI 41759481411](https://github.com/jpdoestech/manpower-erp/actions/runs/41759481411)
  and [PR CI 41759551633](https://github.com/jpdoestech/manpower-erp/actions/runs/41759551633)
  pass backend/frontend/compose for the implementation. Native servers/PG cluster
  stopped, preview/test databases dropped, temporary credentials removed; input
  database still has zero public tables. No production data/deploy touched.

## P1-01 verification evidence (2026-11-04)

Host: Python 3.13.12, uv 0.13.7, Node 24.14.1/npm 11.19.1, PostgreSQL 18.3.
Backend commands run from backend using `..\.tools\Scripts\uv`; test DATABASE_URL
points to loopback 55432. New integration databases are generated and dropped by
the existing disposable fixture; no existing data or production migrations touched.

| Command | Result |
|---|---|
| `git fetch --all --prune`, `git branch -avv`, `git log --all --oneline --decorate -15`, `git ls-remote origin 'refs/pull/*'` | PASS; main b3517d3, P0-02 4fd3914, PR #1 head matches, no pre-existing uncommitted work |
| Prerequisite `uv sync --locked`, Ruff format/check, `mypy app tests alembic`, `pytest -q`, `pip-audit` | PASS; 36 tests, 13 typed/formatted files, audit clean |
| P1-01 `uv run --locked ruff format --check .`, `uv run --locked ruff check .` | PASS after formatting |
| `uv run --locked mypy app tests alembic` | PASS; 23 source files |
| `uv run --locked pytest -q` | PASS; 73 tests in 25.50s, no warnings |
| `uv run --locked pip-audit` / `uv lock --check` | PASS; no known vulnerabilities; graph locked |
| `npm run format:check`, `npm run lint`, `npm run typecheck` | PASS; 11 formatted/linted files; tsc exits 0 |
| `npm test` | PASS; 9 tests (5 original + 4 account-flow tests) |
| `npm run build` | PASS; 17 modules, Vite 8.3.5 |
| `npm audit --audit-level=low` | PASS; 0 vulnerabilities; frontend dependency graph unchanged |
| `python backend/tests/smoke_identity.py` with generated preview credentials in process env | PASS; HTTP login/me/logout/replay via http://127.0.0.1:5173; no credential output |
| `.\.tools\docker-compose.exe config --quiet` with process-local test password | PASS; includes safe cookie/origin configuration |
| `.\.tools\actionlint\actionlint.exe .github/workflows/ci.yml` | PASS; includes auth smoke before/after container recreation |
| `git diff --check` | PASS |
| Push CI 41759481411: backend job 126343491301, frontend 126343490882, compose 126343491154 | PASS; all three jobs |
| PR CI 41759551633: backend job 126343707641, frontend 126343707745, compose 126343707340 | PASS; all three jobs, compose 1m27s |

Hosted gates include clean/repeated upgrade/drift/empty downgrade/re-upgrade, all
backend/frontend checks and audits, and Docker HTTP authentication before and after
container recreation. Original bootstrap, dependency outage/recovery and persistent
cluster identifier checks also pass. CI evidence verified in authenticated GitHub
UI; no credentials were extracted for API polling. Documentation-only evidence
changes follow the verified implementation commit.

All previous Python lock versions retained (tomllib comparison to 4fd3914).
Only argon2-cffi 25.1.0, argon2-cffi-bindings 26.1.0, cffi 2.1.1, pycparser 3.12 added.
No frontend dependency added. Current-head migration tests independently verify
identity tables, repeat/check, empty downgrade/re-upgrade and populated refusal.
Historical no-schema baseline regression stays explicitly on 0001_infrastructure.
Tests also cover concurrent throttling, cookie/CSRF/Origin, cross-user self-only
identity, token replay/expiry/deactivation/reset/change and log redaction.

Initial issues corrected: the original frontend mock reused one Response body for
multiple requests; changed to fresh route-specific responses without weakening
bootstrap assertions. Ruff/import/test typing cleaned up. A transient Windows file
mapping blocked one CSS format write; rerun passed. No failed check counted as pass.

## Current next task / limits

Review stacked PR #2; merge nothing automatically. After PR #1 is reviewed/merged,
retarget #2 to main for separate security acceptance. P1-01 remains REVIEW under
ROADMAP's human-acceptance gate for high-risk changes. Recommend P1-02 only after
that gate and separate task authorization. PR #1 remains open into main.
Local Windows Docker engine unavailable; hosted Linux container/auth/persistence/
outage gates pass. MFA, breach-password blocklist, retention/edge throttling,
production roles/RLS/IdP/recovery and calibrated policies remain security review work.
No production readiness or financial-control certification. No production deployment.
Non-failing inherited CI annotations: checkout@v4 Node 20 metadata is deprecated
and GitHub forces it onto Node 24; ubuntu-latest is migrating to Ubuntu 26. These
are recorded for focused CI maintenance, with no unrelated action/runner upgrade
in this authentication slice. Dependency audits report zero known vulnerabilities.

## P1-01 changed files

- Auth: backend/app/identity/{__init__,models,security,service,routes,cli}.py;
  backend/app/main.py, backend/app/observability.py, backend/pyproject.toml, uv.lock.
- Migrations/tests: backend/alembic/env.py, versions/0002_identity.py;
  backend/tests/test_api.py, test_migrations.py, test_identity.py,
  test_identity_security.py, smoke_identity.py.
- UI: frontend/src/AuthPanel.tsx, AuthPanel.test.tsx, App.tsx, App.test.tsx, style.css.
- Delivery/docs: .env.example, compose.yaml, .github/workflows/ci.yml, README.md,
  docs/OPERATIONS.md, SECURITY_RBAC.md, adr/ADR-011-authentication.md;
  tasks/P1-01.md, P0-02.md, DECISIONS.md and STATUS.md.

## Historical P0-02 outcome
- P0-02 requested; clean main `b3517d3` matched origin and the reported scaffold.
  Created `feature/p0-02-infrastructure`; plan/tests are in `tasks/P0-02.md`.
  Reviewed all mandatory docs, source, lockfiles, Compose and CI; detailed ADRs
  recorded before implementing infrastructure. P0-01 evidence below is historical.
- Added SQLAlchemy 2.1.7/Alembic 1.20.1; all existing locked versions retained.
  The baseline creates only Alembic history; clean/repeated upgrade, drift check,
  safe downgrade/re-upgrade and unrelated-row preservation pass on disposable DBs.
- Added request sessions/pool disposal, live/ready separation, safe consistent
  errors, UUID correlation and whitelisted JSON logs. Frontend behavior unchanged.
- Implementation commit `b8e3f9e1b0a5f6d5ee7a293602cffa4ed4c33806` pushed to
  `feature/p0-02-infrastructure`; [PR #1](https://github.com/jpdoestech/manpower-erp/pull/1)
  remains open for review into main. No merge performed.
- Hosted [push CI 41752561626](https://github.com/jpdoestech/manpower-erp/actions/runs/41752561626)
  and [PR CI 41752609488](https://github.com/jpdoestech/manpower-erp/actions/runs/41752609488)
  both completed successfully on 2026-11-04. Backend, frontend and compose jobs all
  passed in both runs, including migrations and outage/recovery/persistence.
- P0-02 is DONE against its acceptance gates. Local isolated PostgreSQL cluster
  stopped; generated test databases cleaned up; input database has zero public
  tables. No production changes or P1-01 implementation performed.

## Historical P0-02 handoff / limits

Review PR #1; do not merge automatically. Recommend **P1-01** only on a separate
user request. No P1-01 work started.
CPA rounding/tax/GL policies, stakeholder hierarchy/role/delegation decisions and
production deployment/permissions remain unapproved; see ADRs. Runtime Compose
credentials remain development-only. Local Windows Docker engine is unavailable.

## P0-02 exact verification (2026-11-04)

Backend commands executed from `backend/` using `..\.tools\Scripts\uv` (uv 0.13.7,
Python 3.13.12). DATABASE_URL explicitly targeted isolated loopback PostgreSQL 18.3
on port 55432, ignored `.local/p0-02-postgres-data`. New tests create/drop only
generated disposable databases; the original input DB is not migrated.

| Command | Final local result |
|---|---|
| `..\.tools\Scripts\uv sync --locked` | PASS; 63 resolved, 61 checked on Windows |
| `..\.tools\Scripts\uv lock --check` | PASS; manifest/lock agree |
| `..\.tools\Scripts\uv run --locked ruff format --check .` | PASS; 13 files |
| `..\.tools\Scripts\uv run --locked ruff check .` | PASS after formatting/import cleanup |
| `..\.tools\Scripts\uv run --locked mypy app tests alembic` | PASS; 13 source files |
| `..\.tools\Scripts\uv run --locked pytest -q` | PASS; 36 tests, no warnings; original P0-01 tests preserved |
| `..\.tools\Scripts\uv run --locked pip-audit` | PASS; no known vulnerabilities |
| `..\.tools\Scripts\uv run --locked alembic upgrade head` (twice), `alembic check`, `alembic current`, `alembic downgrade base`, `alembic upgrade head`, `alembic check` (all prefixed `..\.tools\Scripts\uv run --locked`) | PASS on newly generated disposable CLI DB; head 0001_infrastructure; no upgrade operations detected; DB dropped after checks |
| `npm ci` (frontend) | PASS; 108 added, 109 audited |
| `npm run format:check` (frontend) | PASS; 9 files |
| `npm run lint` (frontend) | PASS; 9 files |
| `npm run typecheck` (frontend) | PASS; tsc exits 0 |
| `npm test` (frontend) | PASS; 5 tests |
| `npm run build` (frontend) | PASS; tsc/Vite 8.3.5, 16 modules |
| `npm audit --audit-level=low` (frontend) | PASS; 0 vulnerabilities |
| `.\.tools\docker-compose.exe config --quiet` (root; process-local test password) | PASS; Compose 5.7.0 |
| `.\.tools\actionlint\actionlint.exe .github/workflows/ci.yml` (root) | PASS; actionlint 1.7.12 |
| `git diff --check` | PASS |
| Hosted backend job 126320930700, push run 41752561626 | PASS; frozen install, format/lint/types, 32 unit/API tests, 4 PostgreSQL integration tests, migration CLI upgrade/repeat/check/downgrade/re-upgrade/check, audit |
| Hosted frontend job 126320929113, push run 41752561626 | PASS; install, format/lint/types, 5 tests, build, audit |
| Hosted compose job 126320929498, push run 41752561626 | PASS; clean build/boot, migration ordering, HTML/proxy/live/ready checks, DB stop → live 200/ready 503, DB restart/readiness recovery, migration check, persistent cluster identifier after container recreation; test volumes removed |
| PR run 41752609488 (jobs 126321088423/126321088735/126321088836) | PASS; compose/backend/frontend on PR merge ref |

Compared HEAD's uv.lock to the new lock using Python tomllib: **no previous package
version changed**; only sqlalchemy, alembic, mako and markupsafe were added.
Offline SQL generation is tested without connecting or disclosing credentials.
Migration tests prove only alembic_version exists after clean initialization,
single head/idempotence, downgrade safety and preservation of an unrelated row.
Session tests prove rollback-on-close/exception and explicit-commit persistence.

Initial issues resolved before delivery: Ruff formatting/import order and strict
test typing; two log-capture tests initially bound a pytest phase stream, corrected
to a stable StringIO using the real configured JSON handler. Added Alembic's
path_separator=os to remove deprecation warnings. No failed attempt counted as pass.

Hosted CI/PR evidence is linked above. Only documentation evidence changes follow
the verified implementation commit. No production migration/deploy or auto-merge.
Tenant/RBAC/Maker–Checker/financial tests are N/A without business records/workflows;
architecture documentation does not certify implementation of those controls.

## P0-02 changed files

- Runtime/config: `.env.example`, `backend/app/main.py`, `backend/app/database.py`,
  `backend/app/observability.py`, `backend/pyproject.toml`, `backend/uv.lock`,
  `backend/Dockerfile`, `compose.yaml`, `.github/workflows/ci.yml`.
- Migrations: `backend/alembic.ini`, `backend/alembic/env.py`,
  `backend/alembic/script.py.mako`, `backend/alembic/versions/0001_infrastructure_baseline.py`.
- Tests: `backend/tests/conftest.py`, `backend/tests/test_api.py`,
  `backend/tests/test_configuration.py`, `backend/tests/test_diagnostics.py`,
  `backend/tests/test_migrations.py`, `backend/tests/test_sessions.py`.
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY_RBAC.md`,
  `docs/OPERATIONS.md`, seven ADRs (001/002/003/005/006/009/010) under `docs/adr/`,
  `tasks/P0-02.md`, `tasks/STATUS.md`, `tasks/DECISIONS.md`.

## Historical P0-01 outcome

- Read all mandatory documents and wrote `tasks/P0-01.md` before coding.
- Original starter-pack report matched the code. The folder initially lacked Git;
  after the user initialized it, inspection found a clean governance-only commit.
  Git initialization also supplied `.gitattributes`; it now enforces LF on checkout.
- Added a minimal React/TypeScript page, public FastAPI bootstrap contract,
  PostgreSQL integration test, locked dependencies, lint/types/tests, local Compose,
  CI and contributor instructions. No accounting/business modules implemented.
- ADR-001 adopted for local bootstrap only; access surface documented in SECURITY_RBAC.
- Native HTTP smoke and browser inspection show the page and **API connected**.
  The bootstrap endpoint is static metadata, not a DB health check.
- All runnable local checks pass. The user subsequently authorized commit/push;
  implementation commit `f0c60ea0fed74edb56ba29bd29419a151b8be828` was pushed to main.
- Hosted [CI run 41749669989](https://github.com/jpdoestech/manpower-erp/actions/runs/41749669989)
  completed successfully on 2026-11-04: **backend**, **frontend**, and **compose**
  jobs all passed. Docker build/start, HTTP smoke and database volume persistence
  are now verified on the Linux runner. P0-01 is DONE; no P0-02 work started.
- No production deployment or production data changes were performed.

P0-01's next-task handoff was P0-02, which is the current authorized task above.

## Task evidence log
| Task | Date | Change / commit | Checks executed | Result | Reviewer |
|---|---|---|---|---|---|
| P0-01 | 2026-11-04 | f0c60ea; pushed to main | Commands below, `tasks/P0-01.md`, CI run 41749669989 | PASS; all acceptance gates, including hosted Docker boot/persistence | Automated checks; no human review claimed |
| P0-02 | 2026-11-04 | b8e3f9e; feature branch; PR #1 | P0-02 commands above; push/PR CI 41752561626/41752609488 | PASS; local and all hosted acceptance gates | Automated checks; PR review pending, no human review claimed |
| P1-01 | 2026-11-04 | 3e4bc82; stacked PR #2 | Current P1-01 evidence, CI 41759481411/41759551633 | All local/hosted gates pass; REVIEW for human security acceptance | No human review claimed |

## Historical P0-01 verification commands and results

Host: Windows, Node **24.14.1**, npm **11.19.1**, Python **3.13.12**, uv **0.13.7**,
isolated PostgreSQL **18.3**. uv was installed into the ignored `.tools` venv.
Backend commands used `..\.tools\Scripts\uv` from `backend/`. A fresh environment
was selected using `$env:UV_PROJECT_ENVIRONMENT='../.local/clean-backend'`.

| Directory | Exact command | Final result |
|---|---|---|
| backend | `..\.tools\Scripts\uv sync --locked` | PASS; fresh venv, 57 packages installed, 59 resolved across platforms |
| backend | `..\.tools\Scripts\uv lock --check` | PASS; lock matches manifest |
| backend | `..\.tools\Scripts\uv run --locked ruff format --check .` | PASS; 4 files already formatted |
| backend | `..\.tools\Scripts\uv run --locked ruff check .` | PASS; All checks passed |
| backend | `..\.tools\Scripts\uv run --locked mypy app tests` | PASS; no issues in 4 source files |
| backend | `..\.tools\Scripts\uv run --locked pytest -q -m 'not integration'` | PASS; 7 passed, 1 deselected; no warnings |
| backend | `..\.tools\Scripts\uv run --locked pytest -q -m integration` | PASS; 1 passed, 7 deselected; no warnings |
| backend | `..\.tools\Scripts\uv run --locked pip-audit` | PASS; No known vulnerabilities found |
| frontend | `npm ci` | PASS; 108 packages added, 109 audited |
| frontend | `npm run format:check` | PASS; Biome checked 9 files |
| frontend | `npm run lint` | PASS; Biome recommended rules, warnings fail, 9 files |
| frontend | `npm run typecheck` | PASS; tsc exits 0 |
| frontend | `npm test` | PASS; 1 file, 5 tests |
| frontend | `npm run build` | PASS; tsc + Vite 8.3.5, 16 modules; output in ignored dist |
| frontend | `npm audit --audit-level=low` | PASS; 0 vulnerabilities |
| root | `.\.tools\docker-compose.exe config --quiet` | PASS with process-local POSTGRES_PASSWORD; Compose 5.7.0 standalone |
| root | `.\.tools\docker-compose.exe config --format json` | PASS; asserted db/api/web published host_ip equals 127.0.0.1 |
| root | `.\.tools\docker-compose.exe config --quiet` with password unset | Expected nonzero; missing-password configuration rejected |
| root | `.\.tools\docker-compose.exe up --build --wait --wait-timeout 180` | NOT PASSED; Docker engine named pipe does not exist |
| root | `.\.tools\actionlint\actionlint.exe -color .github/workflows/ci.yml` | PASS; actionlint 1.7.12 exits 0; no hosted execution implied |
| root | `git diff --check` | PASS; exit 0 |
| root | `git check-ignore .env .local/p0-01-postgres-data/PG_VERSION backend/.venv/pyvenv.cfg frontend/node_modules/react/package.json .tools/docker-compose.exe` | PASS; all ignored |
| hosted CI | `backend` job: locked install, Ruff, mypy, API tests, PostgreSQL integration, pip-audit | PASS; run 41749669989, job 126311356836 |
| hosted CI | `frontend` job: npm ci, format/lint/types/tests/build/audit | PASS; run 41749669989, job 126311356732 |
| hosted CI | `compose` job: `docker compose config --quiet`, `docker compose up --build --wait --wait-timeout 180`, HTML/proxy assertions, `docker compose down`, `docker compose up --wait --wait-timeout 180`, cluster identifier comparison | PASS; run 41749669989, job 126311356501; test volume cleaned up |

Database test environment: `$env:DATABASE_URL='postgresql://postgres@127.0.0.1:55432/postgres'`.
An isolated cluster was initialized under ignored `.local/p0-01-postgres-data`
using `initdb.exe -D .local/p0-01-postgres-data -U postgres --auth=trust --encoding=UTF8 --locale=C`.
Only loopback port 55432 was bound with `pg_ctl.exe -D .local/p0-01-postgres-data -l .local/postgres.log -o '-h 127.0.0.1 -p 55432' -w start`.
This test-only cluster contains no real records and is now stopped; native API
and Vite processes were also stopped after verification.

HTTP checks: ran `uv run --locked uvicorn app.main:app --host 127.0.0.1 --port 8000`
and `npm run dev`; Python urllib assertions verified the HTML title at port 5173
and exact `{name: 'Manpower ERP', stage: 'bootstrap'}` JSON through its `/api/bootstrap`
proxy. Browser AX/screenshot inspection confirmed visible heading and connected
status. See P0-01.md for the full HTTP assertion command.

Migration review: no SQL/migration files or domain schema were introduced. A
psycopg inspection of `information_schema.tables` confirmed **0 public tables**
after integration testing. Migration up/down is N/A until P0-02. Tenant/RBAC,
Maker–Checker and financial reconciliation tests are N/A for this metadata-only
bootstrap; these controls are not implemented or claimed to pass.

Earlier findings resolved: initial Ruff line-length issues were formatted; initial
ESLint/minimatch audit reported 11 moderate findings, removed by using Biome;
Starlette's httpx deprecation was removed by using httpx2. An optional native psql
schema-inspection command could not execute (invalid OS executable); the equivalent
inspection passed using psycopg. No failed check is counted as a pass.

## Changed files

- Root: `.gitattributes`, `.gitignore`, `.dockerignore`, `.env.example`,
  `.node-version`, `compose.yaml`, `README.md`, `.github/workflows/ci.yml`.
- Backend: `backend/.python-version`, `backend/pyproject.toml`, `backend/uv.lock`,
  `backend/Dockerfile`, `backend/app/__init__.py`, `backend/app/main.py`,
  `backend/tests/test_api.py`, `backend/tests/test_database.py`.
- Frontend: `frontend/package.json`, `frontend/package-lock.json`,
  `frontend/tsconfig.json`, `frontend/biome.json`, `frontend/vite.config.ts`,
  `frontend/Dockerfile`, `frontend/index.html`, `frontend/src/main.tsx`,
  `frontend/src/App.tsx`, `frontend/src/style.css`, `frontend/src/App.test.tsx`,
  `frontend/src/test-setup.ts`.
- Governance: `docs/SECURITY_RBAC.md`, `tasks/P0-01.md`, `tasks/DECISIONS.md`,
  `tasks/STATUS.md`, `AGENTS.md` (standing commit/push preference).

## Open blockers / compliance decisions
- Confirm legal entity types (labor service cooperative vs corporation), tax status and approved CPA treatments per company.
- Confirm company scope and branch establishment registration model.
- Confirm exact document series and invoice design with tax reviewer.
- Local Docker engine absent; container builds, volume persistence and Linux runtime
  passed on hosted CI. Windows Docker Desktop execution remains unverified. Branch
  protection is not configured/verified. Commit/push explicitly authorized by user.
- Production deployment/secrets remain undecided. Base image tags can receive patches;
  this is locked language dependency installation, not byte-reproducible OS images.

## Session handoff template
- Goal:
- Files changed:
- Schema/API changes:
- Tests and exact outputs:
- Security/accounting impacts:
- Known limitations:
- Next task ID:
