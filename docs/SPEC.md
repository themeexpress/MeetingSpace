# MeetingSpace — Product Spec

## Roles

- **Employee** — a regular Django `User` (`is_staff=False`). Can browse rooms, view
  room schedules, and manage their own bookings.
- **Admin** — a Django `User` with `is_staff=True`. Can do everything an Employee can,
  plus manage rooms, manage user accounts, and view/cancel any booking.

There is **no public sign-up**. Accounts are created only by an Admin via
`POST /api/admin/users/` (see docs/API.md). Django superuser status is not used by
the application; authorization is based on `is_staff` only.

## Data model

### Room

| Field       | Type       | Constraints                                  |
|-------------|------------|-----------------------------------------------|
| id          | integer    | primary key                                   |
| name        | string     | unique, max length 100                        |
| capacity    | integer    | 1–100 inclusive                               |
| location    | string     | max length 100                                |
| is_active   | boolean    | default `true`                                |
| created_at  | datetime   | auto-set on creation, UTC                     |

### Booking

| Field       | Type       | Constraints                                   |
|-------------|------------|------------------------------------------------|
| id          | integer    | primary key                                    |
| room        | FK → Room  | required                                       |
| user        | FK → User  | required; the booking owner                    |
| title       | string     | max length 120                                 |
| start_time  | datetime   | UTC, required                                  |
| end_time    | datetime   | UTC, required                                  |
| created_at  | datetime   | auto-set on creation, UTC                      |
| updated_at  | datetime   | auto-updated on save, UTC                      |

### User

The Django built-in `User` model (`username`, `password`, `is_staff`, `is_active`, etc.).
No custom user model is introduced.

## Booking rules

Each rule has a stable ID so tests and error messages can reference it.

| ID    | Rule                                                                                                    |
|-------|-----------------------------------------------------------------------------------------------------------|
| BR-1  | `end_time` must be strictly after `start_time`.                                                           |
| BR-2  | A booking cannot start in the past (relative to the current UTC time).                                    |
| BR-3  | Duration (`end_time - start_time`) must be between 15 minutes and 4 hours, inclusive.                      |
| BR-4  | Both `start_time` and `end_time` must fall on 15-minute boundaries (`:00`, `:15`, `:30`, `:45`).           |
| BR-5  | A booking cannot be made against a room where `is_active=False`.                                          |
| BR-6  | Bookings for the same room cannot overlap. Enforced both at the API layer and by a PostgreSQL exclusion constraint on `(room, [start_time, end_time))`. Back-to-back bookings are allowed (e.g. 10:00–11:00 and 11:00–12:00 do not overlap). |
| BR-7  | A user may only view, edit, or cancel their own bookings. A booking is read-only once its `end_time` is in the past (no edit or cancel). |
| BR-8  | Rooms are never deleted, only deactivated (`is_active=False`). Users are never deleted, only deactivated (`is_active=False`). |
| BR-9  | An admin cannot deactivate (`is_active=False`) or demote (`is_staff=False`) their own account.             |

## Time handling

- All datetimes are stored in the database in **UTC**.
- All API requests and responses use **ISO 8601 with explicit UTC offset**
  (e.g. `2026-10-25T09:00:00+00:00`).
- The frontend displays times converted to `APP_TIME_ZONE` (default `Asia/Tokyo`);
  the backend never performs this display conversion.

## Security requirements

- Authentication uses Django's session framework with an `HttpOnly` session cookie.
  No tokens are stored in `localStorage` or `sessionStorage`.
- CSRF protection (Django's `CsrfViewMiddleware`) is enforced on all unsafe methods
  (`POST`, `PATCH`, `PUT`, `DELETE`).
- The login endpoint is throttled to **5 attempts per minute per IP address**.
- Login failures return the **same error message** regardless of whether the
  username does not exist or the password is wrong, to avoid user enumeration.
- Passwords must be at least **10 characters**, validated by Django's built-in
  password validators (`MinimumLengthValidator` with `min_length=10`, plus the
  common-password and numeric-similarity validators).
- Any object the requesting user is not authorized to access (not theirs, or
  admin-only) returns **404 Not Found**, not 403, to avoid leaking existence of
  the resource. Admin-only *collection* endpoints (e.g. `/api/admin/users/`)
  return **403** for a non-admin, since the endpoint's existence is not secret —
  only individual object ownership is hidden. See docs/API.md for the exact
  status code per endpoint.
