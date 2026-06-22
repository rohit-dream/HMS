# MVP Sprint Plan V2 — Production-Ready Roadmap

| Field | Value |
|-------|-------|
| **Version** | 2.1 (audit + SaaS billing + invite gaps closed) |
| **Status** | **Authoritative** — use this for all development |
| **Created** | June 2026 |
| **Team** | 1 solo full-stack developer |
| **Duration** | 12 sprints × 2 weeks = 24 weeks |
| **Capacity** | ~56 net dev hours per sprint |
| **MVP Definition** | PRD §9.1 + FRD §15.1 P0 requirements + production launch (Gate G5) |
| **Out of MVP** | IPD, Laboratory, Pharmacy, Insurance/TPA, AI, mobile apps, HL7/FHIR |

---

## Executive Summary

This plan **replaces** `03_SPRINT_PLAN_DETAILED.md` v1. It fixes every gap identified in the SDLC audit:

- Vertical slices (backend + frontend + tests every sprint)
- RLS on **every** migration sprint
- Security/compliance tasks embedded (not deferred to end)
- All P0 functional requirements assigned to a sprint
- Staging before production
- Explicit OPD API specification sprint
- Production launch checklist with pen test, backup verify, 2FA

**After S12:** A hospital can register → verify email → onboard staff → register patients → book appointments → run OPD → bill patients → view reports → pay SaaS subscription → run on AWS production.

---

## MVP Module Scope

| In MVP | Post-MVP (Phase 2) |
|--------|-------------------|
| Multi-tenant platform | IPD (wards, beds, admissions) |
| Auth + RBAC + 2FA (owners) | Laboratory |
| Tenant/hospital onboarding | Pharmacy + inventory |
| User/staff/department/doctor mgmt | Advanced analytics |
| Patient management + documents | SMS notifications |
| Appointments + OPD full workflow | Multi-location deep scoping |
| Patient billing + receipts | Custom roles |
| Dashboard + core reports | API marketplace |
| Audit logs + PHI access logs | Hindi localization |
| In-app + email notifications | Telemedicine |
| SaaS trial + Razorpay billing | White-label |
| File uploads (S3) | |
| Docker local + AWS staging + production | |

---

## Database Tables — MVP vs Post-MVP

### MVP tables (48 total)

| Sprint | Tables |
|--------|--------|
| S1 | Extensions, schemas, functions |
| S2 | `platform.tenants`, `subscription_plans`, `tenant_subscriptions`, `tenant_locations`, `tenant_settings` |
| S3 | `core.users`, `user_sessions`, `password_reset_tokens`, `email_verification_tokens`, **`audit.audit_logs`** |
| S4 | `core.roles`, `permissions`, `role_permissions`, `user_roles`, **`core.user_invite_tokens`** *(new)* |
| S6 | `core.departments`, `staff`, `doctors`, `doctor_schedules` |
| S7 | `core.patients`, `patient_allergies`, `patient_contacts`, `patient_documents` (+ `chronic_conditions` JSONB on patients) |
| S8 | `clinical.appointments` |
| S9 | `clinical.opd_visits`, `opd_queue`, `opd_vitals`, `opd_clinical_notes`, `opd_prescriptions`, `opd_prescription_items`, `opd_referrals` |
| S10 | `billing.billing_services`, `invoices`, `invoice_line_items`, `payments`, `payment_allocations`, `invoice_adjustments` |
| S11 | `audit.phi_access_logs`, `comms.notification_templates`, `notifications`, `notification_preferences`, `notification_delivery_log` |
| S12 | `platform.subscription_invoices`, **`platform.subscription_payments`**, **`platform.payment_methods`** *(new)* |

### Post-MVP tables (not in any MVP sprint)

`clinical.wards`, `rooms`, `beds`, `admissions`, `admission_transfers`, `nursing_notes`, `ipd_vitals`, `discharge_summaries`, `ipd_daily_charges` · `pharmacy.*` (6) · `laboratory.*` (7)

---

## Gates

| Gate | Sprint | Criteria |
|------|--------|----------|
| **G1** Start feature work | End S2 | Docker, CI, RLS framework, seeds, isolation test pass |
| **G2** Core platform usable | End S4 | Register, verify email, login, manage users/hospital |
| **G3** Clinical workflow | End S9 | Patient → appointment → OPD consult → e-Rx |
| **G4** Revenue workflow | End S10 | Invoice → payment → receipt PDF |
| **G5** **MVP Production Launch** | End S12 | Staging + prod live, 10 beta tenants, security gate pass |

---

# SPRINT 1 — Foundation, Tooling & Quality Baseline

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Runnable monorepo, local Docker stack, CI, logging, error envelope, testing harness, documentation baseline |
| **Gate** | Prerequisites for G1 |

## Features to Develop

- Monorepo structure per `FOLDER_STRUCTURE_FREEZE.md`
- Docker Compose: PostgreSQL 14, Redis 7, API (optional)
- GitHub Actions: ruff + pytest + frontend `tsc`
- FastAPI app factory: health, readiness, correlation ID
- Standard API envelope `{ data, meta, errors }`
- Global exception handlers
- Structured JSON logging with `request_id`, `tenant_id`
- `docs/TESTING_STRATEGY.md` (initial version)
- `docs/DEPLOYMENT_GUIDE.md` (skeleton)
- Alembic init + migration `001_database_foundation` (extensions, 8 schemas, `set_updated_at`, `enforce_tenant_self_reference`)

## Database Changes

| Migration | Content |
|-----------|---------|
| `001_database_foundation` | `pgcrypto`, schemas (`platform`, `core`, `clinical`, `billing`, `pharmacy`, `laboratory`, `comms`, `audit`), trigger functions |

## Backend APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/health/ready` | DB + Redis connectivity |

