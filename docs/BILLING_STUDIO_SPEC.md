# Client Billing Studio — Functional and Technical Specification

## Objective
Authorized accountants configure billing classifications at any time while protecting historical documents and avoiding schema churn.

## Data structure
BillingEntryDefinition(id, stable_code, display_name, data_type, category, source_type, default_gl_mapping, status);
BillingTemplate(id, company_id, contract_id, status);
BillingTemplateVersion(id, template_id, version, effective_from, effective_to, approval_id, published_at, immutable_payload_hash);
BillingTemplateItem(id, version_id, definition_id, display_order, fee_eligible, editable_roles, taxable_rule_id, required, default_value, formula_version_id);
BillingDocument(id, company_id, contract_id, template_version_id, cutoff_start/end, status, version);
BillingLine(id, billing_document_id, entry_definition_id, source_reference, amount, tax_rule_snapshot, gl_mapping_snapshot, fee_eligible_snapshot).

## Configuration lifecycle
DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED -> PUBLISHED -> SUPERSEDED. Reject -> DRAFT with reasons, never repurpose published versions. No backdated changes affecting posted invoices; corrections via adjustment documents.

## Engine pipeline
Select contract+service period -> resolve active approved template -> collect signed payroll/cost sources -> compute formula DAG -> apply configured fees and approved tax rules -> validate and compare disbursements -> approval -> issue invoice -> post GL/AR once.

## Formula DSL
Allow numeric Decimal literals, named fields, + - * /, IF, MIN, MAX, SUM, ROUND, COALESCE and carefully governed lookup functions. Type checks, null semantics, divide-by-zero policy, explicit rounding modes, dependency cycle rejection, execution limits, test fixtures and explanation trace. No arbitrary code or remote lookups inside formulas.

## Must-pass scenarios
- One client adds new `TRANSPORT_ALLOWANCE` entry via proposal/approval, without migration.
- Client A includes Basic/OT/Holiday in 8% fee; Client B excludes them and uses a fixed ₱25,000 fee.
- Old invoices retain original values/formulas after configuration v2 publication.
- Invalid formula, cyclic dependencies, duplicate codes, missing GL mapping and unauthorized change are rejected.
- Independent contract/site configurations under same client work concurrently.
- Difference between calculated costs and disbursement is flagged and routed to authorized review.

## Extensibility
User-defined display columns are configurable views of typed values. Search/export must use approved field metadata. Separate accounting-affecting lines from presentation-only attributes.
