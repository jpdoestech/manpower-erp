# RBAC, Scope and Separation of Duties

## Access layers
Identity -> membership(s) in legal companies -> role grants scoped to company/head office/branch/client/contract -> resource action -> workflow constraints. Explicit deny supersedes grant. Default deny.

## Personas
Platform Super Admin (technical access, no assumed accounting approvals); Company Admin; Head Office Admin; HO Accountant; Branch Admin; Branch Accounting Maker; Branch Accounting Approver; Collections Maker; Viewer; Commenter; auditor read-only.

## Representative permission keys
org.read, org.manage; client.read, client.manage; contract.manage; billing_definition.propose, billing_definition.approve, billing_definition.publish; billing_template.propose, billing_template.approve; billing_draft.create, billing_draft.edit, billing_draft.submit, billing.approve; invoice.issue; journal.propose, journal.approve, journal.post, journal.reverse; payment.record, payment.approve, payment.allocate; tax_rule.propose, tax_rule.approve; reports.read, reports.export; user.grant_role.

## Workflow enforcement
Creator != approver on same transaction; requester != publisher when configuration affects accounting. Re-evaluate role and scope at transition time; do not rely on captured client UI state. Approval delegation needs validity period and audit. Self-service role escalation prohibited. Separate privileged break-glass procedures with monitoring and expiration.

## Tests required for every module
- Company A user gets 403/404 as appropriate on Company B API, report and file.
- Branch A user cannot access Branch B unless explicitly granted.
- User with Maker+Approver cannot approve self-authored document.
- Expired/revoked grants are immediately ineffective.
- Horizontal IDOR, list filtering, exports and async job scope checks.
- Audit records persist on reject/approve/reverse/publish.
