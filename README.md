# Manpower ERP — Codex Development Governance Pack

This is a repository-ready design and execution guide, not an implemented ERP. Copy all files to the repository root, retaining folders. Start by reading `CODEX_START_HERE.md` and assigning Codex P0-01. The operating contract is in `AGENTS.md`; the next tasks are in `tasks/ROADMAP.md`; progress lives in `tasks/STATUS.md`.

## Start sequence
1. Copy pack into new or existing ERP repository.
2. Review proposed technology ADR and company tax assumptions with relevant owners.
3. Launch Codex in repository root; use `CODEX_START_HERE.md` as first prompt.
4. Review each task's tests and changes before accepting it; Codex updates STATUS after every task.
5. For new requirements, run `docs/CHANGE_CONTROL.md` first.

## Contents
- `AGENTS.md`: permanent agent engineering contract.
- `docs/`: product, architecture, billing, finance, security, compliance, tests, change control.
- `tasks/`: staged roadmap, status handoff and decisions.
- `templates/`: task work order.
- `CODEX_START_HERE.md`: first Codex prompt.

**Important:** BIR/DOLE references are starting points for a legal/CPA review; they are not a compliance certification.
