# MeetingSpace

MeetingSpace is a small, production-quality internal meeting-room booking
application. Employees can browse rooms and reserve time slots, while
Admins manage rooms and oversee all bookings across the organisation.

## Features

### Employee
- View the list of meeting rooms and their details (capacity, location, equipment).
- Check room availability on a calendar/schedule view.
- Create, view, and cancel their own bookings.
- Receive clear errors on double-booking or invalid time ranges.

### Admin
- Everything an Employee can do.
- Create, edit, and deactivate meeting rooms.
- View and cancel any booking made by any user.
- Manage user accounts and roles.

## Tech stack

| Layer          | Technology                          |
|----------------|--------------------------------------|
| Backend        | Django 5.2 + Django REST Framework   |
| Database       | PostgreSQL 17                        |
| Frontend       | React 19 + TypeScript + Vite         |
| Containers     | Docker Compose                       |
| CI/CD          | GitHub Actions                       |

## Planned folder structure

```
MeetingSpace/
├── backend/              # Django + DRF project
├── frontend/             # React + TypeScript + Vite app
├── docs/                 # SPEC.md, API.md, and other design docs
├── .github/workflows/    # GitHub Actions CI/CD pipelines
├── docker-compose.yml    # Local multi-container orchestration
├── .env.example
├── .editorconfig
└── README.md
```

## Getting started

_Coming in Step 3._

## Roadmap

- [x] Step 1: Repository skeleton
- [ ] Step 2: Backend project setup (Django + DRF, settings via env vars)
- [ ] Step 3: Docker Compose for local development
- [ ] Step 4: User model, roles, and authentication
- [ ] Step 5: Room model and admin management endpoints
- [ ] Step 6: Booking model and core booking logic
- [ ] Step 7: Booking conflict / overlap validation
- [ ] Step 8: Permissions (Employee vs Admin)
- [ ] Step 9: API tests for rooms and bookings
- [ ] Step 10: Frontend project setup (React + TypeScript + Vite)
- [ ] Step 11: Frontend authentication flow
- [ ] Step 12: Frontend room list and availability views
- [ ] Step 13: Frontend booking creation and cancellation
- [ ] Step 14: Frontend admin views
- [ ] Step 15: CI pipeline (lint, test, build)
- [ ] Step 16: Hardening (security headers, rate limiting, logging)
- [ ] Phase 4: Deployment

## Security

MeetingSpace follows a least-privilege, defense-in-depth approach:

- **Session cookies**: authentication uses Django's secure, `HttpOnly` session
  cookies rather than storing tokens in client-side JavaScript.
- **CSRF protection**: all state-changing requests are protected by Django's
  CSRF middleware, with trusted origins configured via environment variables.
- **Throttled login**: login attempts are rate-limited to mitigate
  credential-stuffing and brute-force attacks.
- **Least privilege**: Employees can only access and modify their own
  bookings; Admin-only actions are enforced server-side via DRF permissions.
- **Secrets in environment variables**: no secrets or credentials are
  hard-coded; all configuration (database credentials, Django secret key,
  allowed hosts, etc.) is supplied via environment variables and never
  committed to source control.
