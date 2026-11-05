# Owner and independent security review — local foundation RC

2026-11-05, Asia/Manila. **All decisions below remain unrecorded/pending.**
This checklist prepares review; checking it is the human's task, not the agent's.
Evidence/order: [integration report](../tasks/INTEGRATION_READINESS.md).
Authoritative separate security records: [P1-01 acceptance](../tasks/SECURITY_ACCEPTANCE_P1-01.md).

## Owner: integration preparation

- [ ] Identify the exact RC SHA and review its complete diff against current main.
  Confirm P0/P1 identity, SQLite tools and UI only; proposed organization/Supabase
  documents grant no runtime permission and contain no implemented business schema.
- [ ] Confirm all eleven pinned heads in the report and any newer commits. Re-fetch
  or compare authoritative remote refs; resolve Git transport failures before any
  local merge that depends on an unverified remote change.
- [ ] Select history-preserving integration order #1 -> #2 -> #3 -> #4 -> #5 ->
  #6 -> #7 -> #8 -> #9 -> #10 -> #11. Resolve each PR's required conditions;
  #4/#11 are documentation drafts, not permission to implement P1-02/CR-002C.
- [ ] Keep original head SHAs in history (merge commits/fast-forward policy).
  If choosing squash/rebase, first rebase/re-review all descendants and regenerate
  ancestry/CI/security evidence; do not reuse the original-stack audit unchanged.
- [ ] Retarget each next PR to main only after its predecessor is actually accepted
  and integrated. Inspect the new diff and run fresh checks against that merge base.
  Do not merge later PRs into predecessor feature branches as an unreviewed shortcut.
- [ ] Verify new RC checks: backend local/PG/auth, migration CLI, full fresh Windows
  nine-tool flow, frontend/components/browser accessibility, Compose health/auth/
  failure recovery/persistence, lockfiles, lint/types/build and dependency audits.
  A skipped/unavailable local gate requires actual passing hosted evidence.
- [ ] Review CR-002A/B phase acceptance, including current-revision-only unencrypted
  local recovery, trusted filesystem custody, old-launcher handling and restored
  credential revocation. Do not infer phase acceptance from previous explicit
  implementation authorization or passing tests.
- [ ] Review UI-001 phone/tablet/laptop/desktop usability and auth presentation.
  Chromium emulation/axe is not physical-device/Safari/Firefox/screen-reader signoff.
  Record relevant conditions without inventing completed UI tests.
- [ ] Keep the RC draft/held until required human decisions and conditions are
  recorded. Use it for cumulative validation; it is not an alternate route around
  individual security acceptance. Reconcile its documentation diff after original
  PR integration; avoid a second independent feature-stack import.
- [ ] Authorize any actual merge separately. No production deployment, credentials,
  data modification or fiscal document generation follows from this checklist.

## Security reviewer: separate PR #2 decision

Review target **dc7fca3c5b747a0ec245dc02973b07bf087277e5**, inherited P0-02.
All A1–A9 remain pending in the authoritative record. Assess with synthetic users:

- [ ] A1: Argon2id parameters, passphrase validation, enumeration/timing behavior.
- [ ] A2: hashed random sessions, expiry/rotation/revocation, cookie/no-store policy.
- [ ] A3: CSRF/Origin, missing-Origin native-client allowance and browser behavior.
- [ ] A4: hidden-prompt provisioning, duplicate/default-credential denial, custody.
- [ ] A5: CLI recovery identity proof and revocation; token recovery is absent here.
- [ ] A6: no self-service role/company grants; privileged operator trust boundary.
- [ ] A7: safe auth audit/diagnostics and DML guard versus privileged-DDL limits.
- [ ] A8: cross-user/forged-authority denial; no claim of future tenant/RLS proof.
- [ ] A9: durable/concurrent limits, configuration, migration/downgrade safety.

## Security reviewer: separate PR #3 decision

