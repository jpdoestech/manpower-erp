# Change Request and Impact Process

When the user changes a requirement at any time:
1. Record change ID, original behavior, requested behavior, reason, urgency, affected company/client and effective date.
2. Classify as UI-only, billing classification, formula/fee, tax, accounting posting, permission, structural schema or integration.
3. Trace impact: database/migration; API; existing documents; GL & AR; roles/approval; imports; reports; tests; operational rollout.
4. State backward-compatibility and historical integrity. Published config gets new version. Posted financial records require correction flow.
5. Update product spec, ADR if architectural, roadmap and acceptance cases BEFORE implementation.
6. Implement safely behind feature/version gating; test old+new scenarios; obtain relevant approval.
7. Update status and document what changed.

## Example
Request: Client X wants a new `SIL_PROVISION` billing entry effective next cutoff. Propose entry -> validate source/type/account/fee eligibility -> approved template vN+1 -> simulate against sample payroll -> publish effective date -> only new documents adopt version -> check historical vN invoice unchanged.

## Never
Do not modify production data manually, apply database changes without migrations, treat UI hiding as security, rewrite posted invoices, or guess tax applicability.
