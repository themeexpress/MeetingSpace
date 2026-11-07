# MeetingSpace — Architecture Decision Records

## ADR-1: Session cookies instead of JWT in localStorage

**Decision:** Use Django's built-in session framework with an `HttpOnly`
cookie for authentication, not a JWT (or any token) stored in
`localStorage`/`sessionStorage`.

**Why:** Tokens in `localStorage` are readable by any JavaScript running on
the page, so a single XSS vulnerability leads to full account takeover.
`HttpOnly` session cookies are invisible to JavaScript. This is an internal
tool with a single first-party frontend talking to a single backend on
related origins, so we don't need JWT's cross-domain/stateless benefits — the
server can cheaply hold session state. CSRF is the trade-off, and Django's
built-in CSRF middleware handles it directly.

## ADR-2: PostgreSQL exclusion constraint for overlap prevention

**Decision:** Enforce "no overlapping bookings per room" (BR-6) both in the
DRF serializer/view *and* with a PostgreSQL exclusion constraint on
`(room, tstzrange(start_time, end_time, '[)'))` using the `btree_gist`
extension (`start_time`/`end_time` are `timestamptz` columns, so the range
type is `tstzrange`, not plain `tsrange`).

**Why:** Application-level validation alone is vulnerable to a race
condition: two requests for the same room/time can both run the serializer's
overlap query before either has committed its `INSERT`, see no conflicting
row yet, and both pass — producing a double-booking. The database is the
only component that can atomically guarantee this invariant under
concurrency, because the exclusion constraint is checked at commit time
against whatever has actually been written, not against a snapshot read
earlier in the request. The constraint is the source of truth; the
serializer-level query exists only to return a friendly `409` with a clear
message in the common, non-racing case. When the race does happen, the
constraint raises a Postgres `IntegrityError` on `save()`, which the view
catches and turns into the same `409` response.

## ADR-3: Deactivate instead of delete

**Decision:** Rooms and Users are never hard-deleted (BR-8). They are
deactivated via `is_active=False`.

**Why:** Bookings reference rooms and users by foreign key. Deleting a room
or user that has booking history would either cascade-delete that history or
require nullable FKs, both of which destroy an audit trail that may be needed
later (e.g. "who booked what, when"). Deactivation preserves history while
removing the entity from day-to-day use (inactive rooms are hidden from
employees; deactivated users can no longer log in).

## ADR-4: Admin-created accounts only, no public sign-up

**Decision:** There is no public registration endpoint. Accounts are created
exclusively by an admin via `POST /api/admin/users/`.

**Why:** MeetingSpace is an internal tool for a known, fixed set of
employees, not a public-facing product. Removing self-registration removes
an entire class of risk (spam accounts, unvetted access, username/email
enumeration via a signup form) and keeps provisioning aligned with however
the organisation already manages employee accounts.

## ADR 5: HSTS without includeSubDomains and preload (for now)

- **Decision:** HSTS is enabled (30 days) but without `includeSubDomains` and `preload`.
  Django checks `security.W005` and `security.W021` are silenced.
- **Why:** both options affect every subdomain and are hard to reverse (the browser preload
  list takes months to leave). The production domain is not final yet.
- **Revisit:** Phase D5, once the domain is final and all subdomains serve HTTPS.
