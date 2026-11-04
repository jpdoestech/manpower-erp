# Product Blueprint

## Scope and users
Web-first ERP for several independent Philippine legal companies. Each company can contain head offices, branches, clients, service contracts, deployments/sites and employees allocated to client projects. A client legal entity can be reused across several contracts, sites, branches where approved.

## Primary business capabilities
1. Organization registry and per-company tax/registration profile.
2. Role assignments scoped by company/head office/branch/client/contract.
3. Client Billing Studio: entry catalogue, custom fields, formulas, fee eligibility, fixed fees, rate tables, approval and versioning.
4. Payroll import (or future HRIS integration), employee/client cost allocation, disbursement monitoring.
5. Billing draft -> variance review -> approval -> invoice -> GL/AR -> collection -> bank reconciliation.
6. A/R monitoring: Disbursement report (Description, Date Disbursed, Total Amount Released, Date Billing Received); configurable detailed billing; aging with Current, 1-30, 31-60, 61-90, 91-120, 120+; company/branch/client subtotals and grand total; separate detail/summary switches.
7. AP, Cash/Bank, GL, Trial Balance, Financial Statements, period close, tax reporting and document archive.

## Key domain entities
LegalCompany, Establishment/Branch, HeadOffice, ClientLegalEntity, ServiceContract, ServiceSite, EmployeeAssignment, PayrollBatch, CostAllocation, Disbursement, BillingDefinition, BillingTemplate, BillingTemplateVersion, BillingFormulaVersion, BillingDocument, BillingLine, Invoice, InvoiceLine, GLAccount, Journal, JournalLine, Payment, PaymentAllocation, TaxRuleVersion, ApprovalRequest, AuditEvent.

## Billing examples to prove flexibility
A: administrative fee 8% on basic+overtime+holiday only; B: flat fee per employee; C: fixed monthly charge; D: mixture of per-hour services + reimbursable charges. Each configuration must specify whether an item is billed, fee-eligible, taxable according to approved rule, GL-mapped, data-source controlled, editable and effective-dated.

## UX expectations
Professional compact ERP UI, dense accessible tables, keyboard input, Excel copy/paste, saved filters, clear approval states, responsive display, 32–36px common desktop control height as design guidance, not a universal constraint. No excessive giant controls.

## Out-of-scope until scheduled
Full HRIS, attendance capture hardware, payroll engine, e-filing transmission, automated regulatory interpretations, AI autonomous financial posting. Integrations must have clean contracts for later adoption.
