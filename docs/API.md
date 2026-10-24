# MeetingSpace — API Contract

Base path: `/api/`. All request/response bodies are JSON unless noted.
All datetimes are ISO 8601 with UTC offset, e.g. `2026-10-25T09:00:00+00:00`.

Authentication is via Django session cookie (`HttpOnly`). Unsafe methods
(`POST`, `PATCH`, `PUT`, `DELETE`) require the `X-CSRFToken` header to match
the `csrftoken` cookie (see `GET /api/auth/csrf/`).

## Errors

| Status | Meaning                        | Body example                                  |
|--------|---------------------------------|------------------------------------------------|
| 400    | Validation error                | `{"start_time": ["BR-4: must be on a 15-minute boundary"]}` |
| 401    | Not logged in                    | `{"detail": "Authentication credentials were not provided."}` |
| 403    | Logged in but not authorized (not admin) | `{"detail": "You do not have permission to perform this action."}` |
| 404    | Not found, or exists but not yours | `{"detail": "Not found."}`                  |
| 405    | Method not allowed               | `{"detail": "Method \"DELETE\" not allowed."}` |
| 409    | Booking overlap (BR-6)           | `{"detail": "BR-6: room is already booked for part of this time range."}` |
| 429    | Throttled                        | `{"detail": "Request was throttled. Expected available in 42 seconds."}` |

---

## `GET /api/health/`

Public. Liveness check.

**200**
```json
{"status": "ok"}
```

---

## `GET /api/auth/csrf/`

Public. Sets the `csrftoken` cookie; call once before `POST /api/auth/login/`.

**200**
```json
{"detail": "CSRF cookie set."}
```

---

## `POST /api/auth/login/`

Public. Throttled to 5 attempts/minute/IP.

**Request**
```json
{"username": "alice", "password": "correct-horse-battery"}
```

**200**
```json
{"id": 1, "username": "alice", "is_staff": false}
```

**400** — bad/missing fields:
```json
{"non_field_errors": ["Unable to log in with provided credentials."]}
```
(Same message for unknown username and wrong password.)

**429** — throttled, see Errors table.

---

## `POST /api/auth/logout/`

Requires authentication.

**204** — empty body.

---

## `GET /api/auth/me/`

Requires authentication.

**200**
```json
{"id": 1, "username": "alice", "is_staff": false}
```

**401** if not logged in.

---

## `GET /api/rooms/`

Requires authentication. Employees see only `is_active=true` rooms; admins see all.

**200**
```json
[
  {"id": 1, "name": "Falcon", "capacity": 8, "location": "3F", "is_active": true, "created_at": "2026-10-01T00:00:00+00:00"}
]
```

---

## `POST /api/rooms/`

Admin only.

**Request**
```json
{"name": "Falcon", "capacity": 8, "location": "3F"}
```

**201** — created Room (same shape as above, `is_active` defaults to `true`).

**400** — e.g. duplicate name:
```json
{"name": ["Room with this name already exists."]}
```

**403** — non-admin.

---

## `GET /api/rooms/{id}/`

Requires authentication.

**200** — Room object (as above).

**404** — unknown id, or an employee requesting an inactive room.

## `PATCH /api/rooms/{id}/`

Admin only. Partial update of `name`, `capacity`, `location`, `is_active`.

**Request**
```json
{"is_active": false}
```

**200** — updated Room object.

**403** — non-admin. **404** — unknown id.

## `DELETE /api/rooms/{id}/`

**405** always (BR-8: rooms are never deleted, only deactivated via PATCH).

---

## `GET /api/rooms/{id}/schedule/?date=YYYY-MM-DD`

Requires authentication. Returns that room's bookings for the given date
(local calendar day in `APP_TIME_ZONE`), ordered by `start_time`.

**200**
```json
[
  {"id": 10, "title": "Sprint planning", "start_time": "2026-10-25T01:00:00+00:00", "end_time": "2026-10-25T02:00:00+00:00", "booked_by": "alice"}
]
```

**400** — missing/invalid `date`:
```json
{"date": ["This field is required."]}
```

**404** — unknown room id.

---

## `GET /api/bookings/`

Requires authentication. Returns the caller's own bookings. Defaults to
upcoming bookings (`end_time >= now`); pass `?past=true` for past bookings.

**200**
```json
[
  {"id": 10, "room": 1, "title": "Sprint planning", "start_time": "2026-10-25T01:00:00+00:00", "end_time": "2026-10-25T02:00:00+00:00", "created_at": "2026-10-20T00:00:00+00:00", "updated_at": "2026-10-20T00:00:00+00:00"}
]
```

---

## `POST /api/bookings/`

Requires authentication. Owner is set to the requesting user.

**Request**
```json
{"room": 1, "title": "Sprint planning", "start_time": "2026-10-25T01:00:00+00:00", "end_time": "2026-10-25T02:00:00+00:00"}
```

**201** — created Booking (shape as above).

**400** — rule violation, e.g.:
```json
{"start_time": ["BR-2: cannot start in the past"]}
```

**409** — overlapping booking (BR-6).

---

## `GET /api/bookings/{id}/`

Owner only.

**200** — Booking object. **404** — unknown id or not owned by caller.

## `PATCH /api/bookings/{id}/`

Owner only. Not allowed if the booking is in the past (BR-7).

**Request**
```json
{"start_time": "2026-10-25T03:00:00+00:00", "end_time": "2026-10-25T04:00:00+00:00"}
```

**200** — updated Booking. **400** — rule violation. **409** — overlap.
**404** — unknown id or not owned by caller.

## `DELETE /api/bookings/{id}/`

Owner only. Cancels (hard-deletes) the booking row. Not allowed if the
booking is in the past (BR-7).

**204** — empty body. **404** — unknown id, not owned, or already cancelled.

---

## `GET /api/admin/bookings/?room=&date=&user=`

Admin only. All bookings, optionally filtered by `room` (id), `date`
(`YYYY-MM-DD`), and `user` (id). All filters optional and combinable.

**200**
```json
[
  {"id": 10, "room": 1, "user": 1, "title": "Sprint planning", "start_time": "2026-10-25T01:00:00+00:00", "end_time": "2026-10-25T02:00:00+00:00"}
]
```

**403** — non-admin.

---

## `DELETE /api/admin/bookings/{id}/`

Admin only. Cancels any user's booking.

**204** — empty body. **403** — non-admin. **404** — unknown id.

---

## `GET /api/admin/users/`

Admin only.

**200**
```json
[
  {"id": 1, "username": "alice", "is_staff": false, "is_active": true}
]
```

## `POST /api/admin/users/`

Admin only. This is the only way to create an account (no public sign-up).

**Request**
```json
{"username": "bob", "password": "a-strong-password", "is_staff": false}
```

**201**
```json
{"id": 2, "username": "bob", "is_staff": false, "is_active": true}
```

**400** — e.g. weak password:
```json
{"password": ["This password is too short. It must contain at least 10 characters."]}
```

**403** — non-admin.

---

## `PATCH /api/admin/users/{id}/`

Admin only. Allows updating `is_active`, `is_staff`, `password`.

**Request**
```json
{"is_active": false}
```

**200** — updated user object (as in `GET /api/admin/users/`, password never
returned).

**400** — BR-9 violation (admin targeting their own account with
`is_active=false` or `is_staff=false`):
```json
{"detail": "BR-9: admins cannot deactivate or demote their own account."}
```

**403** — non-admin. **404** — unknown id.
