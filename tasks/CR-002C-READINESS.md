# CR-002C preparation — implementation and acceptance review

Review date: 2026-11-04, Asia/Manila. Read-only product review plus planning docs.
This is automated/source evidence, not independent human security acceptance.

## Repository and PR audit

Fresh fetch, clean starting worktree. Latest implementation branch:
feature/ui-001-design-system at **e4608e19ca2e62578a509e5876fd050375256b0c**.
Planning branch docs/cr-002c-provider-plan starts there. main remains b3517d3
(P0-01); all PRs #1–#10 remain open/unmerged, #4 draft. #10 is stacked on #9,
#9 on #8; no automatic integration is presumed. All remote/local branch heads
were inspected; no newer provider branch or Supabase implementation was found.

GitHub submitted-review lists for #2, #3, #9 and #10 are empty. The two P1-01
acceptance records remain PENDING HUMAN REVIEW; no accepted SHA, reviewer, date,
conditions or decision reference is supplied. CR-002A/B and UI-001 remain REVIEW.

## Acceptance traceability — existing SQLite tools

| Requirement | Actual source/test evidence | Assessment |
|---|---|---|
| Nine native commands | Root setup/start/stop/test/check/migrate/backup/restore/reset BATs delegate to scripts/windows/local.py; real native smoke in scripts/tests/test_native_launchers.py | Implemented; matching-head Windows CI exercises all nine |
| Offline local auth/config | environment() forces local+SQLite/loopback; setup reuses hidden-prompt ordinary account CLI, no default administrator; fail-closed config tests | Implemented; no Supabase Auth calls/SDK |
| Ownership-safe stop | runtime.py held Windows lock and random instance request; local.stop only uses original still-live Popen for cleanup; stale/unmanaged refusal tests | Implemented within documented cooperative lifecycle |
| Safe backup/WAL | database_tools.snapshot uses SQLite backup API, fixed DB and separate .local-backups; integrity/FK/revision/guard validation, exclusive generated names | Implemented; live/uncommitted-writer and invalid-path/guard tests |
| Confirmed recoverable reset/restore | offline locks/ports, typed phrase, pre-change snapshot, migrated candidate, SQLite checkpoint and os.replace; failure/cancel tests | Implemented; original/recovery retained; no cloud target |
| Identity/security preservation | Restore revokes sessions/resets/pending requests, appends audit; UUID/FK/guard preservation tests and dual-dialect identity regressions | Implemented for current six-table identity schema, not future provider state |
| Reproducible checks/startup | Locked tool versions, repeat setup/migration, HTTP login/me/CSRF logout, repeated stop, recovery flow and CI | Passing automated evidence; human acceptance still pending |

