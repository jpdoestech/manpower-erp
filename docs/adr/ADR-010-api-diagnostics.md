# ADR-010 — Health, errors and observability

Date: 2026-11-04. Status: ADOPTED for infrastructure; monitoring operations pending.

Alternatives: raw framework tracebacks/access logs, or a small explicit diagnostic
contract. Choose process-only GET /api/health/live and GET /api/health/ready with
a bounded PostgreSQL SELECT 1. DB failure must return generic 503 while live stays
200. Readiness checks connectivity, not legal compliance or future schema/business
readiness. No DB credentials, versions, hostnames or exception text in responses.

API failures use `{error: {code, message, request_id}}`; keep HTTP status and
protocol headers. Validation errors must not echo input. Unexpected failures get
a generic 500. Correlation is a canonical UUID: accept a single valid supplied
X-Request-ID or generate one. It is untrusted diagnostic metadata, never identity
or tenant authority. Echo it in all responses and safe errors; isolate per request.

Application JSON logs whitelist UTC timestamp, severity, fixed event, request ID,
method, route template, status, duration_ms and exception type. No bodies, headers,
raw paths/query strings, DSNs, SQL parameters or exception messages/tracebacks.
Disable raw Uvicorn access logging in shipped entrypoints. SQLAlchemy echo stays
off and parameters hidden. Application logs are diagnostics, not financial audit
records; durable approval/posting audit storage belongs to later domain modules.

Basic metrics design: aggregate request_completed logs into request/error counts
and latency distributions by bounded method/route-template/status labels. Readiness
probe history supplies availability. Never label metrics by user/company/request
ID, arbitrary URL or error text. No public metrics endpoint, collector or alerting
service is needed for this slice. Future monitoring must define retention, sampling,
access, redaction, health scrape limits, thresholds and operational ownership with
the DPO/release/security owners before production. Do not log financial payloads
for debugging. Background/streaming jobs need their own scoped diagnostics later.

Consequences: safe actionable status/correlation without sensitive stack traces;
restricted debugging may require synthetic reproduction. Evidence: observability
and API tests, Compose health/down/recovery smoke and `docs/OPERATIONS.md`.