Review target **37dbd7f2280e6b89919f7bf3d5e69954c67c1968**, including #2 behavior.
All B1–B9 remain pending; a decision on #2 does not automatically decide #3.

- [ ] B1: inherited auth/session plus reauthentication and revocation regressions.
- [ ] B2: admin/recovery CSRF/Origin/validation and no-store secret responses.
- [ ] B3: one-time two-admin bootstrap, concurrent/repeated denial and no grants.
- [ ] B4: inactive registration, independent activation/deactivation/unlock,
  requester/target separation, current actor checks and concurrent replay denial.
- [ ] B5: hash-only single-use expiring recovery tokens, race/invalidation/secret clearing.
- [ ] B6: independently exercised identity verification/private handoff and loss/
  compromise/reissue procedures; no self-reset approval or substituted recipient.
- [ ] B7: admin abuse/availability, lockouts, total-admin loss and operator custody.
- [ ] B8: actor/subject/change audit, existing user/UUID preservation, downgrade guards.
- [ ] B9: technical admin is identity-only; future company isolation stays unproven.

## Security dispositions and recording rules

- [ ] Disposition R1–R8 separately: MFA/step-up; recovery proof/delivery; Super Admin/
  DB-operator custody and total loss; production TLS/origins/secrets/roles; abuse/
  session policy; audit/retention/tamper limits; future scopes/RLS; integration/
  rollback. State which conditions block development and which block production.
- [ ] Evaluate inherited security changes after the pinned PRs: #6 SQLite migration/
  serialized transactions/guards; #8 sanitized operator diagnostics; #9 local
  restore/revocation and filesystem custody; #10 auth render/composition/storage.
  Identify any RC-specific findings/conditions; do not certify the cumulative
  security surface solely from the earlier PR snapshots.
- [ ] Record PASS/FAIL/justified N/A for every applicable A/B item with evidence.
  For each finding: severity, affected SHA, required change, accountable owner,
  deadline/milestone, verified resolution/reference; leave unknown values unset.
- [ ] For each PR separately record reviewer identity, qualification/independence,
  date/timezone, exact reviewed SHA, decision, conditions and GitHub review permalink.
  Allowed outcomes: ACCEPTED FOR DEVELOPMENT, CHANGES REQUIRED, REJECTED or PENDING
  HUMAN REVIEW. Conditional approval with unmet prerequisite conditions does not
  open the gate. Preserve the actual source of any externally supplied decision.
- [ ] Do not mark P1-01 DONE until both acceptances and conditions are verified by
  the maintainer. No production/security/CPA approval is implied by test success.

## Exact authorization needed before CR-002C implementation

- [ ] Satisfy CR-002C G1: real B/inherited phase acceptance at exact accepted SHA,
  with reviewer/date/reference and verified conditions.
- [ ] Satisfy G2: both separate P1-01 security decisions and RC-relevant conditions.
- [ ] Verify G3/G4: intended accepted integration ancestry and relevant UI findings;
  preserve pending UI review without inventing an extra security gate.
- [ ] Approve proposed ADR-017/C-D1–7: browser/server token custody and encryption
  key lifecycle, cloud login methods, JWT/JWKS policy, live session revocation,
  identity-link/external-only credential migration, admin MFA/reauth/recovery and
  same-origin hosting boundary. Unknown mechanism or owner remains pending.
- [ ] Satisfy G6/G7: explicitly authorized disposable Supabase project/configuration,
  isolated synthetic users/secrets/CI lane and dual-dialect test environment.
- [ ] Record explicit authorization to start the planned C slices after conditions
  are met. This is not permission to merge, deploy D, transfer E or start P1-02.

Current outcomes: **PENDING HUMAN REVIEW** for #2/#3 and **acceptance pending** for
CR-002B. No names, signatures, dates of approval, waived risks or decisions are
provided here. The implementation agent cannot complete those human actions.
