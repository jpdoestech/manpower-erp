# P1-01 — Independent human security acceptance

Document prepared: 2026-11-04. Overall decision: **PENDING HUMAN REVIEW**.
The user explicitly confirmed that acceptance has not been granted or recorded.
Automated checks are supporting evidence, not human acceptance or a security audit.
P1-01 remains REVIEW; dependent P1-02 implementation remains BLOCKED.

## Review procedure and evidence rules

1. A qualified independent human reviewer inspects the pinned PR diff, inherited
   controls, tests and operational instructions. Record their identity, relevant
   security qualification/responsibility and independence; do not invent these.
2. Use synthetic users and disposable PostgreSQL only. Reproduce relevant negative
   cases with separate browser profiles/cookie jars; do not test production accounts.
   Never attach raw passwords, session/recovery tokens, cookies, DSNs or real data.
3. Leave each checkbox unchecked until the human reviews it. For every item, record
   PASS, FAIL or justified NOT APPLICABLE, evidence/reference and findings. An
   existing passing test does not check off a human-review item automatically.
4. Record findings with severity, affected PR/SHA, impact, required fix/condition,
   owner, verification evidence and due milestone. Unknown owner/date stays unset.
   Evaluate the outstanding risks below; do not silently waive them.
5. Each PR needs its own actual reviewer decision and GitHub review permalink tied
   to the reviewed SHA. Re-review relevant changes if either head changes. PR #3
   must be assessed with PR #2 inherited behavior, not only its incremental diff.
6. Allowed human outcomes: ACCEPTED FOR DEVELOPMENT, CHANGES REQUIRED, REJECTED,
   or PENDING HUMAN REVIEW. Record any conditions and whether they block P1-02.
   Conditional approval with unsatisfied prerequisite conditions does not open the
   gate. No unresolved critical defect may be treated as accepted.
7. Only after both actual acceptances and applicable conditions are verified may
   the maintainer record P1-01 DONE. Re-fetch and verify the chosen P1-02 base
   contains the accepted revisions. Never merge automatically. Development
   acceptance does not authorize production or certify future tenant isolation.

## PR #2 — Authentication and session foundation