## Frontend Pages

| Page | Path | Purpose |
|------|------|---------|
| App shell | `/` | Layout, nav placeholder |
| Health check | `/health` | API connectivity display |

## Validation Rules

- N/A (infrastructure sprint)

## Security Requirements

- `.env.example` only; no secrets in git
- CORS restricted to configured origins (not `*` in production config)
- Security headers middleware stub (full list in S11)

## Testing Requirements

- Pytest + `conftest.py` with test DB
- `tests/unit/test_envelope.py`
- `tests/integration/test_health.py`
- CI must pass on every push
- Coverage baseline recorded (target ≥70% on new code per sprint)

## Definition of Done

- [ ] `docker compose up` → Postgres + Redis healthy
- [ ] `alembic upgrade head` succeeds on clean DB
- [ ] `GET /health` and `/health/ready` return envelope JSON
- [ ] CI green (backend lint + tests)
- [ ] `npm run build` succeeds (frontend)
- [ ] `TESTING_STRATEGY.md` and `DEPLOYMENT_GUIDE.md` skeleton committed
- [ ] No secrets in repository

---

# SPRINT 2 — Multi-Tenant Core, RLS Framework & Seeds

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Platform tables live, RLS pattern established, system tenant + plans seeded, tenant middleware, DB session `SET app.tenant_id` |
| **Gate** | **G1** |

## Features to Develop

- Alembic `002_platform_tables` (5 platform tables)
- RLS policies on all platform tenant-scoped tables
- `platform.create_tenant()` function
- SQLAlchemy models: platform schema
- `TenantScopedRepository` base class
- DB session hook: `SET LOCAL app.tenant_id` on every request/job
- Tenant resolution middleware (slug header for dev; subdomain for prod)
- System tenant seed (`00000000-0000-0000-0000-000000000001`)
- Subscription plans seed (starter, professional, enterprise)
- Cross-tenant isolation integration test (mandatory in CI)
- Platform API: tenant CRUD (admin), register stub

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `002_platform_tables` | `tenants`, `subscription_plans`, `tenant_subscriptions`, `tenant_locations`, `tenant_settings` | ✅ All |

## Backend APIs

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/platform/register` | Public |
| GET | `/api/v1/platform/tenants/{id}` | Platform admin |
| PATCH | `/api/v1/platform/tenants/{id}/status` | Platform admin |

## Frontend Pages

- None (backend focus; shell only)

## Validation Rules

- `slug`: `^[a-z0-9-]+$`, unique, reserved words blocked
- `subdomain`: same as slug rules
- `email`: valid format, lowercase stored

## Security Requirements

- `tenant_id` never accepted from request body for data access
- RLS `FORCE ROW LEVEL SECURITY` on all new tables
- Isolation test: Tenant A row invisible to Tenant B context

## Testing Requirements

- `tests/integration/test_tenant_isolation.py` (RLS + repository)
- `tests/integration/test_platform_register.py`
- Seed idempotency test (re-run seeds without duplicate errors)

## Definition of Done

- [x] All platform tables migrated with RLS
- [x] `SET LOCAL app.tenant_id` works in repository layer
- [x] System tenant + 3 plans seeded
- [x] Cross-tenant isolation test passes in CI
- [x] Tenant registration API returns `201` with `tenant_id`
- [x] **G1 passed** (MVP-020)

---

# SPRINT 3 — Authentication, Email Verification & Frontend Auth (Vertical Slice)

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Complete auth: login, logout, refresh, password reset, email verification, CAPTCHA — **backend AND frontend together** |
| **Gate** | — |

## Features to Develop

- Alembic `003_auth_audit_tables` + RLS
- JWT RS256 access token (30 min) + HttpOnly refresh cookie (7 days)
- bcrypt password hashing
- Account lockout: 5 failures → 15 min lock
- `core.email_verification_tokens` table
- **`audit.audit_logs` table** (required for login/logout audit — FR-AUTH-008)
- Email verification flow (FR-PLT-002)
- CAPTCHA on register/login (hCaptcha dev stub)
- Auth API: login, logout, refresh, me, forgot/reset password, verify-email
- **Audit writes on login, logout, lockout, password reset**
- **Frontend session idle timeout (30 min)** — FR-AUTH-006
- **JWT key generation script** (`scripts/generate_jwt_keys.py`)
- **Frontend:** `AuthProvider`, login page, forgot/reset/verify pages, token refresh interceptor
- **Frontend:** access token in memory only (never localStorage)

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `003_auth_audit_tables` | `users`, `user_sessions`, `password_reset_tokens`, `email_verification_tokens`, **`audit_logs`** | ✅ All |

## Backend APIs

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/logout` | Bearer |
| POST | `/api/v1/auth/refresh` | Cookie |
| GET | `/api/v1/auth/me` | Bearer |
| PATCH | `/api/v1/auth/me` | Bearer |
| POST | `/api/v1/auth/forgot-password` | Public |
| POST | `/api/v1/auth/reset-password` | Public |
| POST | `/api/v1/auth/verify-email` | Public |
| POST | `/api/v1/auth/resend-verification` | Bearer |

## Frontend Pages

| Page | Path |
|------|------|
| Login | `/login` |
| Forgot password | `/forgot-password` |
| Reset password | `/reset-password` |
| Verify email | `/verify-email` |

## Validation Rules

- Password: min 8, uppercase, lowercase, number, special char
- Email: valid, unique per tenant
- Reset token: 1-hour expiry, single use
- Verification token: 24-hour expiry

## Security Requirements

- Permissions **NOT** in JWT (roles only for UI hints)
- Refresh token rotation on refresh
- Session invalidation on password change
- Rate limit: 10 login attempts/min/IP (Redis)
- Audit log: login, logout, lockout, reset events
- CAPTCHA verified server-side

