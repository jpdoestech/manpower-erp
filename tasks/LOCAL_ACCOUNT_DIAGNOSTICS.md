# Local account provisioning diagnostics

Plan before code — 2026-11-04. User reports setup reached the optional account
prompt and failed with a generic identity error. The supplied password meets the
15-character minimum; do not repeat/use it in tests or create/change their account.
Read-only inspection: revision 0004, admin-name count 0, FK violations 0. Original
cause cannot be recovered from the old generic message. Confirmed defect: CLI
collapses mismatch/validation/hidden-input/EOF/database errors into one message.

Branch fix/local-account-error-messages from verified 17e5bfb / PR #7; no merges.
Scope: backend/app/identity/cli.py, focused CLI error tests, SQLite 15-character
provisioning regression, local Windows docs and STATUS. No policy, hashes, API,
authorization, database/schema or account modifications. Keep fail-closed input.

Acceptance: mismatch/short password/username errors explain the correction; hidden
input unavailable/EOF explicitly ask for an interactive terminal; DB failures stay
sanitized. Unrecognized ValueError and SQL exception content never leak values.
Engine disposal and existing rollback tests retained. Fresh disposable SQLite
CLI creation accepts a synthetic 15-character password with mocked hidden input;
correct confirmation creates one ordinary hashed account with no admin grant.
Run backend unit/SQLite, formatting/lint/types, and existing hosted PostgreSQL,
Windows, frontend and Docker gates; report original cause as unconfirmed.

Local evidence: from backend, `uv run --locked pytest -q -m "not integration"`
reports 110 passed / 42 deselected, 24.55s. Includes eight sanitized CLI error
cases, successful exact-15-character ordinary SQLite CLI provisioning and existing
confirmation/rollback/security cases. Hidden prompts are mocked; actual user's
keystrokes cannot be reconstructed. No real password used or local account changed.
`uv run --locked ruff format --config pyproject.toml --check . ../scripts`,
`uv run --locked ruff check --config pyproject.toml . ../scripts` and
`uv run --locked mypy app tests alembic ../scripts` pass (34 files).
Hosted PostgreSQL/Windows/frontend/Docker regression evidence pending after push.
`uv run --locked python -m unittest discover -s ../scripts/tests -p 'test_*launchers.py' -v`:
16 passed / 1 opt-in native smoke skipped (17 discovered), 11.986s. No new local
interactive TTY/browser, PostgreSQL or Docker execution is claimed.
