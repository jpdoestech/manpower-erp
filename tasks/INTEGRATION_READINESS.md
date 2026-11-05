# Controlled integration readiness — local foundation release candidate

2026-11-05, Asia/Manila. Status: REVIEW; not a security acceptance/release.

## Plan and acceptance before changes

1. Fetch branches; inspect all PR #1–#11 heads, bases, checks, reviews and threads.
   Prove ancestry/merge bases, disjoint incremental commits and patch duplication;
   distinguish old matching-head checks from new integrated evidence.
2. Create release/rc-2026-11-05 from the existing complete stack at 2232702.
   Preserve commit identities, local files and production data. No PR merge,
   cherry-pick/rebase or runtime change is needed if ancestry is already linear.
3. Run available local SQLite/authentication/migration, Windows launcher,
   frontend/browser accessibility, format/lint/type/build/lock/audit/static checks.
   Use only disposable fixtures. Verify real PostgreSQL, Docker and fresh Windows
   workflow in RC CI when unavailable locally; never replace missing tests with
   an assertion of success. Keep developer listeners/data intact.
4. Consolidate PR readiness, integration order, conflicts/dependency findings,
   exact evidence and remaining human decisions. Add an owner/reviewer checklist;
   keep P1-01 A1–A9/B1–B9 and all pending records unchanged.
5. Update STATUS/ROADMAP, commit/push the isolated RC and open a draft review PR.
   New RC CI must supply current integration evidence; no main merge, production
   operation, pending milestone DONE or Supabase implementation.

Acceptance: all eleven PRs accounted for, ancestry/order proven, RC contains all
implemented features, exact local/CI results and unrun limits recorded, no hidden
critical failure, independent decisions explicitly pending, clean committed/pushed
tree and a reviewable integration checklist. This is a development RC, not a
production release or CR-002C authorization.

## Evidence

Audit and execution results pending below. Initial git fetch attempts failed with
GitHub port-443 connection errors; connector PR heads/checks are available. No
remote freshness claim is made for those failed fetches.

## Branch ancestry and integration order

Main remains b3517d3d172aabbccc13682ce839d34cbd940b2e (P0-01). The connector
inventories all 12 original remote branches (second page empty); each matches
the local head. Repeated CLI fetch fails before transfer: connector data is the
fresh snapshot, not evidence that those fetch commands succeeded.

All PRs #1–#11 are open/unmerged, #4/#11 draft. Each has zero submitted reviews
and zero review threads; current configured-base mergeability is true for all.