[PR #2](https://github.com/jpdoestech/manpower-erp/pull/2), head
`dc7fca3c5b747a0ec245dc02973b07bf087277e5`; base feature/p0-02-infrastructure.
Implementation `3e4bc828b5d0fbb9570b710576ceb51643fc6cb9`.

| Review record | Actual recorded value |
|---|---|
| Decision | **PENDING HUMAN REVIEW** |
| Reviewer identity | Not provided |
| Qualification/responsibility and independence | Not provided |
| Review date/time with timezone | Not recorded |
| Human-confirmed reviewed SHA | Not recorded; proposed target is pinned above |
| Conditions, findings and dispositions | Not assessed by a human |
| GitHub review permalink | Not provided |
| Authorization to begin dependent implementation | Not granted |

Every item below is pending human assessment:

- [ ] **A1 Authentication:** inspect Argon2id parameters, 15–128 character validation,
  unchanged passphrases, normalized unique usernames, dummy verification and generic
  unknown/wrong/inactive failures; verify no plaintext credential persistence.
- [ ] **A2 Sessions:** inspect random opaque token generation/hash-only persistence,
  eight-hour absolute expiry, rotation of presented cookie, logout/replay and
  all-session revocation on password change/operator reset/deactivation. Verify
  host-only Path=/api, HttpOnly, SameSite=Strict, Secure default and no-store headers;
  assess browser storage and the explicit loopback HTTP exception. No refresh token.
- [ ] **A3 CSRF:** reproduce missing/wrong/other-user CSRF denial for protected
  mutations; foreign/duplicate Origin and privilege-payload rejection. Review login
  Origin validation and missing-Origin allowance for native clients; assess actual
  browser behavior, not only API tests. No permissive CORS may be introduced.
- [ ] **A4 Provisioning:** inspect operator create/deactivate/reset commands, hidden
  confirmed prompts, refusal of echoing fallback, duplicate rejection and no default
  credentials/public signup. Assess privileged CLI/DB access and independent custody.
- [ ] **A5 Recovery baseline:** inspect CLI-only password reset and session revocation.
  PR #2 has no token recovery/admin bootstrap; assess those in PR #3 rather than
  marking them implemented here. Review owner verification and operator misuse risks.
- [ ] **A6 Privilege boundaries:** login grants self-session access only; no company
  or financial grants, grant payloads or public user administration. Assess the CLI
  trust boundary; it cannot constrain an operator already holding DB-owner access.
- [ ] **A7 Audit:** verify success/failure/throttle/password/operator events, UUID
  correlation, safe logs and rejected UPDATE/DELETE/TRUNCATE. Review audit custody,
  read permissions and the privileged-DDL limitation; no financial-ledger assurance.
- [ ] **A8 Isolation:** reproduce forged user/company/role header denial, cross-user
  CSRF checks and unavailable company/business routes. Company-owned records/RLS
  do not exist; these tests do not prove future Company A/B data isolation.
- [ ] **A9 Abuse/configuration/migrations:** inspect concurrent durable name/global
  limits, timed lockout, unsafe Origin/cookie configuration rejection, safe errors,
  clean migration/drift/empty rollback and refusal to erase populated audit history.

Evidence pointers (reported checks; human assessment still pending):

- [P1-01 report](P1-01.md), [ADR-011](../docs/adr/ADR-011-authentication.md),
  [security matrix](../docs/SECURITY_RBAC.md), [operations](../docs/OPERATIONS.md).
- Pinned PR files: app/identity/{security,service,routes,cli,models}.py,
  app/{database,observability,main}.py; migration 0002_identity; AuthPanel/UI tests.
- Tests: test_identity_security.py, test_identity.py, test_diagnostics.py,
  test_migrations.py. Use the PR #2 versions, not PR #3's expanded head assertions.
- Reported 73 backend/9 frontend tests; [head push CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41760545518)
  and [head PR CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41760549728)
  have six successful checks in the prerequisite audit. Reconfirm at review time.

## PR #3 — Administrator controls and password recovery

[PR #3](https://github.com/jpdoestech/manpower-erp/pull/3), head
`37dbd7f2280e6b89919f7bf3d5e69954c67c1968`; base feature/p1-01-authentication.
Implementation `5ca0ad3ab96e1e0fb3ea68f83ddc6302d5c061c3`.

| Review record | Actual recorded value |
|---|---|
| Decision | **PENDING HUMAN REVIEW** |
| Reviewer identity | Not provided |
| Qualification/responsibility and independence | Not provided |
| Review date/time with timezone | Not recorded |
| Human-confirmed reviewed SHA | Not recorded; proposed target is pinned above |
| Conditions, findings and dispositions | Not assessed by a human |
| GitHub review permalink | Not provided |
| Authorization to begin dependent implementation | Not granted |

Every item below is pending human assessment:

- [ ] **B1 Authentication/session regression:** assess inherited A1/A2 controls and
  new revocation paths. Verify current-password reauthentication on every admin
  mutation, current active-session checks and generic recovery failures. Password
  proof must never be represented as MFA assurance.
- [ ] **B2 CSRF and API boundaries:** test all admin mutation routes with absent,
  forged and cross-user CSRF/foreign Origin, anonymous/ordinary accounts, unknown
  fields and forged role/company headers. Review no-store on reset-token responses.
- [ ] **B3 Bootstrap/Super Admin:** inspect false-by-default capability migration,
  one-time hidden-prompt provisioning of two distinct unused accounts, atomicity,
  duplicate/concurrent/repeated denial including disabled admins. Verify no public
  grant API, default credentials or implicit company/financial authority.
- [ ] **B4 Account lifecycle:** reproduce inactive registration until independent
  activation, requester AND target self-approval denial, live actor/requester grant
  checks, expired/duplicate/concurrent approval denial, deactivation and approved
  unlock. Verify reactivation invalidates old credentials and preserves the admin pair.
- [ ] **B5 Token recovery:** inspect 256-bit random token generation, hash-only DB
  storage, 15-minute expiry, one-time delivery, replacement and atomic concurrent
  redemption. Test inactive/expired/used tokens, password-change/operator-reset
  invalidation, session revocation and no automatic login. Check UI clears secrets
  and no token appears in URLs, localStorage, logs or retained evidence.
- [ ] **B6 Recovery operations:** independently exercise subject-identity verification,
  private handoff, lost token/response, mistaken recipient and compromise handling
  with synthetic data. Verify approver cannot substitute their own identity or
  approve their own reset. Delivery policy is manual, not automated or approved yet.
- [ ] **B7 Administrator abuse/availability:** inspect current-password/name/global/
  recovery limits, company-denied technical admins and live authorization under
  concurrent transitions. Assess fixed two-admin provisioning, lockout/recovery
  dead ends, total-admin loss and privileged operator bypass/custody.
- [ ] **B8 Audit and migration integrity:** inspect actor/subject/change/request UUID
  linkage, denied self-approval, immutable auth events and absence of secrets.
  Verify existing 0002 identities/sessions/audit gain no admin rights, clean repeat/
  drift/rollback works and new security history/grants prevent destructive rollback.
  Account-change records are retained; DB-owner tamper resistance is not certified.
- [ ] **B9 Company-access isolation:** verify capability authorizes identity operations
  only, no company memberships/scoped grants/business routes were added, and the
  P1-02 plan requires explicit company authorization. Defer actual tenant/RLS and
  Company/HO/Branch/Client/Contract tests to P1-02/P1-03; do not certify them here.

Evidence pointers (reported checks; human assessment still pending):

- [Follow-up report](P1-01-account-controls.md), [ADR-012](../docs/adr/ADR-012-account-controls.md),
  [operations](../docs/OPERATIONS.md#controlled-account-administration-p1-01).
- Pinned PR files: app/identity/{administration,models,service,routes,cli}.py,
  migration 0003_account_controls; RecoveryForm and existing AuthPanel.
- test_account_controls.py covers concurrent bootstrap/approval/redemption,
  self-approval, revoked actors, lifecycle/recovery and migration preservation;
  test_identity.py and test_identity_security.py remain regression evidence.
- Reported 92 backend/13 frontend tests; [head push CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41765505644)
  and [head PR CI](https://github.com/jpdoestech/manpower-erp/actions/runs/41765508990)
  have six successful checks in the prerequisite audit. Reconfirm at review time.

## Outstanding risks and required human dispositions

All dispositions/owners/dates below are **not yet assigned or accepted**. The
reviewer must classify severity, state development conditions and identify the
production blockers explicitly; listing a risk does not accept it.

| Risk | Known limit / human review needed |
|---|---|
| R1 MFA and step-up | MFA is a plan only; password reauthentication is not MFA. Decide development restrictions and required enrollment/challenge/recovery/step-up enforcement before privileged production use. |
| R2 Recovery identity and delivery | No approved automated verified channel or email integration. Define identity proof, private handoff, sender/recipient checks, lost-response/reissue and suspected compromise procedure; approve and exercise the runbook. |
| R3 Super Admin and operator custody | Bootstrap creates a fixed pair, no promotion API; total loss/disablement lacks a reviewed recovery process. Privileged CLI/DB owners can bypass application approval. Define independent operator custody, monitoring and exceptional recovery without self-approval. |
| R4 Production configuration | Only development Compose owner credentials/runtime demonstrated. Review TLS/proxy termination, exact Origin, Secure cookies, secret custody/rotation, least-privilege runtime versus migrator, network exposure, API docs and backup/restore/access controls. No production configuration is accepted here. |
| R5 Abuse and session policy | Fixed 5/name/15-minute, 60 global/minute and 5 recovery/15-minute limits can affect availability; global throttling is not edge DoS protection. Assess enumeration/timing, hash-cost calibration, password blocklist, idle/absolute session policy and monitoring. |
| R6 Audit custody and retention | Auth-event DML trigger is not protection against privileged DDL. Define access, off-host retention/monitoring, tamper detection, session/throttle cleanup and DPO-approved retention; do not erase history to bypass downgrade guards. |
| R7 Future company isolation | No organizational records or scoped RBAC/RLS are implemented. Authentication/technical admin must not imply future company access. P1-02 needs real cross-company and runtime-role/RLS proof before its own acceptance. |
| R8 Deployment/integration | PRs remain stacked and unmerged. Verify accepted SHA ancestry and final integration checks; define reviewed forward-fix/rollback boundaries without deleting security history. Acceptance is not deployment or merge authorization. |

## Recording a future actual review

Fill the appropriate PR's review record only from the human review. For each finding
record: checklist ID/risk ID, severity, evidence, decision rationale, required
condition, accountable owner, due date/milestone and verified resolution/reference.
For justified N/A, explain why the requirement is absent from that pinned PR and
where it is assessed. Do not copy a decision from one PR onto the other.

The decision must identify the exact reviewed commit, reviewer identity and
qualification/independence, review date/time, decision, conditions and GitHub review
permalink. If supplied outside GitHub, preserve the actual source and obtain the
reviewer's GitHub reference; do not fabricate a review URL or post as the reviewer.
No signatures, acceptance dates, approved conditions or reviewer identities have
been entered by the implementation agent.

Current gate: **PENDING HUMAN REVIEW for both PRs**. P1-02 remains planning only in
[its task plan](P1-02.md) and [draft PR #4](https://github.com/jpdoestech/manpower-erp/pull/4).
No automatic merge, P1-01 DONE, organization implementation or production release.
