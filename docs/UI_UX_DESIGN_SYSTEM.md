# ERP UI design system — UI-001

The workspace serves phones, tablets, laptops and large desktop displays. Compact
desktop density and comfortable touch input share one component set. It is a web
application shell, not an installed/offline PWA or a financial workflow.

## Visual language

Restrained operational workspace: navy navigation (#15283F), blue actions
(#2669A9), light gray separators (#E7ECF1), white surfaces and gold (#C6A15A)
orientation accents. All colors live in custom properties in src/style.css;
dark mode overrides semantic tokens, including action text contrast. Gold is
decorative, never the only indication of a status. Status text accompanies color.
Local Segoe UI / Helvetica Neue typography avoids external font requests.
Desktop text is compact; page headings 28px, section headings 15px, common
controls 34–38px. Spacing follows 4/8/12/16/20/24/32px increments.

## Responsive behavior

| Size / input | Layout |
|---|---|
| <=600px phones | Sticky header, modal module drawer, fixed four-action bottom bar; no permanent sidebar; stacked cards and readable module list |
| 601–850px tablet / landscape | Compact icon rail and modal full navigation; single-column overview |
| 851–1150px small laptop / wide tablet | Labeled sidebar, condensed search, single-column overview |
| >1150px laptop / desktop | Collapsible sidebar, full header search and two-column overview |
| Large desktop | Content grows to 1600px within the workspace; forms remain bounded |
| Coarse pointer | 44px minimum buttons/inputs; touch input text 16px |

Phone controls use 44px targets, safe-area insets and dynamic viewport heights.
No viewport zoom restrictions. Wide generic tables scroll inside a labeled,
keyboard-focusable region; the module directory uses a readable list on phones.
No page-level horizontal scrolling is expected. Native date/datalist appearance
varies by browser. Notifications/search/navigation use scrollable native modals
for short or landscape screens. Reduced-motion users get no skeleton animation.

## Reusable components

Import from frontend/src/ui/components.tsx (icons from ui/Icon.tsx).

| Component | Contract |
|---|---|
| Button | primary, secondary, quiet, danger; explicit button default; native disabled |
| Field | Native input, linked label/help/error, aria-invalid; type=date for dates |
| Select | Labeled native select |
| SearchableDropdown | Native input + datalist; suggestions are not authorization or strict enum validation |
| DataTable | Caption, column headers, stable row IDs; read-only table, no fabricated records |
| Dialog | showModal/close, native inertness/focus containment; Escape closes before unmount; trigger focus restored |
| ConfirmDialog | Explicit cancel/confirm; cancellation never invokes confirm; callers own authorization/async state |
| Tabs | Roving focus, arrows/Home/End, linked panels |
| Badge | Text plus semantic neutral/success/warning/danger tone |
| StatePanel | Empty, safe error and unauthorized patterns with optional action |
| Toast | Polite persistent announcement and dismiss button; no timed disappearance |
| Skeleton | Named loading status, decorative bars, reduced-motion support |

Use the signed-in **Design system** page for interactive examples. It is explicitly
a UI reference; validation, status and confirmation examples save no records and
make no API calls. Real forms must validate server-side and enforce current scopes.
Native HTML validation supplements the server; no client control grants authority.

## Accessibility and evidence

Skip link, semantic landmarks/breadcrumbs, visible focus, labels and live regions
are required. Native details account menu uses normal Tab/Enter semantics, not a
partially implemented ARIA menu. Focus moves to the workspace after local page
navigation without scrolling a heading behind the sticky header.
Playwright/axe checks light/dark login, shell, account and reference, native dialog
Escape/focus, keyboard tabs, viewport overflow and phone target height. Tests use
synthetic API fixtures; real cookie/CSRF/database behavior is covered separately
by backend and Windows native smoke. See tasks/UI-001.md for exact results.
Automated accessibility checks do not certify WCAG conformance; physical device,
screen-reader, Safari/Firefox and usability acceptance remain human follow-up.
