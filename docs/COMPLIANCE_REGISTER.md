# Philippine Compliance Decision Register

This file is a product research and review checklist, NOT an assertion that regulatory settings are already approved. The legal/CPA reviewer must confirm effective law and entity-specific applicability before production issuance.

| Area | Required implementation | Approval / evidence |
|---|---|---|
| Company tax profile | VAT, Non-VAT, legally exempt, effective dates, proof | CPA and tax owner |
| CAS/CBA | Business/RDO registration and applicable acknowledgement before use | BIR compliance reviewer |
| Invoices | Required fields, numbering, issuance timing, audit, credit/debit notes | CPA / BIR reviewer |
| E-invoicing | Structured invoice data, regulatory applicability, current deadlines and technical specs | CPA + technical tax reviewer |
| CWT/EWT | Configurable, transaction-scoped rates/bases and BIR certificates | CPA |
| Cooperatives | CDA certificate and specific BIR exemption basis / limits | CPA/legal |
| DOLE contractor registration | Registration IDs, contract compliance data, expiry alerts | Labor compliance |
| Payroll statutes | SSS/PhilHealth/Pag-IBIG and other applicable payables | Payroll/legal |
| Data privacy | Retention, RBAC, security controls, privacy review | DPO |

## Initial primary sources (re-verify before production)
- BIR RMC 5-2021 CAS/CBA registration: https://bir-cdn.bir.gov.ph/local/pdf/RMC%20No.%205-2021%20%281%29.pdf
- BIR RMC 65-2025 digest (acknowledgement context): https://bir-cdn.bir.gov.ph/BIR/pdf/RMC%20No.%2065-2025%20Digest.pdf
- BIR RR 11-2025 e-invoice: https://bir-cdn.bir.gov.ph/BIR/pdf/RR%20No.%2011-2025.pdf
- BIR RR 26-2025 e-invoice transitional amendment: https://bir-cdn.bir.gov.ph/BIR/pdf/RR%20No.%2026-2025.pdf
- DOLE contractor registration: https://ble.dole.gov.ph/registration-of-job-contractor/

## Change procedure
1. Register regulation title, publication date, effective date, applicable taxpayers, confidence, URL and reviewer.
2. Explain affected data structures, formulas, reports, generated documents and migration needs.
3. Draft new dated tax-rule version with fixtures; never silently alter historical computation.
4. Obtain approval, then deploy with audit and rollback strategy.
5. Keep uncertain items BLOCKED, not marked compliant.