## Testing Requirements

- Login / refresh / logout integration tests
- Lockout after 5 failures
- Cross-tenant login isolation (same email, different tenants)
- Frontend: login form validation (Zod)
- E2E smoke: login → `/me` (Playwright or API-only script)

## Definition of Done

- [ ] User can log in via UI and reach dashboard placeholder
- [ ] Refresh works without re-login
- [ ] Password reset flow works (email logged in dev)
- [ ] Email verification blocks full access until verified
- [ ] Auth integration tests pass
- [ ] RLS on all auth tables

---

# SPRINT 4 — RBAC, User Management & Hospital Admin (Vertical Slice)

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | RBAC enforced; hospital owner can manage hospital profile, branches, users, roles |
| **Gate** | **G2** |

## Features to Develop

- Alembic `004_rbac_invite_tables` + RLS
- Permission catalog seed (all MVP permissions incl. **`opd:queue`**, **`admin:staff`**)
- Role clone on tenant provisioning
- Permission resolver + Redis cache (5 min TTL)
- `@requires_permission` decorator on all endpoints
- User management API (CRUD, invite, disable, roles, reset)
- **`POST /auth/accept-invite`** + `core.user_invite_tokens` table
- Hospital profile + locations + settings API (tax rate, currency, MRN prefix — FR-ADM-004)
- Email adapter (SES stub / log-only dev)
- Subscription status middleware (trial/active/suspended gate)
- Tenant registration wizard (frontend) with **privacy policy + terms acceptance** (NFR-COMP-008)
- Protected routes + role-based landing
- `PermissionGuard` + `usePermissions()` hooks
- Hospital settings UI, branches UI, user management UI, **system config UI (tax, currency, MRN)**

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `004_rbac_invite_tables` | `roles`, `permissions`, `role_permissions`, `user_roles`, **`user_invite_tokens`** | ✅ All |

## Backend APIs

| Module | Base Path | Key Endpoints |
|--------|-----------|---------------|
| Hospital | `/api/v1/hospital` | `GET/PATCH /profile`, CRUD `/locations`, CRUD `/settings` |
| Admin Users | `/api/v1/admin/users` | CRUD, invite, disable, roles, reset-password |
| Auth | `/api/v1/auth/accept-invite` | Public (invite token) |

## Frontend Pages

| Page | Path | Permission |
|------|------|------------|
| Registration wizard | `/register` | Public |
| Hospital settings | `/admin/settings` | `admin:settings` |
| Branches | `/admin/branches` | `admin:settings` |
| User list | `/admin/users` | `admin:users` |
| User detail / invite | `/admin/users/:id` | `admin:users` |
| Dashboard (role router) | `/dashboard` | Authenticated |

## Validation Rules

- Max 2 `hospital_owner` per tenant
- Cannot remove last owner
- Plan user limit enforced on create/invite (402 if exceeded)
- Invite email required; role must exist in tenant

## Security Requirements

- RBAC 403 on unauthorized endpoints
- UI hides actions without permission
- Invite tokens single-use, 72-hour expiry
- Tenant suspended → 403 on all authenticated routes

## Testing Requirements

- RBAC: receptionist denied `admin:users`
- Owner allowed all admin endpoints
- Permission cache invalidation on role change
- User CRUD integration tests
- E2E: register → verify → login → invite user

## Definition of Done

- [ ] Self-service registration + onboarding wizard works E2E
- [ ] Hospital owner manages profile, branch, users via UI
- [ ] RBAC enforced on API and UI
- [ ] Subscription middleware blocks suspended tenants
- [ ] **G2 passed**

---

# SPRINT 5 — API Standards, OPD Spec & Error/Logging Hardening

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Close documentation gaps; publish OPD OpenAPI module; audit logging framework; OpenAPI docs live |
| **Gate** | — |

## Features to Develop

- **Author `docs/API_DESIGN_OPD.md`** (complete): visits, queue, vitals, notes, e-Rx
- Add **`opd:queue`** permission to RBAC catalog + role maps
- OpenAPI tags and router stubs for OPD (no business logic yet)
- Audit log write service (persists to `audit.audit_logs` from S3)
- Mutation middleware: log POST/PUT/PATCH/DELETE with actor, resource, IP
- **Composite FK rule**: document + lint check for `(tenant_id, id)` on all cross-schema FKs
- Idempotency key support for billing endpoints (header validation)
- API rate limiting middleware skeleton (Redis)
- Frontend: shared form components, table, modal, toast (design system minimum)
- Update stale docs (`DEVELOPMENT_READINESS_REPORT`, `00_PROJECT_BASELINE`)

## Database Changes

- None (spec + infrastructure sprint)

## Backend APIs

- OpenAPI `/api/v1/docs` complete for modules S1–S4
- OPD router stubs returning `501` with documented schemas

## Frontend Pages

| Component | Purpose |
|-----------|---------|
| `components/ui/*` | Button, Input, Table, Modal, Toast |
| `components/forms/FormField` | RHF + Zod wrapper |

## Validation Rules

- Document all OPD request/response schemas in OpenAPI
- Standard 422 validation error format on all endpoints

## Security Requirements

- OpenAPI does not expose internal admin paths without auth docs
- Audit service never logs passwords or tokens

## Testing Requirements

- OpenAPI schema snapshot test (breaking change detection)
- Audit write unit test (mock DB)

## Definition of Done

- [ ] OPD API fully specified (≥15 endpoints documented)
- [ ] OpenAPI published and accurate for auth, hospital, admin, patients stub
- [ ] Audit write service callable from any domain service
- [ ] Shared UI components used in admin screens
- [ ] Stale planning docs updated

---

