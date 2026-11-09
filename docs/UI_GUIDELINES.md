# MeetingSpace — UI Guidelines

Every later frontend step follows these rules. They cover product feel,
design tokens, layout, state handling, feedback, forms, copy, time display,
accessibility, and UI-level security. The foundation these rules describe
(tokens, component library, API client, auth plumbing, routing) was built in
Step 12 and lives in `frontend/src/`.

## 1. Product feel

A calm, professional internal tool. Clarity over decoration: one accent
colour, no gradients, no illustrations. Only subtle `150ms` transitions
(`var(--transition-fast)` in `src/styles/tokens.css`), switched off entirely
under `prefers-reduced-motion: reduce`.

## 2. Design tokens

All colours, spacing, radius, and font sizes live as CSS variables in
`src/styles/tokens.css`. **Components read tokens only — never a raw hex
value or a magic pixel number.**

- Colour: `--color-surface`, `--color-text`, `--color-muted`,
  `--color-border`, `--color-accent` (+ `--color-accent-contrast`),
  `--color-success`, `--color-warning`, `--color-danger`. Light values in
  `:root`; dark overrides under `@media (prefers-color-scheme: dark)`. Every
  text/background pair is verified ≥ 4.5:1 contrast (see rule 9).
- Spacing: `--space-1` through `--space-7` = 4/8/12/16/24/32/48px.
- Radius: `--radius` = 8px, used everywhere (buttons, fields, dialogs, toasts).
- Font sizes: `--font-size-xs/sm/md/lg/xl` = 12/14/16/20/24px.
- Font: `--font-sans` is the system font stack — no web fonts, no FOUT/FOIT.

## 3. Layout

Top bar: app name, nav (Rooms, My bookings, Admin — Admin only if
`user.is_staff`), and a user menu (username + Log out). Content area is
centred, `max-width: var(--content-max-width)` (1120px), with
`var(--space-4)` (16px) side padding on phones.

Breakpoints: `640px` and `1024px`. Below 640px the inline nav hides and a
menu button (`aria-expanded`, `aria-label="Toggle navigation menu"`) reveals
a stacked nav panel instead. No layout may cause horizontal scrolling at a
375px viewport — use `box-sizing: border-box` everywhere (set globally in
`src/styles/global.css`) and avoid fixed widths wider than the smallest
supported viewport.

See `src/layout/Layout.tsx` for the reference implementation.

## 4. Data view states

Every view that loads data has exactly four states, and must never show a
blank page:

1. **Loading** — a `Skeleton` (`src/components/Skeleton`), shaped like the
   eventual content.
2. **Empty** — `EmptyState` (`src/components/EmptyState`): a short message
   plus the next action (e.g. "No rooms yet." + an "Add a room" button).
3. **Error** — `ErrorState` (`src/components/ErrorState`): a plain-language
   message plus a Retry button.
4. **Success** — the real content.

## 5. Feedback

- Buttons (`src/components/Button`) show a spinner and are disabled
  (`aria-busy="true"`) while their action's request is in flight.
- A successful action shows a toast (`src/components/Toast` —
  `ToastProvider` + `useToast()`), announced via `role="status"
  aria-live="polite"`.
- Destructive actions (cancel a booking, deactivate a user, remove admin
  rights) require `ConfirmDialog` (`src/components/ConfirmDialog`), whose
  message must name the specific item and explain the effect — e.g.
  `Cancel "Sprint planning"? This can't be undone.`, not just "Are you sure?".

## 6. Forms

- Every field has a **visible label** (`TextField`/`Select` render a real
  `<label>` — never placeholder-only).
- Optional help text renders under the field, linked via `aria-describedby`.
- Validation errors render next to their field (also `aria-describedby`,
  `role="alert"`) **and** as a summary banner at the top of the form for API
  errors that aren't tied to one field.
- Keep the user's typed value in the field after an error — never clear the
  form.
- On submit with invalid input, move focus to the first invalid field (see
  `LoginPage.tsx` for the reference pattern: required-field check → set field
  errors → focus the first one before ever calling the API).

## 7. Copy

Sentence case, plain words, no internal codes (`BR-4`, `409`, etc.) ever
shown to a user. All API errors are mapped through
`src/api/errors.ts::getFriendlyMessage` / `getFieldErrors` — never render
`error.messages` directly. Current mappings include:

| Raw                     | Friendly text                                               |
|-------------------------|---------------------------------------------------------------|
| `BR-4`                  | Times must be on the hour or at :15, :30 or :45.             |
| `409` / `BR-6`          | That time overlaps another booking in this room.             |
| `BR-1`/`BR-2`/`BR-3`/`BR-5`/`BR-7`/`BR-8`/`BR-9` | see `BR_CODE_MESSAGES` in `src/api/errors.ts` |
| `401`/`403`/`404`/`429` | generic fallback text, see `STATUS_FALLBACKS`                 |

Add new codes to that same table — don't invent a second mapping elsewhere.

## 8. Time

Always show times in Asia/Tokyo, 24-hour format. Add "Times in JST" once per
page (not per row) wherever times are shown. Dates render like
`Tue, 3 Nov 2026`. Use the `Intl.DateTimeFormat`/`Intl.ListFormat` APIs built
into the browser — no date library is a dependency of this project.

```ts
new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Tokyo',
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
}).format(date)

new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Tokyo',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
}).format(date)
```

## 9. Accessibility (WCAG 2.2 AA)

- Text contrast ≥ 4.5:1 — every token pair in `tokens.css` was checked with
  the WCAG relative-luminance formula before being committed, not eyeballed.
- Every interactive element has a visible focus ring
  (`:focus-visible { outline: 2px solid var(--color-focus-ring) }` in
  `global.css`) — never remove it.
- Everything works by keyboard alone: dialogs trap focus (native `<dialog>` +
  `showModal()`), the skip link (`.skip-link` in `global.css`) jumps to
  `#main-content`, nav links are real `<a>`/`NavLink` elements.
- Semantic HTML: `<button>` for actions, `<nav>` for navigation, `<main>` for
  content, `<table>` for tabular data (later steps), `<label>` for every
  field.
- Dialogs use the native `<dialog>` element (`src/components/Dialog`);
  closing one returns focus to whatever triggered it.
- Toasts and form errors are announced via `aria-live` (`role="status"` /
  `role="alert"`).
- A "Skip to content" link is the first focusable element on every page.
- Touch targets are at least 44×44px (`Button`, `TextField`/`Select` inputs,
  the toast dismiss button, the mobile nav toggle all enforce this via
  `min-height`/`min-width` in their CSS modules).
- Status is never shown by colour alone — `Badge` always pairs colour with a
  text label; toasts pair colour with an icon glyph *and* descriptive text.

## 10. Security in the UI

- Never store tokens or user data in `localStorage`/`sessionStorage`. Auth
  state lives only in React state (`AuthContext`), re-derived from
  `GET /api/auth/me/` on load; the actual session lives in the `HttpOnly`
  cookie the browser manages.
- Never render API text as raw HTML (no `dangerouslySetInnerHTML` on
  anything that came from a response body).
- Hiding admin UI (`RequireAdmin`, the nav's `user.is_staff` check) is a
  convenience for non-admins, not a security boundary — the API's
  `IsAdminUser` permission is the real enforcement. Don't rely on hidden UI
  to protect anything.