| PR | Head | Current base | Successful checks | Evidence |
|---|---|---|---|---|
| [#1](https://github.com/jpdoestech/manpower-erp/pull/1) | 4fd3914 | main | 6/6 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41752943625/job/126322179926) |
| [#2](https://github.com/jpdoestech/manpower-erp/pull/2) | dc7fca3 | feature/p0-02-infrastructure | 6/6 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41760549728/job/126346975466) |
| [#3](https://github.com/jpdoestech/manpower-erp/pull/3) | 37dbd7f | feature/p1-01-authentication | 6/6 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41765508990/job/126362815953) |
| [#4](https://github.com/jpdoestech/manpower-erp/pull/4) | d8d1cd6 | feature/p1-01-account-controls | 6/6 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41775979895/job/126396311872) |
| [#5](https://github.com/jpdoestech/manpower-erp/pull/5) | 19a0ba7 | feature/p1-02-organizations | 8/8 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41782640611/job/126417512620) |
| [#6](https://github.com/jpdoestech/manpower-erp/pull/6) | 65246ba | feature/windows-local-launchers | 10/10 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41790760958/job/126443340754) |
| [#7](https://github.com/jpdoestech/manpower-erp/pull/7) | 17e5bfb | feature/cr-002a-database-compatibility | 10/10 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41797888437/job/126466252678) |
| [#8](https://github.com/jpdoestech/manpower-erp/pull/8) | 9e44c96 | feature/cr-002b-local-setup-start | 10/10 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41825405321/job/126558758697) |
| [#9](https://github.com/jpdoestech/manpower-erp/pull/9) | fbaa78c | fix/local-account-error-messages | 10/10 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41841664110/job/126614554142) |
| [#10](https://github.com/jpdoestech/manpower-erp/pull/10) | e4608e1 | feature/cr-002b-completion | 10/10 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41854609216/job/126659713079) |
| [#11](https://github.com/jpdoestech/manpower-erp/pull/11) | 2232702 | feature/ui-001-design-system | 10/10 | [matching-head CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41863177900/job/126690379015) |

Recommended order: **#1 -> #2 -> #3 -> #4 -> #5 -> #6 -> #7 -> #8 -> #9 -> #10 ->
#11**. Incremental commit counts: 2/2/2/2/3/2/2/2/5/2/1, totaling **25 unique
commits**, no overlap and no duplicate stable patch IDs. Each base is exactly
the previous head and its ancestor. Main is ancestor of the complete stack.
No missing feature cherry-pick, rebase or branch-to-branch merge is needed.

Release candidate **release/rc-2026-11-05** starts at
22327029a121ef6d0756e44a4a0401e221d84e26. It already contains every implemented
P0/P1 identity, SQLite/native tooling, diagnostic fix and UI change. Added
integration docs introduce no runtime, dependency, migration or provider changes.

Maintainer sequence: accept each predecessor and preserve head history, integrate,
retarget the next PR to main and recheck the new diff/merge base. Squash/rebase of
earlier heads would invalidate this original ancestry proof unless descendants
are also rewritten/reviewed. Use the cumulative RC for validation, not a bulk
route around human acceptance. After originals land, reconcile its remaining
documentation diff rather than importing a second independent feature stack.

## Technical readiness versus approval

| PR | Technical assessment | Unresolved condition |
|---|---|---|
| #1 | Infrastructure/health/migrations/logging; 6/6 pass | Owner review/integration; no production acceptance |
| #2 | Local identity/opaque sessions; 6/6 pass | Independent human A1–A9 decision at dc7fca3 |
| #3 | Admin pair/Maker–Checker/recovery; 6/6 pass | Separate human B1–B9 at 37dbd7f, including inherited #2 |
| #4 | Checklist and P1-02 proposal only; 6/6 pass, draft | Documentation review; no organization runtime authorization |
| #5 | Docker BAT tooling; 8/8 pass | Owner/inherited security review; Docker prerequisite |
| #6 | SQLite compatibility; 10/10 pass | A phase acceptance; SQLite locking/guards security impact |
| #7 | Native setup/start slice; 10/10 pass | Review together with full B; no retroactive A acceptance |
| #8 | Sanitized provisioning diagnostics; 10/10 pass | Message/secret review; original interactive cause unconfirmed |
| #9 | Complete nine-tool lifecycle/recovery; 10/10 pass | B/inherited acceptance and filesystem/recovery limits |
| #10 | Responsive shell/primitives; 10/10 pass | UI/usability review and relevant inherited security findings |
| #11 | C strategy/plan only; 10/10 pass, draft | Technical review, not Supabase implementation permission |

Checks match current heads; none is stale by SHA. Earlier PRs ran 3/4 jobs per
event instead of today's five and cannot certify a future retargeted base.
The new RC needs its own current integration checks. Empty reviews do not imply
approval, and automated compatibility does not decide unresolved security risks.

## Dependencies and configurations

Node 24, Python 3.13.18, React/React DOM 19.3.1, Vite 8.3.5, SQLAlchemy 2.x/Alembic
and PostgreSQL 18 remain compatible in the exercised graph. Backend lock check/
sync dry-run: 67 resolved/65 installed, no changes. npm dependency graph exits 0,
problems []; missing other-platform optional packages are expected on Windows.
Build/types/tests show no required-dependency incompatibility. pip-audit finds no
known vulnerabilities; npm audit reports zero. OS/container/production security
certification is not inferred. No dependency or lockfile changed.

## Fresh regression commands and results

| Directory / command | Result |
|---|---|
| root: `cmd.exe /d /c "test-local.bat < nul"` | Exit 0: 110 backend / 42 deselected (52.10s), launcher/database safety passes with opt-in startup skipped, 27 frontend (21.60s) |
| frontend: `npm run format:check`, `npm run lint`, `npm run typecheck`, `npm run build` | Pass; 22 files formatted/linted; production bundle built |
| frontend: `npm ls --all --json` | Exit 0, problems [] |
| frontend: `npm audit --audit-level=low` | 0 vulnerabilities |
| frontend: `npm run test:browser` | 27 passed (2.0m), nine 320–2560px viewport/input profiles, light/dark, axe and keyboard/focus checks |
| backend: `uv lock --check`, `uv sync --locked --dry-run` | Pass; no environment changes required |
| backend: `uv run --locked ruff format --config pyproject.toml --check . ../scripts` | 37 files already formatted |
| backend: `uv run --locked ruff check --config pyproject.toml . ../scripts` | Pass |
| backend: `uv run --locked mypy app tests alembic ../scripts` | Pass, 37 files |
| backend: `uv run --locked pip-audit` | No known vulnerabilities |
| backend: `uv run --locked pytest -q -m integration` | 42 passed / 110 deselected (98.34s), actual PostgreSQL 18.3 |
| backend: `uv run --locked alembic upgrade head` twice, `check`, `downgrade base`, `upgrade head`, `check` | Pass; no schema drift |
| root: `.tools/docker-compose.exe --env-file .env.example config --quiet` | Pass with process-only synthetic POSTGRES_PASSWORD |
| root: `.tools/actionlint/actionlint.exe` | Pass |

Python commands use .tools/Scripts/uv.exe. PG tests used a new ignored cluster
.local/rc-20261105-pg-90f5b34814be4c61a6022b0a7247f950, loopback 6543, test-only
trust auth and synthetic data. Fixtures create/drop generated databases; migration
CLI targets that cluster's empty postgres DB. Cluster stopped and retained offline.
First start on 55435 failed because Windows excludes 55394–55493; retry on available
6543 passed without changing code or machine permissions.

Actual isolated Windows nine-command smoke passes (final local evidence below).
Docker executable/engine is absent locally; fresh hosted
Compose startup/auth/outage/recovery/persistence remains required. No production
data, user credentials, fiscal document or deployment was touched.

## Exact remaining security decisions and C authorization

SECURITY_ACCEPTANCE_P1-01.md retains all eighteen unchecked human items and two
PENDING HUMAN REVIEW records. Separate qualified human decisions are needed:

- PR #2 A1–A9: hashing/authentication, sessions, CSRF/Origin, operator provisioning,
  CLI recovery, privilege boundaries, audit, cross-user/forged-authority denial
  and abuse/config/migration safety.
- PR #3 B1–B9: inherited controls, admin CSRF, protected pair bootstrap, independent
  lifecycle, single-use recovery, identity/private delivery procedures, admin
  availability/custody, audit/migrations and identity-only company boundary.
- For each: exact reviewed SHA, reviewer identity/qualification/independence,
  date/timezone, decision, conditions/findings with owner and verified resolution,
  and GitHub review reference. One decision never supplies the other's approval.
- Disposition R1–R8: MFA/step-up; manual recovery; Super Admin/operator total loss;
  production TLS/secrets/roles; abuse/session policy; audit/DPO retention/tamper
  limits; future tenant/RLS; integration/rollback. Classify development versus
  production conditions rather than silently waiving them.
- Review cumulative auth-related deltas (#6 SQLite, #8 diagnostics, #9 recovery,
  #10 auth rendering/storage), preserving earlier exact-SHA decisions and recording
  RC-specific conditions. DML guards do not protect against a privileged DDL owner.

Complete [owner/reviewer checklist](../docs/INTEGRATION_REVIEW_CHECKLIST.md).
To start C: record actual B/inherited phase acceptance and both P1-01 decisions/
conditions; verify accepted integration ancestry and relevant UI findings; approve
ADR-017 C-D1–7 token custody/encryption/key rotation, cloud login/JWT policy,
live revocation, immutable identity linking/external-only credential migration,
admin MFA/reauth/recovery and same-origin topology. Provide an authorized
disposable project/configuration/secret custody and both-provider test lane,
then record actual C implementation authorization. No merge, deployment D,
transfer E, company grants or P1-02 permission follows automatically.

## Remaining limits

Human acceptance remains pending; no milestone is newly marked DONE. Company
records/RBAC/RLS and Supabase Auth remain absent. Physical devices, Safari/Firefox,
screen readers, real hidden TTY/browser-opening, forced crash cleanup and production
recovery are unverified. Native backups stay trusted local/current-revision and
unencrypted. Git transport failures and local Docker availability remain visible;
passing CI does not invent a successful local run or human decision.

## Final local candidate verification / publication boundary

`ERP_NATIVE_SMOKE=1 uv run --locked python -m unittest discover -s ../scripts/tests
-p test_native_launchers.py -k actual_bats -v` from backend passes: **1 test,
447.604s, OK, no skip**. It verifies all nine actual BATs in an isolated path with
spaces/ampersand: repeated setup, start/readiness, real ordinary-user login/me/
CSRF logout, check, live backup, repeated stop, restore/reset/restore, repeated
migrate and test-local. Generated fixture accounts/data only; fixed root workspace
DB was not migrated/reset/restored. Owned test processes stopped and ports released.

The normal launcher discovery contains 30 cases: its earlier test-local run has
29 passing plus the one opt-in smoke skipped; the separate real smoke above
supplies that missing case. Do not call the earlier skipped run a no-skip run.
Other exact local counts: 110 backend/SQLite, 42 actual PG, 27 frontend and
27 nine-profile browser checks; no unresolved local test failure after the
documented reserved-port retry. Node 24.14.1/npm 11.19.1, uv 0.13.7,
Python 3.13.18/SQLite 3.53.1 and PostgreSQL 18.3 were used.

Protected-file comparison against 2232702 confirms backend/frontend/scripts/CI,
dependency locks, migrations and SECURITY_ACCEPTANCE_P1-01.md unchanged. Document
links/checklist counts and staged whitespace are checked before publication.
Git transport failures are retained above; the authorized connector publishes
only this RC ref and documentation objects. Tree/parent/SHA consistency must be
verified locally and remotely, with no main or predecessor-ref update.

Fresh candidate CI must run all five jobs (push and candidate PR): backend/PG/
migration/audit, frontend/browser/audit, native Windows SQLite/full workflow,
legacy Windows BATs and Docker Compose. Existing PR checks above are historical
matching-head evidence, not a claim that the new RC already ran them. Final RC
head/run URLs and pass/fail/pending state are recorded in its draft PR description
and completion report. Hold integration until those checks and human conditions
are actually satisfied; leave all pending milestones unchanged.