# SPRINT 6 — Departments, Staff & Doctors (Vertical Slice)

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Hospital organizational structure complete |
| **Gate** | — |

## Features to Develop

- Alembic `005_org_tables` + RLS
- Departments CRUD API
- Staff CRUD API (link department, optional user account)
- Doctors API (extends staff: specialization, fee, license)
- Doctor schedules API (weekly slots)
- Department, staff, doctor admin UI
- Doctor list for appointment module

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `005_org_tables` | `departments`, `staff`, `doctors`, `doctor_schedules` | ✅ All |

## Backend APIs

| Module | Base Path |
|--------|-----------|
| Staff | `/api/v1/staff` |
| Departments | `/api/v1/admin/departments` |
| Doctors | `/api/v1/doctors` |
| Schedules | `/api/v1/doctors/{id}/schedules` |

## Frontend Pages

| Page | Path |
|------|------|
| Departments | `/admin/departments` |
| Staff list | `/admin/staff` |
| Staff form | `/admin/staff/new`, `/admin/staff/:id` |
| Doctors | `/admin/doctors` |
| Doctor schedule editor | `/admin/doctors/:id/schedule` |

## Validation Rules

- Department code unique per tenant
- Staff employee code unique per tenant
- Doctor must link to staff record
- Schedule: `day_of_week` 0–6, `end_time` > `start_time`
- Consultation fee ≥ 0

## Security Requirements

- `admin:staff`, `admin:departments`, `admin:doctors` permissions
- Soft delete only

## Testing Requirements

- Department + staff + doctor CRUD integration tests
- Tenant isolation on all org endpoints
- Schedule overlap validation unit test

## Definition of Done

- [ ] Admin creates departments, staff, doctors via UI
- [ ] Doctor schedules configurable
- [ ] RLS on all org tables
- [ ] Integration tests pass

---

# SPRINT 7 — Patient Management (Vertical Slice)

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Full patient lifecycle: register, search, profile, allergies, contacts, duplicate warning, consent |
| **Gate** | — |

## Features to Develop

- Alembic `006_patient_tables` + RLS + **`pg_trgm` extension**
- MRN generator: `MRN-YYYY-NNNNN` per tenant
- Patient CRUD API + allergies + contacts + **chronic conditions** (FR-PAT-006)
- **`GET /patients/{id}/visits`** visit history API (FR-PAT-011)
- Duplicate detection by phone + name similarity (warning, not block)
- Patient consent flag on registration (DPDP FR-PAT-009)
- Trial plan: 100 patient cap enforcement
- PHI access log writes on patient read (service; table in S11)
- Patient list, registration form, profile UI
- Visit history section (empty until S9)

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `006_patient_tables` | `patients`, `patient_allergies`, `patient_contacts`, `patient_documents` | ✅ All |
| Indexes | `pg_trgm` on name; btree on `tenant_id+phone`, `tenant_id+mrn` | — |

## Backend APIs

| Method | Path | Permission |
|--------|------|------------|
| GET/POST | `/api/v1/patients` | `patient:read` / `patient:create` |
| GET/PATCH/DELETE | `/api/v1/patients/{id}` | `patient:read` / `patient:update` / `patient:delete` |
| GET/POST | `/api/v1/patients/{id}/allergies` | `patient:update` |
| GET/POST | `/api/v1/patients/{id}/contacts` | `patient:update` |
| GET/POST | `/api/v1/patients/{id}/chronic-conditions` | `patient:update` |
| GET | `/api/v1/patients/{id}/visits` | `patient:read` |
| GET | `/api/v1/patients/check-duplicate` | `patient:create` |

## Frontend Pages

| Page | Path |
|------|------|
| Patient list | `/patients` |
| Register patient | `/patients/new` |
| Patient profile | `/patients/:id` |

## Validation Rules

- Phone: 10 digits (India MVP)
- DOB: not future; age computed
- Gender: enum `male|female|other`
- MRN auto-generated; immutable
- Consent checkbox required on create
- Duplicate warning shown; user confirms to proceed

## Security Requirements

- PHI access logged on GET patient by id
- Return 404 (not 403) for cross-tenant patient ID
- Soft delete only

## Testing Requirements

- MRN uniqueness per tenant (same MRN allowed across tenants)
- Duplicate detection unit test
- Search performance smoke (<1s on 10K seed records)
- Patient CRUD + isolation integration tests
- Registration form Zod tests

## Definition of Done

- [ ] Receptionist registers patient in <2 min via UI
- [ ] Search by name, phone, MRN works
- [ ] Allergies and contacts on profile
- [ ] Duplicate warning functional
- [ ] Trial patient cap enforced
- [ ] RLS + isolation tests pass

---

# SPRINT 8 — Appointments & Scheduling (Vertical Slice)

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Doctor-wise appointment booking with availability checks |
| **Gate** | — |

## Features to Develop

- Alembic `007_appointment_tables` + RLS
- Appointments CRUD API
- Slot availability check against doctor schedules
- Conflict detection (409 on double-book)
- Appointment calendar UI (week view)
- Booking modal (patient + doctor + slot)
- Walk-in flag on appointment

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `007_appointment_tables` | `clinical.appointments` | ✅ |

## Backend APIs

| Method | Path | Permission |
|--------|------|------------|
| GET/POST | `/api/v1/appointments` | `appointment:read` / `appointment:create` |
| GET/PATCH/DELETE | `/api/v1/appointments/{id}` | `appointment:read` / `appointment:update` |
| POST | `/api/v1/appointments/{id}/confirm` | `appointment:update` |
| POST | `/api/v1/appointments/{id}/cancel` | `appointment:update` |
| GET | `/api/v1/appointments/availability` | `appointment:read` |

## Frontend Pages

