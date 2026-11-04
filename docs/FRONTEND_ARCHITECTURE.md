# Frontend architecture — UI-001

React 19 / TypeScript / Vite remain the runtime stack. No runtime dependency is
added. ADR-016 evaluates Tailwind and accessible headless libraries; native HTML
and CSS fit this slice. Pinned Playwright/axe are development-only regression tools.

## Ownership

- App.tsx: existing bootstrap metadata check, resilient light/dark preference,
  anonymous presentation and composition of authenticated content.
- AuthPanel.tsx: validated account in React memory, existing /me, login/logout,
  password requests, CSRF headers, generic errors and secret clearing. Optional
  render boundaries receive account presentation/actions; no new auth provider.
- RecoveryForm.tsx: existing single-use administrator-token recovery unchanged.
- shell/navigation.ts: static module IDs/labels/grouping/descriptions, no records.
- shell/ApplicationShell.tsx: local preview page selection, responsive navigation,
  context placeholder, breadcrumbs, module-only search, account/notification UI.
- ui/components.tsx: native semantic controls and shared feedback patterns.
- ui/Icon.tsx: local decorative SVG paths, no icon/network dependency.
- ui/Reference.tsx: explicit no-save interactive component reference.
- style.css: shared light/dark tokens, responsive density and component classes.

Page selection is ephemeral React state; no resource routing/deep-link framework
is introduced for placeholders. Browser reload returns to the overview. Add real
routes in the first approved operational module, with server authorization and
not-found behavior. Do not turn a module label into a resource permission.

## Authentication and scope boundary

Only existing validated /me/login responses render ApplicationShell. Cookie
transport remains same-origin; CSRF on logout/password change is unchanged.
Failed logout remains visibly reported on the active shell page; successful
logout or password change removes the shell. Password change is optional on
My account, not an initial forced workflow. Recovery remains outside the shell.
Only erp-theme is persisted in localStorage; no passwords, tokens, identities,
company grants or session data are stored there. Storage failure is nonfatal.

No authorized organization API exists: context selection is disabled, no synthetic
companies are shown, and login grants no business permissions. Administration is
unavailable because /me supplies no server capability. Its label is a disabled
catalogue destination, not a management UI. Future backend scopes/capabilities
must be rechecked server-side on every protected operation. No role is inferred
from a username. P1-01 acceptance and CR-002B acceptance remain pending.

## Local development and checks

Existing setup-local.bat/start-local.bat/test-local.bat continue to use SQLite.
No backend/schema/env change. Theme and shell work independently of DB dialect.
The current local API/Vite process is not stopped/reset by UI tests.

From frontend, Node 24:

```sh
npm ci
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:browser
npm audit --audit-level=low
```

Browser tests own Vite on 127.0.0.1:5174, refuse reuse, and mock only /api test
responses. They never create a developer account or touch its database. Vitest
includes src/**/*.test.{ts,tsx}; browser/*.spec.ts is a separate Playwright suite.
Browser output/screenshots are ignored in frontend/test-results; CI uploads them
as ui-browser-evidence for seven days. Real Windows fresh flow and PG/Compose
regressions remain required existing CI gates. No production bundling of fixtures.