Re-fetched PR #9 head fbaa78c has **10/10 success**:
[push 41841656509](https://github.com/jpdoestech/manpower-erp/actions/runs/41841656509),
[PR 41841664110](https://github.com/jpdoestech/manpower-erp/actions/runs/41841664110).
Downloaded Windows job 126614553627 confirms 110 backend passes (15.89s), all nine
commands and 30 launcher/safety tests (190.751s). This is reused historical evidence
for the unchanged exact head, not a fresh local startup claim.

Limits: unencrypted trusted current-revision snapshots, local disk/OS-user custody,
old launcher Enter shutdown, unmanaged/crashed-owner recovery, hidden real TTY,
browser opening and forced-OS-crash paths remain as documented. Do not turn this
review into production recovery, financial concurrency or formal B acceptance.

## Acceptance traceability — UI-001 / PR #10

| Requirement | Actual source/test evidence | Assessment |
|---|---|---|
| Responsive shell | ApplicationShell.tsx, style.css: labeled/collapsed sidebar, tablet rail, phone drawer/bottom bar; playwright.config nine profiles 320–2560px | Implemented; no page overflow in tested Chromium profiles |
| Header/breadcrumb/account/theme | Shell state + native account details; App theme preference only; optional My account password form | Implemented; no forced password-change workflow |
| Search/context/notifications | Static module search; disabled company/branch selector; explicit unconnected notifications state | Implemented interface; no record search or organizational authority |
| ERP destinations | navigation.ts includes all twelve requested modules; administration disabled, others clear placeholders | Implemented catalogue; no fake records/totals or admin UI |
| Shared components/states | ui/components, Icon, Reference; labeled native controls/date/datalist, table, dialog/confirmation/tabs/badges/validation/toast/skeleton and state patterns | Implemented; native behavior limitations documented |
| Auth integration | AuthPanel retains transport/CSRF/secret-clearing; render boundary only after validated account; RecoveryForm unchanged; logout failure visible | Source and component/backend regressions pass |
| Accessibility/devices | Keyboard tabs/modal Escape/focus, labels/axe light/dark scans, no overflow, touch targets, synthetic browser fixtures | Passing automated coverage; not physical-device or screen-reader certification |
| Local compatibility | No backend/migration/tool implementation change from #9; full native Windows CI includes updated frontend tests | Passing; no production/hosting claim |

Re-fetched PR #10 head e4608e1 has **10/10 success**:
[push 41854596698](https://github.com/jpdoestech/manpower-erp/actions/runs/41854596698),
[PR 41854609216](https://github.com/jpdoestech/manpower-erp/actions/runs/41854609216).
Downloaded job logs confirm:

- 126659712968: 110 unit/SQLite tests (10.89s), 42 real PostgreSQL tests (13.24s),
  migration CLI, Ruff/mypy and pip-audit pass, no known vulnerabilities.
- 126659712440: 27 frontend tests, 27 browser tests (44.6s), build and npm audit
  pass; no vulnerabilities. Browser fixtures do not prove live provider behavior.
- 126659713079: 110 Windows backend tests (10.88s), all nine tools and 30 native/
  safety tests (158.960s), no skips. Compose health/auth/outage/recovery/persistence
  gates are successful in the same matching-head run.

## Fresh checks in this preparation turn

| Directory / exact command | Observed result |
|---|---|
| root: git fetch --all --prune; status/branch/log inspection | Fetch succeeds, initial tree clean, heads unchanged |
| backend: `..\.tools\Scripts\uv.exe run --locked pytest -q -m "not integration"` | 110 passed, 42 deselected, 33.91s |
| frontend: `npm test` | 27 passed, 5 files, 16.50s |
| frontend: `npm run test:browser` | 27 passed, nine profiles, 1.3m |

Do not relabel previous CI commands as newly run locally. PostgreSQL/Docker/full
fixed-port native startup and audits/lint/type/build are reused from exact-head
CI logs above. Existing API/Vite listeners remain 8000:23068 and 5173:27032; no
developer login/password, backup/reset/restore or stop action performed. New
provider tests/live project do not exist and were not run.

Documentation validation also passes: all local links in four planning/review
documents resolve; seven gates/decision groups and twelve acceptance groups exist;
all eighteen human checklist items and both pending decision records are unchanged.
`git diff --quiet e4608e1 -- backend frontend scripts .github tasks/SECURITY_ACCEPTANCE_P1-01.md`
and `git diff --check` pass. Changed files are documentation only.

## Differences and remaining readiness requirements

1. Implemented and CI-verified is not merged or accepted. main still lacks the
   feature stack. Historical task entries describe older source checkpoints;
   current head/CI evidence above supersedes them for this audit without rewriting
   the historical record or marking pending milestones DONE.
2. AUTH_PROVIDER=supabase still deliberately raises an error in auth_settings().
   DATABASE_MODE=supabase only configures PostgreSQL TLS. No JWT library/adapter,
   external identity mapping, cloud refresh state or provider MFA exists.
3. Principal currently holds local User/AuthSession/raw cookie at the auth boundary;
   administration.reauthenticate verifies a local password hash. Provider support
   needs reviewed seams at every caller, not a JWT middleware bolted onto /me.
4. User.password_hash is mandatory today. External-only credentials and additive
   migration/SQLite trigger-preservation decisions are missing from runtime;
   the new plan addresses them without changing the database now.
5. Restore knows only existing tables/capabilities. Any provider session/refresh/
   operation tables must extend validation and revocation before C can pass.
6. No actual company membership/RBAC tables or resource APIs exist. A deny-all
   scope interface can preserve the boundary; it cannot certify tenant isolation.
7. No real Supabase project, live-session revocation channel, token encryption-key
   custody, cloud administrator proof/recovery or Vercel topology is accepted.
   JWT signature validity alone cannot fill those gaps. P1-01 security acceptance
   remains an implementation blocker; UI device/usability acceptance stays pending.

Conclusion: SQLite tools and UI-001 satisfy the automated acceptance evidence
reviewed here, with documented human/operational limits. **CR-002C is ready for
technical review, not implementation.** Exact gates G1–7, decisions C-D1–7 and
acceptance tests C-A1–12 are in [CR-002C.md](CR-002C.md). No runtime repair is
authorized or required by this planning-only change; unresolved review conditions
must be assessed by their actual owners, not waived by the agent.