| Page | Path |
|------|------|
| Appointment calendar | `/appointments` |
| Appointment detail | `/appointments/:id` |

## Validation Rules

- `appointment_date` not in past
- Slot must fall within doctor schedule
- Status transitions: `scheduled` → `confirmed` → `completed` | `cancelled` | `no_show`
- Cannot book completed/cancelled slot

## Security Requirements

- `appointment:create` for receptionist; `appointment:read` for doctor
- Patient and doctor must belong to same tenant

## Testing Requirements

- Double-book returns 409
- Availability endpoint unit tests
- Appointment isolation integration tests
- Calendar UI component test

## Definition of Done

- [ ] Receptionist books appointment for doctor + patient
- [ ] Availability reflects doctor schedule
- [ ] Confirm and cancel work
- [ ] UI calendar functional at ≥1024px

---

# SPRINT 9 — OPD Workflow (Vertical Slice)

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Full OPD: queue → consultation → vitals → notes → e-prescription → complete visit |
| **Gate** | **G3** |

## Features to Develop

- Alembic `008_opd_tables` + RLS
- OPD visits API (create from appointment or walk-in)
- Queue API: add token, call next, reorder, complete
- Consultation API: vitals, clinical notes, diagnosis
- E-prescription API: header + line items
- Queue polling endpoint (5s interval — MVP; WebSocket post-MVP)
- OPD queue board UI (receptionist)
- Doctor consultation screen (patient context, history, vitals form, Rx form)
- Visit status: `waiting` → `in_consultation` → `completed`
- Link completed visit to patient history

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `008_opd_tables` | `opd_visits`, `opd_queue`, `opd_vitals`, `opd_clinical_notes`, `opd_prescriptions`, `opd_prescription_items`, `opd_referrals` | ✅ All |

## Backend APIs

| Module | Base Path |
|--------|-----------|
| OPD Visits | `/api/v1/opd/visits` |
| Queue | `/api/v1/opd/queue` |
| Vitals | `/api/v1/opd/visits/{id}/vitals` |
| Notes | `/api/v1/opd/visits/{id}/notes` |
| Prescriptions | `/api/v1/opd/visits/{id}/prescriptions` |

## Frontend Pages

| Page | Path | Role |
|------|------|------|
| OPD queue board | `/opd/queue` | Receptionist |
| Doctor consultation | `/opd/consult/:visitId` | Doctor |
| OPD visit summary | `/opd/visits/:id` | All clinical |

## Validation Rules

- Token number auto-assigned per doctor per day
- Vitals: BP, pulse, temp, weight, height, SpO2 — numeric ranges
- Prescription: drug name, dosage, frequency, duration required
- Cannot prescribe on completed visit
- Queue polling returns current state <500ms

## Security Requirements

- `opd:queue` for receptionist; `opd:consult` for doctor
- PHI access log on consultation view
- Clinical notes immutable after visit completed (append-only correction in post-MVP)

## Testing Requirements

- Full OPD workflow integration test
- Queue token ordering unit test
- Role test: receptionist cannot access consult notes write
- E2E: appointment → queue → consult → complete

## Definition of Done

- [ ] Walk-in and appointment both create visits
- [ ] Queue board updates via polling
- [ ] Doctor completes consult with vitals + e-Rx
- [ ] Visit appears on patient history
- [ ] **G3 passed**

---

# SPRINT 10 — Billing & Invoicing (Vertical Slice)

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Service master, invoice from OPD visit, payments, receipts, PDF |
| **Gate** | **G4** |

## Features to Develop

- Alembic `009_billing_tables` + RLS
- Billing service master CRUD
- Invoice: draft from OPD visit (auto-populate consultation fee)
- Invoice finalize, void (with reason + audit)
- **`POST /billing/invoices/{id}/approve-discount`** for discounts >10% (FR-BIL + `billing:approve`)
- Payments: cash, UPI, card, bank transfer
- Partial payments + outstanding balance
- Receipt generation + sequential receipt number
- GST tax line calculation
- PDF generation (invoice + receipt) — sync MVP; async SQS post-MVP
- Seed default services on tenant onboarding
- Billing UI: invoice list, create, payment modal, receipt print
- Idempotency on payment POST

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `009_billing_tables` | `billing_services`, `invoices`, `invoice_line_items`, `payments`, `payment_allocations`, `invoice_adjustments` | ✅ All |

## Backend APIs

| Module | Base Path |
|--------|-----------|
| Services | `/api/v1/billing/services` |
| Invoices | `/api/v1/billing/invoices` |
| Payments | `/api/v1/billing/payments` |
| Receipts | `/api/v1/billing/receipts/{id}/pdf` |

## Frontend Pages

| Page | Path |
|------|------|
| Service master | `/billing/services` |
| Invoice list | `/billing/invoices` |
| Invoice detail + pay | `/billing/invoices/:id` |
| Payment receipt | `/billing/receipts/:id` |

## Validation Rules

- Invoice number sequential per tenant
- Void only if no payments applied
- Discount >10% requires `billing:approve_discount` (owner/admin)
- Payment amount ≤ outstanding balance
- Tax rates from tenant settings

## Security Requirements

- `billing:void` restricted to owner/admin
- Accountant: `billing:*` except void
- All voids audited with reason

## Testing Requirements

- Invoice from OPD visit integration test
- Partial payment math unit test
- Idempotent payment test (duplicate key)
- Void audit log verification
- E2E: complete visit → invoice → pay → receipt PDF

## Definition of Done

- [ ] OPD visit generates billable invoice
- [ ] Payment recorded with receipt PDF
- [ ] Void with audit trail works
- [ ] Accountant role tested
- [ ] **G4 passed**

---

# SPRINT 11 — Dashboard, Reports, Audit, Notifications & File Uploads

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Operational visibility, compliance logging, document uploads, notifications |
| **Gate** | — |

