# Financial Invariants and Posting Rules

## Unbreakable invariants
1. Every posted journal has total debits equal total credits in the company's base currency, at approved rounding precision.
2. Every journal belongs to exactly one legal company and an open/eligible period.
3. Posted journal lines, invoice totals and document snapshots are immutable; use authorized reversal/adjustment documents.
4. Invoice issuance is idempotent and document numbering cannot collide per approved numbering scope.
5. No invoice can post without approved template, valid tax mapping, GL mapping and authorization.
6. AR open balance = invoice/debit charges minus allocated payments/credits; withholding certificates are tracked as distinct settlement components.
7. Cash receipts are not automatically recognized as revenue if revenue was already recognized at invoicing.
8. Payroll disbursement, accrued payroll expense, reimbursable cost and billing amounts are separate accounting concepts.
9. Financial statements and historical aging are reproducible as of cutoff dates.
10. Intercompany flows use explicit intercompany accounts and controlled elimination in consolidation.

## State machines
Billing: draft -> submitted -> reviewed -> approved -> invoiced; rejects/voids have reasoned exceptions.
Invoice: prepared -> issued -> posted -> partially_paid/paid; corrections via credit/debit note or reversal under authorized policy.
Journal: draft -> submitted -> approved -> posted -> reversed (new compensating journal).
Payment: recorded -> verified -> posted -> allocated/reconciled.

## Required reconciliation tests
Invoice lines vs header vs tax components; AR subledger vs GL control account; receipt allocation vs bank activity; payroll liability vs disbursements; aging bucket totals vs total open AR; period-end trial balance.

## Tax caution
A transaction's tax status is not determined solely by whether the company is VAT or Non-VAT. Contract terms and legal applicability must be independently reviewed. Never hardcode exemptions or withholding rates without approved rules and source references.
