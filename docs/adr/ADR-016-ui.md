# ADR-016 — Compact ERP shell and native UI primitives

Date: 2026-11-04. Status: adopted for UI-001 implementation; review pending.
Authority: explicit UI-001 request. No authentication or production acceptance.

## Context and alternatives

Existing React/TypeScript/Vite uses plain CSS and no UI/router dependencies.
Tailwind provides utility composition and Vite integration but adds build tooling
and a second styling vocabulary; shared CSS tokens/classes meet this slice.
React Aria/headless primitives provide richer focus/interaction behavior but add
dependencies and composition contracts. Prefer native button/input/select/date,
datalist/details/dialog semantics here; implement only the small tested keyboard
tab pattern. Native modal dialog supplies browser focus containment and Escape.

Decision: retain current dependencies and use semantic HTML + CSS tokens. Revisit
headless primitives when real scoped asynchronous selection, complex grids or
menus exceed native behavior. No custom ARIA menu/combobox/grid is simulated.

## Boundaries

AuthPanel owns the existing validated account, cookie transport, CSRF and secret
clearing. An optional authenticated render boundary composes the shell without
persisting session data. Only theme is stored locally; unavailable storage is safe.
No routing dependency: small local page selection represents non-resource previews.
Module search filters a static navigation catalogue, never company/employee data.
Context selection is disabled until authorized scope APIs exist. System admin is
unavailable until server capability evidence exists; username is not authority.
Future pages require backend permission checks independently of shell visibility.

## Consequences and verification

Smaller dependency surface, compact consistent UI and no external font requests.
Native date/datalist appearance varies by browser. Dialog tests need a small jsdom
platform shim; real browser focus/layout verification is distinct from DOM tests.
No claim of full WCAG certification or screen-reader coverage. Automated tests
cover keyboard/state/auth regressions; browser checks cover responsive themes.

References: https://tailwindcss.com/docs/installation/using-vite,
https://react-spectrum.adobe.com/react-aria/Dialog.html,
https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog.

## Device and accessibility regression tools

The user's follow-up makes phones, tablets, laptops and large displays first-class
acceptance targets. DOM/jsdom tests cannot measure layout or native modal focus.
Add pinned dev-only @playwright/test 1.64.1 and @axe-core/playwright 4.14.0 for real
browser viewport/keyboard and automated accessibility checks. No runtime UI library
is added. Chromium emulation is repeatable CI evidence, not physical iOS/Android
or screen-reader certification. Sources: https://playwright.dev/docs/emulation and
https://playwright.dev/docs/accessibility-testing. Browser API responses use clearly
synthetic test fixtures only; there is no runtime mock-session path.