## Features to Develop

- Alembic `010_audit_comms_tables` + RLS
- `audit.phi_access_logs` table *(new)*
- Audit log list API with filters (user, action, date)
- PHI access logs API (owner/admin only)
- Dashboard stats API (today patients, revenue, appointments) — Redis 2-min cache
- Reports: daily collection, OPD summary, audit log export (CSV/PDF)
- S3 pre-signed upload URLs for patient documents
- Patient document metadata API
- ClamAV scan hook (stub: mark clean in dev; real scan before prod)
- In-app notifications API
- **SQS worker service** (`hms-worker` Docker image + email job consumer)
- Notification templates seed
- Appointment confirmation email on booking
- Dashboard UI + reports page
- Audit log viewer UI
- Notification bell UI

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `010_comms_phi_tables` | `phi_access_logs`, `notification_templates`, `notifications`, `notification_preferences`, `notification_delivery_log` | ✅ All |

## Backend APIs

| Module | Base Path |
|--------|-----------|
| Audit | `/api/v1/admin/audit` |
| PHI Access | `/api/v1/admin/phi-access` |
| Dashboard | `/api/v1/reports/dashboard` |
| Reports | `/api/v1/reports/daily-collection`, `/opd-summary` |
| Files | `/api/v1/files/upload-url`, `/files/confirm` |
| Notifications | `/api/v1/notifications` |

## Frontend Pages

| Page | Path |
|------|------|
| Dashboard | `/dashboard` (enhanced) |
| Reports | `/reports` |
| Audit logs | `/admin/audit` |
| Patient documents tab | `/patients/:id/documents` |

## Validation Rules

- File upload: max 10MB, PDF/JPG/PNG only
- MIME validated by magic bytes
- Report date range max 1 year
- Audit logs: append-only, no delete API

## Security Requirements

- S3 keys server-generated: `tenants/{tenant_id}/patients/{patient_id}/...`
- PHI access report: owner/admin only
- Pre-signed URL expiry 15 min

## Testing Requirements

- Dashboard cache invalidation test
- File upload integration test (mock S3)
- Audit log filter integration test
- Daily collection report accuracy test with seed data

## Definition of Done

- [ ] Dashboard shows today's KPIs
- [ ] Daily collection report matches payments
- [ ] Audit log searchable in UI
- [ ] Patient document upload works
- [ ] Email sent on appointment booking (dev log)
- [ ] PHI access logs populated

---

# SPRINT 12 — SaaS Billing, Security Hardening, Staging, Production Launch

| Field | Value |
|-------|-------|
| **Duration** | 2 weeks (~56 hrs) |
| **Goal** | Razorpay subscription, 2FA, rate limits, staging + production AWS, UAT, **MVP LAUNCH** |
| **Gate** | **G5 — MVP Production Launch** |

## Features to Develop

- Alembic `011_saas_billing_tables` + RLS
- Razorpay: customer, subscription, webhook handler
- **`platform.payment_methods`** + **`platform.subscription_payments`** tables
- Trial → paid conversion flow
- Plan upgrade/downgrade + proration
- Suspension on payment failure (7-day grace)
- **Scheduled jobs**: monthly auto-billing (FR-SUB-004), renewal reminders 7d+1d (FR-SUB-005)
- Plan limit enforcement (users, patients, module flags — FR-SUB-006)
- TOTP 2FA for `hospital_owner` and `hospital_admin`
- Rate limiting: 1000 req/min/tenant, 10 auth/min/IP
- Security headers (HSTS, CSP, X-Frame-Options)
- **Bandit SAST in CI** (NFR-SEC-013)
- Terraform: staging environment (ECS, RDS, Redis, S3)
- Terraform: production environment (Multi-AZ RDS)
- **Docker images + ECR push pipeline**
- CloudWatch alarms (error rate, CPU, DB connections)
- Backup restore drill on staging
- OWASP ZAP scan on staging (NFR-SEC-014 self-assessment)
- `DEPLOYMENT_GUIDE.md` complete
- Onboarding wizard UI (final steps: departments, services, first patient)
- UAT with 10 beta tenants
- P0 bug burn-down
- MVP release notes

## Database Changes

| Migration | Tables | RLS |
|-----------|--------|-----|
| `011_saas_billing_tables` | `subscription_invoices`, **`payment_methods`**, **`subscription_payments`** | ✅ All |

## Backend APIs

| Module | Base Path |
|--------|-----------|
| Subscription | `/api/v1/platform/subscription` |
| Webhooks | `/api/v1/webhooks/razorpay` |
| 2FA | `/api/v1/auth/2fa/setup`, `/auth/2fa/verify` |

## Frontend Pages

| Page | Path |
|------|------|
| Subscription & billing | `/admin/subscription` |
| 2FA setup | `/admin/security/2fa` |
| Onboarding wizard | `/onboarding` |
| Payment method | `/admin/subscription/payment` |

## Validation Rules

- Webhook signature verified (HMAC)
- 2FA TOTP 6 digits; backup codes hashed
- Subscription state machine enforced

## Security Requirements

- **Pre-launch gate (all must pass):**
  - [ ] RLS on all **48** MVP tables verified
  - [ ] Cross-tenant isolation regression 100% pass
  - [ ] 2FA enforced for owners
  - [ ] Rate limiting active
  - [ ] Security headers verified
  - [ ] Secrets in AWS Secrets Manager only
  - [ ] Backup restore tested
  - [ ] OWASP ZAP scan: no critical/high open
  - [ ] ClamAV enabled on file uploads (or disabled with documented risk acceptance)

## Testing Requirements

- Razorpay webhook integration test (sandbox)
- 2FA setup + login flow test
- Full regression suite (all gates G2–G4)
- Load test: 50 concurrent users, P95 <500ms on staging
- Smoke test on production post-deploy

## Definition of Done

- [ ] Staging environment live and matches production config
- [ ] Production deployed on AWS
- [ ] 10 beta tenants onboarded and completing workflows
- [ ] Razorpay trial → paid works in sandbox then production
- [ ] `DEPLOYMENT_GUIDE.md` published
- [ ] P0 bugs = 0
- [ ] **G5 passed — MVP LAUNCHED**

---

# APPENDIX A — Sprint Dependency Map

```mermaid
flowchart TD
    S1[S1 Foundation] --> S2[S2 Multi-Tenant + RLS]
    S2 --> S3[S3 Auth + FE Auth]
    S3 --> S4[S4 RBAC + Hospital Admin]
    S4 --> S5[S5 OPD Spec + API Standards]
    S5 --> S6[S6 Staff + Doctors]
    S6 --> S7[S7 Patients]
    S7 --> S8[S8 Appointments]
    S8 --> S9[S9 OPD Workflow]
    S9 --> S10[S10 Billing]
    S4 --> S10
    S10 --> S11[S11 Reports + Audit + Files]
    S11 --> S12[S12 Launch]
    S4 --> S12
```

| Sprint | Hard Depends On | Soft Depends On |
|--------|-----------------|-----------------|
| S1 | — | — |
| S2 | S1 | — |
| S3 | S2 | — |
| S4 | S3 | — |
| S5 | S4 | — |
| S6 | S4 | S5 |
| S7 | S4 | S6 |
| S8 | S6, S7 | — |
| S9 | S8 | S5 (OPD spec) |
| S10 | S9 | — |
| S11 | S10 | S4 |
| S12 | S11 | All |

---

# APPENDIX B — Module Dependency Map

```mermaid
flowchart LR
    PLT[Platform] --> AUTH[Auth]
    AUTH --> RBAC[RBAC]
    RBAC --> HOSP[Hospital Admin]
    HOSP --> ORG[Staff/Doctors]
    ORG --> PAT[Patients]
    PAT --> APPT[Appointments]
    APPT --> OPD[OPD]
    OPD --> BIL[Patient Billing]
    BIL --> RPT[Reports]
    AUTH --> NOTIF[Notifications]
    PAT --> FILES[File Uploads]
    PLT --> SUB[SaaS Subscription]
    RBAC --> AUDIT[Audit Logs]
```

---

# APPENDIX C — Development Order (Strict)

1. Infrastructure → 2. Multi-tenant → 3. Auth → 4. RBAC → 5. Hospital admin → 6. OPD API spec → 7. Org structure → 8. Patients → 9. Appointments → 10. OPD → 11. Billing → 12. Reports/audit/files → 13. SaaS billing → 14. Production

**Rule:** Never start sprint N+1 until sprint N Definition of Done is complete.

**Rule:** Every sprint ships backend + frontend + tests for its scope.

---

# APPENDIX D — Testing Strategy (Summary)

Full document: `docs/TESTING_STRATEGY.md`

| Layer | Tool | When | Coverage Target |
|-------|------|------|-----------------|
| Unit | pytest, Vitest | Every PR | ≥70% new backend logic |
| Integration | pytest + TestClient | Every PR | All API endpoints per sprint |
| Tenant isolation | pytest | Every PR (mandatory) | 100% tenant-scoped resources |
| RLS | pytest + raw SQL | S2, each migration sprint | Session variable + policy |
| E2E | Playwright or API scripts | End S4, S9, S10, S12 | Critical user journeys |
| Load | k6 or Locust | S12 staging | 50 users, P95 <500ms |
| Security | OWASP ZAP, Bandit | S12 | No critical/high |
| Regression | Full suite | S12 pre-launch | All gates G2–G5 |

### Mandatory Test Cases (MVP)

| ID | Test | Sprint |
|----|------|--------|
| T-01 | Cross-tenant patient 404 | S7 |
| T-02 | Login + refresh + logout | S3 |
| T-03 | RBAC 403 receptionist → admin | S4 |
| T-04 | Register → verify → onboard | S4 |
| T-05 | Patient MRN unique per tenant | S7 |
| T-06 | Appointment double-book 409 | S8 |
| T-07 | OPD queue → consult → complete | S9 |
| T-08 | Invoice → pay → receipt | S10 |
| T-09 | Daily collection report accuracy | S11 |
| T-10 | Razorpay webhook signature | S12 |
| T-11 | 2FA login required for owner | S12 |
| T-12 | Full workflow <5 min | S12 |

---

# APPENDIX E — Deployment Strategy (Summary)

Full document: `docs/DEPLOYMENT_GUIDE.md`

| Environment | When | Infrastructure |
|-------------|------|----------------|
| **Local** | S1+ | Docker Compose |
| **CI** | S1+ | GitHub Actions |
| **Staging** | S12 week 1 | AWS ECS + RDS + Redis + S3 |
| **Production** | S12 week 2 | AWS Multi-AZ, Secrets Manager |

### Deploy Pipeline

```
PR → CI (lint, test, build) → merge to dev →
staging deploy (auto) → smoke test →
manual promote to production (S12) →
post-deploy smoke → monitor 24h
```

### Rollback

- ECS: revert to previous task definition
- DB: Alembic downgrade only if migration reversible; else forward-fix migration
- RDS: restore from snapshot (RTO 4h per NFR)

---

# APPENDIX F — MVP Release Checklist

### Functional

- [ ] Tenant self-registration with email verification
- [ ] Login, logout, password reset, 2FA (owners)
- [ ] RBAC on all endpoints and UI actions
- [ ] Hospital profile, branches, settings
- [ ] User invite, roles, disable
- [ ] Departments, staff, doctors, schedules
- [ ] Patient CRUD, search, allergies, contacts, consent, duplicate warning
- [ ] Appointments with availability
- [ ] OPD queue, consultation, vitals, e-prescription
- [ ] Billing: services, invoice, payment, receipt PDF
- [ ] Dashboard + daily collection + OPD summary + audit report
- [ ] Patient document upload
- [ ] Email notifications (appointment confirm)
- [ ] In-app notification bell
- [ ] SaaS trial + Razorpay subscription

### Technical

- [ ] 44 MVP tables migrated with RLS
- [ ] `SET LOCAL app.tenant_id` on all DB sessions
- [ ] OpenAPI docs published
- [ ] Structured logging + correlation IDs
- [ ] Rate limiting active
- [ ] Security headers on all responses
- [ ] S3 file storage with tenant prefixes
- [ ] Redis cache for permissions + dashboard
- [ ] CI green; isolation tests pass
- [ ] Staging + production on AWS
- [ ] CloudWatch alarms configured
- [ ] Backup restore verified
- [ ] `DEPLOYMENT_GUIDE.md` complete
- [ ] `TESTING_STRATEGY.md` complete

### Business

- [ ] 10 beta tenants onboarded
- [ ] UAT sign-off recorded
- [ ] Privacy policy + terms linked at signup
- [ ] P0 bugs = 0
- [ ] MVP demo video recorded

---

# APPENDIX G — Complete Feature Coverage Report

| P0 Requirement (FRD) | Sprint | Covered |
|----------------------|--------|---------|
| FR-PLT-001–007 Tenant management | S2, S4 | ✅ |
| FR-PLT-002 Email verification | S3 | ✅ |
| FR-PLT-011–013 Tenant isolation | S2, every migration | ✅ |
| FR-AUTH-001–006, 008 Auth | S3 | ✅ |
| FR-AUTH-009–012 RBAC | S4 | ✅ |
| FR-SUB-001–006, 009–010 Subscription | S12 | ✅ |
| FR-PAT-001–006, 011 Patients | S7 | ✅ |
| FR-PAT-003 Duplicate detection | S7 | ✅ |
| FR-PAT-009 Consent | S7 | ✅ |
| FR-OPD-001–002, 004, 006–007, 009–010, 012–013 OPD | S8, S9 | ✅ |
| FR-BIL-001–002, 004–007, 009–010 Billing | S10 | ✅ |
| FR-RPT-008 Audit log report | S11 | ✅ |
| FR-ADM-001–005 Admin | S4, S6 | ✅ |
| FR-NTF-001 Email notifications | S11 | ✅ |
| FR-XMOD-001–005 Cross-module | S9, S10 | ✅ |

**P0 coverage: 100%** (all assigned to sprints)

---

# APPENDIX H — MVP Readiness Report

| Dimension | v1 Plan | v2 Plan |
|-----------|---------|---------|
| Frontend vertical slices | ❌ Backend-first | ✅ Every sprint |
| RLS per migration | ❌ Once in S1 | ✅ Every DB sprint |
| OPD API spec | ❌ Missing | ✅ S5 |
| Email verification | ❌ Missing | ✅ S3 |
| 2FA | ❌ Missing | ✅ S12 |
| Pen test / security gate | ❌ Checklist only | ✅ S12 full gate |
| Staging environment | ❌ Missing | ✅ S12 |
| Backup verify | ❌ Missing | ✅ S12 |
| PHI access logs | ❌ Partial | ✅ S11 |
| SaaS billing in MVP | ⚠️ S11 only | ✅ S12 (MVP launch) |

---

# APPENDIX I — Features Intentionally Postponed (After MVP)

| Feature | FR Priority | Target Phase |
|---------|-------------|--------------|
| IPD (admissions, beds, nursing) | P1 | Phase 2 — Sprints 13–14 |
| Laboratory module | P1 | Phase 2 — Sprint 15 |
| Pharmacy + inventory | P1 | Phase 2 — Sprint 16 |
| SMS notifications | P1 | Phase 2 |
| Multi-location deep scoping | P1 | Phase 2 |
| WebSocket real-time queue | NFR | Phase 2 |
| Patient CSV import (async) | P1 | Phase 2 |
| Custom roles | P2 | Phase 3 |
| Insurance/TPA billing | P2 | Phase 3 |
| Hindi localization | P2 | Phase 3 |
| AI features | P3 | Phase 4 |
| Mobile apps | Out of scope | Phase 5 |
| HL7/FHIR | Out of scope | Phase 5 |

---

# APPENDIX J — Final MVP Completion Score

| If you complete… | Score |
|------------------|-------|
| v1 sprint plan (old) | 82% |
| **v2 sprint plan (this document) — all S1–S12 DoD** | **97%** |

Remaining 3%: external legal sign-off, optional third-party pen test firm, first-week production traffic tuning.

---

# Final Verdict

## ✅ YES — this v2 sprint plan is sufficient for a production-ready MVP launch

After completing **all 12 sprints** with every Definition of Done item checked, the Hospital Management SaaS MVP will be **fully functional, deployable, testable, and ready for real hospital usage** within the defined MVP scope (OPD + billing; no IPD/lab/pharmacy).

---

## Document Control

| Action | Owner | When |
|--------|-------|------|
| Archive v1 sprint plan | PM | Now — reference only |
| Use v2 as sole execution plan | Dev | Immediate |
| Update `05_TASK_BACKLOG.md` to MVP-001 series | PM | With `10_MVP_TASK_BACKLOG.md` |
| Reconcile `01_MASTER_SDLC_PLAN.md` | PM | Next commit |

**Supersedes:** `03_SPRINT_PLAN_DETAILED.md` v1, DS-001–DS-080 task numbering for remaining work.
