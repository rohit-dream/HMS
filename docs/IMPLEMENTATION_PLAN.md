# Implementation Plan

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Active |
| **Last Updated** | June 2026 |
| **Author** | Solution Architecture |
| **Audience** | Solo full-stack developer |
| **Duration** | 6 months active development + 6 months stabilization |
| **Related Documents** | SPRINT_PLAN.md, SYSTEM_ARCHITECTURE.md, DATABASE_DESIGN.md, API_DESIGN.md, RBAC_DESIGN.md, MULTI_TENANT_DESIGN.md, SECURITY_ARCHITECTURE.md, BILLING_SUBSCRIPTION.md, ROADMAP.md |

---

## Executive Summary

This document is the **practical execution guide** for building the HMS SaaS platform as a **solo full-stack developer**. It synthesizes 17 project documents into a single actionable plan covering development order, backend/frontend roadmaps, infrastructure, and engineering practices.

### Current State

| Asset | Status |
|-------|--------|
| Documentation (`docs/`) | Complete — 17 documents |
| `database/schema.sql` | Implemented — 61 tables, RLS enabled (~2,400 lines) |
| `database/seed-data.sql` | Empty — to be authored Sprint 1 |
| `backend/` | Not started |
| `frontend/` | Not started |

### Solo Developer Constraints

| Constraint | Mitigation |
|------------|------------|
| ~56 net development hours per 2-week sprint | Strict MVP scope; defer P2 items |
| Full-stack context switching | Backend Mon–Wed, Frontend Thu–Fri |
| No code review partner | Self-review checklist; automated tests as safety net |
| Single point of failure | Managed AWS services; comprehensive runbooks |
| Documentation vs. code gaps | OPD/IPD API specs built from RBAC + clinical workflows (see §5) |

### Authoritative References (Conflict Resolution)

When documents disagree, use this precedence:

1. **SECURITY_ARCHITECTURE.md** — security controls
2. **RBAC_DESIGN.md** — roles (`hospital_owner`, `hospital_admin`, `doctor`, etc.)
3. **DATABASE_DESIGN.md** + `schema.sql` — data model
4. **API_DESIGN.md** — API contracts (extend for missing OPD/IPD modules)
5. **BILLING_SUBSCRIPTION.md** — SaaS billing (not hospital patient billing)
6. **SPRINT_PLAN.md** — sprint-level task breakdown

> **Note:** `MULTI_TENANT_DESIGN.md` uses `tenant_admin` / `billing_staff` in examples. Implementation must use **RBAC_DESIGN.md** role codes: `hospital_owner`, `hospital_admin`, `accountant`.

### MVP Scope Boundary

**In scope (Months 1–6):** Platform, auth, RBAC, patients, OPD, billing, IPD, lab, pharmacy, reports, notifications, subscription billing, production launch.

**Out of scope (post-MVP):** All features in `ADVANCED_FEATURES_ROADMAP.md` (Phases 4–9), AI features, white-label, telemedicine, HL7/FHIR.

---

## 1. Development Order

Build in **vertical slices** — each sprint delivers a testable end-to-end capability. Never build all backend APIs before any frontend.

### 1.1 Phase Sequence

```
Phase 1 — MVP Foundation        Months 1–2   Sprints 1–4
Phase 2 — Clinical Depth        Months 3–4   Sprints 5–8
Phase 3 — Growth & Launch       Months 5–6   Sprints 9–12
Stabilization                   Months 7–12  Beta support, bug fixes, ops
```

### 1.2 Module Build Order

| Order | Module | Sprint | Dependency |
|-------|--------|--------|------------|
| 1 | Platform foundation (DB, middleware, CI) | 1 | — |
| 2 | Authentication + RBAC | 2 | 1 |
| 3 | Tenant registration + trial subscription | 2 | 1, 2 |
| 4 | Patients + Staff + Admin | 3 | 2 |
| 5 | Doctors + Appointments | 4 | 3 |
| 6 | OPD (visits, queue, consultation, Rx) | 4 | 3, 5 |
| 7 | Hospital billing (invoices, payments) | 4 | 3, 6 |
| 8 | IPD (wards, beds, admissions) | 5 | 3, 7 |
| 9 | IPD clinical + discharge billing | 6 | 8 |
| 10 | Laboratory | 7 | 3, 7 |
| 11 | Pharmacy + inventory | 8 | 6, 7 |
| 12 | Reports + dashboard | 9 | All clinical |
| 13 | Notifications + multi-location | 10 | 5, 7 |
| 14 | SaaS subscription billing (Razorpay) | 11 | 2 |
| 15 | Production launch + onboarding wizard | 12 | All |

### 1.3 Weekly Rhythm (Solo Developer)

| Day | Focus |
|-----|-------|
| Monday | Backend: models, repositories, service logic |
| Tuesday | Backend: API routes, tests, OpenAPI |
| Wednesday | Backend: integration tests, bug fixes, deploy to staging |
| Thursday | Frontend: pages, forms, API integration |
| Friday | Frontend: polish, E2E smoke test, sprint review, planning |

### 1.4 Decision Gates

| Gate | When | Go Criteria |
|------|------|-------------|
| G1 — Start coding | Before Sprint 1 | `schema.sql` reviewed; Docker Compose runs |
| G2 — MVP demo | End Sprint 4 | Register → patient → OPD → bill → pay works on staging |
| G3 — Clinical suite | End Sprint 8 | IPD + lab + pharmacy E2E on staging |
| G4 — Monetization | End Sprint 11 | Razorpay trial → paid conversion works |
| G5 — Production | End Sprint 12 | 10 beta tenants; pen test; isolation tests pass |

---

## 2. Backend Development Roadmap

**Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic v2, Alembic, pytest.

**Architecture:** Modular monolith — single FastAPI app with domain routers. Background jobs via **SQS worker** (not Celery).

### 2.1 Sprint-by-Sprint Backend Deliverables

#### Sprint 1 — Foundation (Week 1–2)

| Deliverable | Reference |
|-------------|-----------|
| FastAPI project scaffold with layered structure | API_DESIGN.md §2.6 |
| SQLAlchemy models for `platform` + `core` schemas | DATABASE_DESIGN.md |
| Tenant middleware: JWT `tenant_id` → `SET LOCAL app.tenant_id` | MULTI_TENANT_DESIGN.md §7 |
| Standard response envelope + exception handlers | API_DESIGN.md §2.3 |
| Correlation ID middleware + structured JSON logging | SYSTEM_ARCHITECTURE.md §9 |
| Health endpoints: `GET /health`, `GET /ready` | — |
| Alembic baseline migration from `schema.sql` | §4 below |
| Seed script: system tenant, plans, permissions | BILLING_SUBSCRIPTION.md §2 |

#### Sprint 2 — Auth & RBAC (Week 3–4)

| Deliverable | Reference |
|-------------|-----------|
| JWT RS256: access token (30 min), refresh in HttpOnly cookie | SECURITY_ARCHITECTURE.md §5 |
| Auth module: register, login, logout, refresh, forgot/reset password | API_DESIGN.md §3 |
| Tenant provisioning: `platform.create_tenant()` + trial subscription | MULTI_TENANT_DESIGN.md §3 |
| Permission resolver (Redis-cached; roles in JWT, permissions server-side) | SECURITY_ARCHITECTURE.md §6 |
| `@requires_permission()` decorator | RBAC_DESIGN.md §5 |
| Subscription status middleware (trial/active/suspended gate) | BILLING_SUBSCRIPTION.md §4 |
| Role seeding on tenant provisioning (clone from system tenant) | RBAC_DESIGN.md §2 |
| Audit log writes for auth events | SECURITY_ARCHITECTURE.md §11 |
| Email adapter (AWS SES) for verification + password reset | — |

#### Sprint 3 — Patients & Admin (Week 5–6)

| Deliverable | Reference |
|-------------|-----------|
| Patient CRUD + search + allergies + contacts | API_DESIGN.md §4 |
| MRN auto-generation per tenant | FUNCTIONAL_REQUIREMENTS.md FR-PAT-002 |
| Duplicate patient warning (phone match) | FR-PAT-003 |
| Staff + departments + doctors API | API_DESIGN.md §5, §11 |
| Tenant settings (organization profile) | MULTI_TENANT_DESIGN.md §4 |
| Trial patient limit enforcement (402) | BILLING_SUBSCRIPTION.md §9 |
| PHI access logging on patient reads | SECURITY_ARCHITECTURE.md §11.3 |

#### Sprint 4 — OPD & Billing (Week 7–8)

| Deliverable | Reference |
|-------------|-----------|
| Appointments CRUD + availability | API_DESIGN.md §6 |
| OPD visits + queue (token management) | RBAC_DESIGN.md §4.3; design during sprint |
| Consultation: vitals, clinical notes, e-prescription | FUNCTIONAL_REQUIREMENTS.md §OPD |
| Billing: service master, invoices, finalize, void, payments | API_DESIGN.md §7 |
| PDF generation: invoice + receipt (async SQS job → S3) | SYSTEM_ARCHITECTURE.md ADR |
| Daily collection report | API_DESIGN.md §7.7 |
| Seed default billing services on tenant onboarding | SPRINT_PLAN.md Sprint 4 |

> **Gap:** OPD visit/queue/consultation endpoints are not in API_DESIGN.md. Define OpenAPI spec at start of Sprint 4 using RBAC permissions (`opd:consult`, `opd:prescribe`) and DATABASE_DESIGN clinical tables.

#### Sprint 5 — IPD Foundation (Week 9–10)

| Deliverable | Reference |
|-------------|-----------|
| Wards / rooms / beds CRUD | DATABASE_DESIGN.md §2.2.5 |
| Bed availability dashboard aggregation | — |
| Admissions: create, list, status transitions | RBAC: `ipd:admit` |
| Bed plan limit enforcement | BILLING_SUBSCRIPTION.md §9 |
| Admission number sequence per tenant | — |

#### Sprint 6 — IPD Clinical (Week 11–12)

| Deliverable | Reference |
|-------------|-----------|
| Nursing notes + IPD vitals API | DATABASE_DESIGN.md |
| Discharge summary + discharge workflow | RBAC: `ipd:discharge` |
| IPD daily charges accrual (manual trigger for MVP) | — |
| IPD final invoice from accrued charges | — |
| Discharge PDF (async worker) | — |

#### Sprint 7 — Laboratory (Week 13–14)

| Deliverable | Reference |
|-------------|-----------|
| Lab test catalog, orders, samples, results | API_DESIGN.md §10 |
| Critical value flag + in-app notification | — |
| Lab report PDF finalize | RBAC: `lab:report` |
| Lab charges → invoice line item | — |

#### Sprint 8 — Pharmacy (Week 15–16)

| Deliverable | Reference |
|-------------|-----------|
| Medicines CRUD, pending Rx queue, dispense | API_DESIGN.md §8 |
| Inventory: stock-in, adjust, movements ledger | API_DESIGN.md §9 |
| Low-stock + expiring alerts | — |
| Pharmacy charges → invoice line item | — |

#### Sprint 9 — Reports (Week 17–18)

| Deliverable | Reference |
|-------------|-----------|
| Dashboard stats API (Redis cache, 2-min TTL) | — |
| OPD, IPD, lab, pharmacy, financial reports | RBAC: `reports:clinical`, `reports:financial` |
| CSV + PDF export (async) | — |

#### Sprint 10 — Notifications (Week 19–20)

| Deliverable | Reference |
|-------------|-----------|
| In-app notifications CRUD | DATABASE_DESIGN comms schema |
| SQS worker: email (SES) + SMS (MSG91) | — |
| Scheduled appointment reminder job | — |
| Tenant locations (branches) CRUD + location scoping | MULTI_TENANT_DESIGN.md |

#### Sprint 11 — SaaS Billing & Security (Week 21–22)

| Deliverable | Reference |
|-------------|-----------|
| Razorpay: customer, payment method, charge, webhooks | BILLING_SUBSCRIPTION.md §5 |
| Plan upgrade/downgrade + proration | BILLING_SUBSCRIPTION.md §7 |
| Dunning + suspension flow | BILLING_SUBSCRIPTION.md §8 |
| Usage metering API (users, beds, patients) | BILLING_SUBSCRIPTION.md §9.4 |
| Audit log list API | SECURITY_ARCHITECTURE.md §11 |
| Rate limiting (Redis) | SECURITY_ARCHITECTURE.md §9 |
| Patient CSV import (async SQS job) | API_DESIGN.md §4.8 |
| TOTP 2FA for `hospital_owner` / `hospital_admin` | SECURITY_ARCHITECTURE.md §5.6 |

#### Sprint 12 — Production (Week 23–24)

| Deliverable | Reference |
|-------------|-----------|
| Production config via Secrets Manager | SECURITY_ARCHITECTURE.md §14 |
| Sentry + CloudWatch integration | SYSTEM_ARCHITECTURE.md |
| Onboarding progress API | MULTI_TENANT_DESIGN.md §4.2 |
| Bug fix buffer | — |

### 2.2 Backend Layer Responsibilities

| Layer | Responsibility | Rule |
|-------|----------------|------|
| **Router** (`api/v1/`) | HTTP handling, Pydantic validation, call service | No business logic; no direct DB |
| **Service** (`services/`) | Business rules, orchestration, permission checks | Calls repositories only |
| **Repository** (`repositories/`) | Tenant-scoped queries, `tenant_id` filter | Every query includes `tenant_id` |
| **Model** (`models/`) | SQLAlchemy ORM mapping | Maps 1:1 to `schema.sql` |
| **Schema** (`schemas/`) | Pydantic request/response DTOs | Separate from ORM models |
| **Worker** (`worker/`) | SQS job handlers (email, PDF, import, billing) | Sets `tenant_id` per job |

### 2.3 Middleware Stack (Request Order)

```
1. Correlation ID
2. CORS
3. Security headers
4. Rate limiting
5. JWT authentication (optional per route)
6. Tenant context resolution
7. Subscription status gate
8. RBAC permission check
9. Audit log (on mutation)
```

---

## 3. Frontend Development Roadmap

**Stack:** React 18, TypeScript, Vite, TailwindCSS, React Router v6, TanStack Query, Zod, React Hook Form.

**Principle:** Build UI one sprint behind backend API availability. Use mock data only in Sprint 1.

### 3.1 Sprint-by-Sprint Frontend Deliverables

| Sprint | Screens | Routes |
|--------|---------|--------|
| **1** | App shell, layout, sidebar, design tokens, API client | `/` |
| **2** | Login, registration wizard, password reset, protected routes, auth context | `/login`, `/register`, `/reset-password` |
| **3** | Patient list/search, registration form, profile, departments, staff list, org settings | `/patients/*`, `/admin/departments`, `/admin/staff`, `/admin/settings` |
| **4** | Appointment calendar, OPD queue board, consultation screen, billing (invoice + payment), role dashboards | `/opd/*`, `/billing/*`, `/dashboard` |
| **5** | Ward/bed management, bed dashboard, admission form, admitted patients list | `/ipd/wards`, `/ipd/admissions` |
| **6** | Nursing vitals chart, nursing notes, discharge form, running IPD bill | `/ipd/patients/:id` |
| **7** | Lab catalog, order queue, sample collection, result entry, report view | `/lab/*` |
| **8** | Medicine master, Rx queue, dispense form, inventory list, stock-in | `/pharmacy/*` |
| **9** | Admin dashboard (charts), reports page with filters + export | `/dashboard`, `/reports` |
| **10** | Notification bell, preferences, branch selector, branch admin | `/notifications`, `/admin/branches` |
| **11** | Subscription page, Razorpay checkout, usage widget, audit log viewer, CSV import | `/admin/subscription`, `/admin/audit` |
| **12** | Onboarding wizard (5 steps), production optimizations (lazy routes, code splitting) | `/onboarding` |

### 3.2 Frontend Architecture

| Concern | Approach |
|---------|----------|
| State — server | TanStack Query (cache, refetch, mutations) |
| State — client | React Context for auth, tenant, location |
| Forms | React Hook Form + Zod resolver |
| API calls | Centralized `apiClient` with interceptors (token, 401 refresh, error toast) |
| RBAC UI | `<PermissionGuard permission="patient:create">` component |
| Routing | Role-based dashboard redirect after login |
| Styling | TailwindCSS utility classes; shared component library in `components/ui/` |
| Responsive | Desktop-first (≥ 1024px); tablet acceptable; mobile post-MVP |

### 3.3 Role-Based Navigation

| Role | Default Landing | Visible Modules |
|------|-----------------|-----------------|
| `hospital_owner` | Dashboard | All |
| `hospital_admin` | Dashboard | All except subscription |
| `doctor` | OPD queue / today's appointments | OPD, IPD (clinical), patients (read) |
| `receptionist` | OPD queue | Patients, appointments, OPD queue |
| `nurse` | IPD admitted patients | IPD (vitals, notes) |
| `accountant` | Billing / daily collection | Billing, reports (financial) |
| `pharmacist` | Pharmacy queue | Pharmacy, inventory |
| `lab_technician` | Lab order queue | Laboratory |

---

## 4. Database Migration Strategy

### 4.1 Starting Point

`database/schema.sql` is the **authoritative initial schema** (61 tables, 8 schemas, RLS policies). Do not rewrite — baseline from it.

### 4.2 Alembic Workflow

| Step | Action |
|------|--------|
| 1 | Sprint 1 Day 1: `alembic init` in `backend/` |
| 2 | Generate baseline: `alembic revision --autogenerate -m "baseline"` from existing `schema.sql` |
| 3 | Mark baseline as applied: `alembic stamp head` on existing databases |
| 4 | All future changes: new Alembic revision per sprint (never edit baseline) |
| 5 | CI: `alembic upgrade head` on test DB before pytest |

### 4.3 Migration Rules

| Rule | Rationale |
|------|-----------|
| One migration per logical change | Easier rollback and review |
| Never modify a migration already deployed to staging | Create a new revision instead |
| Include RLS policies in migrations for new tables | MULTI_TENANT_DESIGN.md §8 |
| Include `tenant_id` + composite FKs on new tables | Isolation guarantee |
| Test migrations up AND down locally | Catch destructive changes |
| Seed data in separate `seed/` scripts, not migrations | Idempotent seeding |

### 4.4 Planned Migrations (Post-Baseline)

| Sprint | Migration | Tables / Changes |
|--------|-----------|------------------|
| 2 | `002_auth_seed_roles` | Seed permissions, system roles |
| 3 | `003_patient_search_indexes` | `pg_trgm` on patient name/phone |
| 4 | `004_opd_billing_sequences` | Invoice/visit number sequences |
| 10 | `005_location_id_columns` | Add `location_id` to visits, admissions, invoices |
| 11 | `006_subscription_billing_tables` | `subscription_invoices`, `payment_methods`, `dunning_attempts` per BILLING_SUBSCRIPTION.md |
| 11 | `007_phi_access_logs` | `audit.phi_access_logs` per SECURITY_ARCHITECTURE.md |

### 4.5 Deferred (Post-MVP)

| Item | Trigger |
|------|---------|
| Table partitioning (`audit_logs`, `opd_visits`) | 50+ tenants |
| `audit.ai_invocations` | AI features (ADVANCED_FEATURES_ROADMAP Phase 7) |
| Field-level encryption columns | Phase 2 security hardening |
| Read replica routing | Report performance degradation |

### 4.6 Environment Database Setup

| Environment | Setup Command |
|-------------|---------------|
| Local | `docker compose up postgres` → `alembic upgrade head` → `python -m scripts.seed` |
| Staging | CI/CD pipeline runs `alembic upgrade head` on deploy |
| Production | Manual approval gate → `alembic upgrade head` with backup snapshot first |

---

## 5. API Development Sequence

### 5.1 Module Build Order

Build APIs in this sequence (matches §1.2). Complete OpenAPI spec for each module before coding.

| Phase | Module | Base Path | Endpoints (approx.) | Sprint |
|-------|--------|-----------|---------------------|--------|
| 1 | Health | `/health` | 2 | 1 |
| 2 | Auth | `/api/v1/auth` | 8 | 2 |
| 3 | Patients | `/api/v1/patients` | 8 | 3 |
| 4 | Doctors | `/api/v1/doctors` | 5 | 3 |
| 5 | Staff | `/api/v1/staff` | 6 | 3 |
| 6 | Appointments | `/api/v1/appointments` | 5 | 4 |
| 7 | OPD | `/api/v1/opd` | 8–10 | 4 |
| 8 | Billing | `/api/v1/billing` | 10 | 4 |
| 9 | IPD | `/api/v1/ipd` | 12–15 | 5–6 |
| 10 | Laboratory | `/api/v1/laboratory` | 10 | 7 |
| 11 | Pharmacy | `/api/v1/pharmacy` | 8 | 8 |
| 12 | Inventory | `/api/v1/inventory` | 6 | 8 |
| 13 | Reports | `/api/v1/reports` | 6 | 9 |
| 14 | Notifications | `/api/v1/notifications` | 5 | 10 |
| 15 | Locations | `/api/v1/locations` | 4 | 10 |
| 16 | Subscription | `/api/v1/subscription` | 12 | 11 |
| 17 | Webhooks | `/api/v1/webhooks` | 1 | 11 |
| 18 | Audit | `/api/v1/audit` | 2 | 11 |

### 5.2 OPD / IPD API Specification (Sprint 4–5 Gap Fill)

These endpoints are required by RBAC but missing from API_DESIGN.md. Define and implement using this sequence:

**OPD (Sprint 4):**

| Method | Endpoint | Permission |
|--------|----------|------------|
| POST | `/opd/visits` | `opd:create` |
| GET | `/opd/visits` | `opd:read` |
| GET | `/opd/visits/{id}` | `opd:read` |
| POST | `/opd/visits/{id}/vitals` | `opd:consult` |
| POST | `/opd/visits/{id}/notes` | `opd:consult` |
| POST | `/opd/visits/{id}/prescriptions` | `opd:prescribe` |
| GET | `/opd/queue` | `opd:read` |
| POST | `/opd/queue` | `opd:create` |
| PATCH | `/opd/queue/{id}` | `opd:update` |

**IPD (Sprint 5–6):**

| Method | Endpoint | Permission |
|--------|----------|------------|
| CRUD | `/ipd/wards`, `/ipd/rooms`, `/ipd/beds` | `ipd:read`, `admin:settings` |
| GET | `/ipd/beds/availability` | `ipd:read` |
| POST | `/ipd/admissions` | `ipd:admit` |
| GET/PATCH | `/ipd/admissions/{id}` | `ipd:read`, `ipd:discharge` |
| POST | `/ipd/admissions/{id}/vitals` | `ipd:update` |
| POST | `/ipd/admissions/{id}/nursing-notes` | `ipd:update` |
| POST | `/ipd/admissions/{id}/discharge` | `ipd:discharge` |

### 5.3 API Conventions (Mandatory)

| Convention | Standard |
|------------|----------|
| Versioning | `/api/v1/` URL prefix |
| Response envelope | `{ data, meta, errors }` per API_DESIGN.md §2.3 |
| Pagination | `?page=1&page_size=20` → `meta.pagination` |
| Errors | `{ error_code, message, details[] }` |
| Idempotency | `X-Idempotency-Key` on POST (payments, registrations) |
| Tenant scope | `tenant_id` from JWT only |
| Soft delete | `DELETE` sets `deleted_at`; never hard delete clinical data |
| OpenAPI | Auto-generated at `/api/v1/docs`; keep in sync |

---

## 6. Authentication Strategy

> Full specification: **SECURITY_ARCHITECTURE.md §5**

### 6.1 Token Strategy

| Token | Storage | TTL | Contents |
|-------|---------|-----|----------|
| Access token | Memory (JS variable) | 30 minutes | `sub`, `tenant_id`, `roles`, `jti` |
| Refresh token | HttpOnly Secure cookie | 7 days | Opaque ID → Redis session |

**Critical:** Do **not** put permissions in JWT. Resolve server-side with Redis cache (5-min TTL, invalidate on role change).

### 6.2 Login Flow

```
1. User submits email + password on {subdomain}.platform.com
2. Backend resolves tenant from subdomain (or Host header)
3. Verify password (bcrypt), check lockout, check tenant status
4. Issue access token (JSON body) + refresh token (Set-Cookie)
5. Frontend stores access token in memory; React Query handles API calls
6. On 401: call POST /auth/refresh (cookie sent automatically) → new access token
7. On refresh failure: redirect to /login
```

### 6.3 Registration Flow

```
1. POST /auth/register with org details + plan_code + X-Idempotency-Key
2. Backend: create tenant, trial subscription (14 days), clone roles, create admin user
3. Send verification email (async)
4. Return tenant_id + trial_ends_at
5. Redirect to login → onboarding wizard (Sprint 12)
```

### 6.4 Session Security Checklist

- [ ] RS256 signing key in AWS Secrets Manager (not HS256)
- [ ] Refresh token rotation on every refresh
- [ ] All sessions invalidated on password change
- [ ] Account lockout after 5 failed attempts (15-min lock)
- [ ] Rate limit: 10 login attempts/minute/IP
- [ ] CAPTCHA on registration (Sprint 11)
- [ ] 2FA for `hospital_owner` / `hospital_admin` (Sprint 11)

---

## 7. Multi-Tenant Implementation Strategy

> Full specification: **MULTI_TENANT_DESIGN.md**

### 7.1 Three-Layer Isolation

| Layer | Implementation | Sprint |
|-------|----------------|--------|
| **Application** | Repository mixin auto-filters `tenant_id` | 1 |
| **Session** | `SET LOCAL app.tenant_id = '{uuid}'` per request | 1 |
| **Database** | RLS policies on all 61 tables (already in schema.sql) | 1 |

### 7.2 Tenant Context Lifecycle

```
Request → JWT decoded → tenant_id extracted
       → Subscription status checked
       → SET LOCAL app.tenant_id
       → All repository queries scoped
       → Response returned
       → Session closed (RESET app.tenant_id)
```

### 7.3 Implementation Checklist (Every New Feature)

- [ ] Table has `tenant_id UUID NOT NULL`
- [ ] Composite FKs include `tenant_id`
- [ ] RLS policies: SELECT, INSERT, UPDATE, DELETE
- [ ] Repository methods filter by `tenant_id`
- [ ] API uses JWT `tenant_id` (never client-supplied)
- [ ] Cache keys prefixed: `tenant:{id}:...`
- [ ] S3 paths: `tenants/{tenant_id}/...`
- [ ] SQS jobs include `tenant_id` in payload
- [ ] Cross-tenant isolation test added

### 7.4 System Tenant Reads

Platform seed data (`subscription_plans`, `permissions`) lives under system tenant UUID `00000000-0000-0000-0000-000000000001`. RLS policy must allow read of system tenant rows by all tenants:

```sql
-- Conceptual: allow SELECT on system tenant seed data
USING (
  tenant_id = current_setting('app.tenant_id')::uuid
  OR tenant_id = '00000000-0000-0000-0000-000000000001'
)
```

Apply to `subscription_plans` and `permissions` tables only.

### 7.5 SQS Worker Tenant Context

Every background job message must include `tenant_id`. Worker sets DB context before any query:

```
Message: { "job_type": "send_reminder", "tenant_id": "...", "payload": {...} }
Worker: SET LOCAL app.tenant_id → execute → RESET
```

Never reuse DB connections across tenants without resetting context.

---

## 8. RBAC Implementation Strategy

> Full specification: **RBAC_DESIGN.md**

### 8.1 Role Catalog (MVP)

| Role Code | Display Name | Sprint Introduced |
|-----------|--------------|-------------------|
| `hospital_owner` | Hospital Owner | 2 (registration) |
| `hospital_admin` | Hospital Admin | 3 (staff invite) |
| `doctor` | Doctor | 3 |
| `receptionist` | Receptionist | 3 |
| `nurse` | Nurse | 5 |
| `accountant` | Accountant | 4 |
| `pharmacist` | Pharmacist | 8 |
| `lab_technician` | Lab Technician | 7 |

Platform admin is a separate auth realm — not part of tenant RBAC.

### 8.2 Permission Format

```
{module}:{action}

Examples: patient:read, opd:consult, billing:void, admin:subscription
```

### 8.3 Implementation Steps

| Step | Sprint | Task |
|------|--------|------|
| 1 | 1 | Seed `core.permissions` catalog (system tenant) |
| 2 | 2 | Seed role → permission mappings for all 8 roles |
| 3 | 2 | Build `PermissionResolver` (DB + Redis cache) |
| 4 | 2 | Build `@requires_permission("patient:read")` FastAPI dependency |
| 5 | 2 | Clone roles on tenant provisioning |
| 6 | 3+ | Apply decorator to every protected endpoint |
| 7 | 3 | Build frontend `<PermissionGuard>` component |
| 8 | 4 | Role-based sidebar navigation |
| 9 | 11 | Audit log for permission denials |

### 8.4 Permission Resolution (Not in JWT)

```python
# Pseudocode — illustrative only
async def get_user_permissions(user_id: UUID, tenant_id: UUID) -> set[str]:
    cache_key = f"tenant:{tenant_id}:permissions:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    permissions = await db.query(
        # JOIN user_roles → role_permissions → permissions
    )
    await redis.set(cache_key, json.dumps(permissions), ex=300)
    return permissions
```

Invalidate cache on: role assignment change, role permission change, user deactivation.

### 8.5 MVP Permission Minimum per Module

| Module | Permissions Needed |
|--------|-------------------|
| Patients | `read`, `create`, `update`, `delete`, `import` |
| OPD | `read`, `create`, `consult`, `prescribe` |
| IPD | `read`, `admit`, `update`, `discharge` |
| Billing | `read`, `create`, `collect`, `void` |
| Laboratory | `read`, `create`, `verify`, `report` |
| Pharmacy | `read`, `dispense` |
| Admin | `users`, `settings`, `subscription` |
| Reports | `clinical`, `financial` |
| Audit | `read` |

---

## 9. Folder Structure

### 9.1 Monorepo Layout

```
hospital-management-saas/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py          # Aggregates all routers
│   │   │       ├── auth.py
│   │   │       ├── patients.py
│   │   │       ├── doctors.py
│   │   │       ├── staff.py
│   │   │       ├── appointments.py
│   │   │       ├── opd.py
│   │   │       ├── ipd.py
│   │   │       ├── billing.py
│   │   │       ├── laboratory.py
│   │   │       ├── pharmacy.py
│   │   │       ├── inventory.py
│   │   │       ├── reports.py
│   │   │       ├── notifications.py
│   │   │       ├── subscription.py
│   │   │       ├── audit.py
│   │   │       └── webhooks.py
│   │   ├── core/
│   │   │   ├── config.py              # Settings from env
│   │   │   ├── security.py            # JWT, password hashing
│   │   │   ├── dependencies.py        # get_db, get_current_user
│   │   │   ├── middleware.py          # Tenant, correlation, rate limit
│   │   │   ├── exceptions.py          # Custom exception classes
│   │   │   └── permissions.py         # @requires_permission
│   │   ├── models/                    # SQLAlchemy ORM (by schema)
│   │   │   ├── platform.py
│   │   │   ├── core.py
│   │   │   ├── clinical.py
│   │   │   ├── billing.py
│   │   │   ├── pharmacy.py
│   │   │   ├── laboratory.py
│   │   │   ├── comms.py
│   │   │   └── audit.py
│   │   ├── schemas/                   # Pydantic DTOs (by domain)
│   │   ├── services/                  # Business logic (by domain)
│   │   ├── repositories/              # Data access (by domain)
│   │   └── adapters/                  # External: SES, S3, SQS, Razorpay, MSG91
│   ├── worker/
│   │   ├── main.py                    # SQS consumer loop
│   │   └── handlers/                  # email, pdf, import, billing, reminders
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py                # DB fixtures, test tenant
│   ├── scripts/
│   │   └── seed.py                    # Dev seed data
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                       # API client, endpoints by module
│   │   ├── components/
│   │   │   ├── ui/                    # Button, Input, Table, Modal, Toast
│   │   │   └── layout/               # Sidebar, Header, PageShell
│   │   ├── features/                  # Feature modules (mirror backend)
│   │   │   ├── auth/
│   │   │   ├── patients/
│   │   │   ├── opd/
│   │   │   ├── ipd/
│   │   │   ├── billing/
│   │   │   ├── laboratory/
│   │   │   ├── pharmacy/
│   │   │   ├── admin/
│   │   │   ├── reports/
│   │   │   └── subscription/
│   │   ├── hooks/                     # useAuth, usePermissions, useTenant
│   │   ├── contexts/                  # AuthContext, TenantContext
│   │   ├── routes/                    # Route definitions + guards
│   │   ├── lib/                       # utils, constants, formatters
│   │   └── types/                     # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── Dockerfile
│
├── database/
│   ├── schema.sql                     # Authoritative baseline
│   └── seed-data.sql
│
├── infrastructure/
│   └── terraform/                     # AWS: ECS, RDS, S3, Redis, SQS
│
├── docker-compose.yml                 # Local: api + worker + postgres + redis
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Lint + test on PR
│       └── deploy-staging.yml
└── docs/                              # Project documentation
```

### 9.2 Module Boundary Rules

| Rule | Description |
|------|-------------|
| Features import from `components/ui/` and `lib/` only | No cross-feature imports |
| Backend services do not import from `api/` | Dependency flows inward |
| Shared types in `schemas/` (backend) and `types/` (frontend) | Keep DTOs separate from ORM |
| External integrations only in `adapters/` | Swappable for testing |

---

## 10. Coding Standards

### 10.1 Python (Backend)

| Standard | Rule |
|----------|------|
| Style | PEP 8; enforced by `ruff` |
| Type hints | Required on all function signatures |
| Async | `async def` for route handlers and I/O; sync for pure logic |
| Naming | `snake_case` functions/variables; `PascalCase` classes |
| Imports | Absolute imports from `app.` |
| Docstrings | Required on services and public repository methods |
| Error handling | Raise domain exceptions; catch in middleware → HTTP response |
| SQL | No raw SQL in routes; repositories only; always parameterized |
| Secrets | Never hardcode; use `settings` from env / Secrets Manager |

### 10.2 TypeScript (Frontend)

| Standard | Rule |
|----------|------|
| Style | ESLint + Prettier |
| Components | Functional components only; no class components |
| Naming | `PascalCase` components; `camelCase` functions/variables |
| Files | `PascalCase.tsx` for components; `camelCase.ts` for utilities |
| Props | Typed interfaces; no `any` |
| API types | Generate from OpenAPI (optional Sprint 9+) or manual in `types/` |
| State | TanStack Query for server state; Context for auth only |

### 10.3 SQL / Database

| Standard | Rule |
|----------|------|
| Naming | `snake_case` tables and columns |
| Primary keys | UUID v4 (consider v7 for high-insert tables later) |
| Timestamps | `TIMESTAMPTZ` (UTC) |
| Soft delete | `deleted_at IS NULL` filter in all queries |
| Migrations | Descriptive names: `003_add_phi_access_logs` |

### 10.4 API Design

| Standard | Rule |
|----------|------|
| Nouns | `/patients`, not `/getPatients` |
| HTTP verbs | GET read, POST create, PUT/PATCH update, DELETE soft-delete |
| Status codes | 201 create, 204 delete, 404 not found (not 403 for IDOR), 402 plan limit |
| Pagination | Always on list endpoints |
| Validation | Pydantic server-side; Zod client-side |

### 10.5 Git Commit Messages

```
type(scope): short description

feat(auth): add JWT refresh token rotation
fix(billing): correct GST calculation on proration
test(patients): add cross-tenant isolation test
chore(ci): add ruff linting to pipeline
```

Types: `feat`, `fix`, `test`, `chore`, `docs`, `refactor`.

---

## 11. Git Workflow

### 11.1 Branch Strategy (Solo Developer)

```
main          ← production-ready; always deployable
  └── dev     ← integration branch; daily work merges here
        └── feature/sprint-N-description   ← optional short-lived branches
```

| Branch | Purpose | Merge To |
|--------|---------|----------|
| `main` | Production releases only | — |
| `dev` | Active development integration | `main` (end of each sprint) |
| `feature/*` | Optional for risky changes | `dev` |

### 11.2 Daily Workflow

```
1. git checkout dev && git pull
2. Create feature branch if needed (or work directly on dev)
3. Implement + test locally
4. git add → git commit (conventional message)
5. git push origin dev
6. CI runs lint + tests automatically
7. Merge to main at sprint end after staging smoke test
```

### 11.3 Sprint Release Workflow

```
End of sprint:
1. Full regression on staging
2. Merge dev → main
3. Tag: git tag v0.4.0-mvp (semantic versioning)
4. CI deploys main to staging automatically
5. Manual promote to production (Sprint 12 only initially)
```

### 11.4 Self-Review Checklist (Before Every Merge)

- [ ] `tenant_id` filter on all new queries
- [ ] RBAC permission decorator on new endpoints
- [ ] Pydantic validation on request bodies
- [ ] Unit test for business logic
- [ ] Integration test for tenant isolation (if new endpoint)
- [ ] No secrets in code
- [ ] OpenAPI docs updated
- [ ] No `console.log` / `print` debugging left

### 11.5 What Not to Do

- No force push to `main`
- No committing `.env` files
- No large PRs spanning multiple modules (keep commits focused)
- No skipping CI checks

---

## 12. Environment Setup

### 12.1 Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20 LTS |
| Docker + Docker Compose | Latest |
| PostgreSQL client (`psql`) | 14+ |
| Git | Latest |
| AWS CLI | v2 (for staging/prod deploy) |

### 12.2 Local Development Setup

```bash
# 1. Clone repository
git clone <repo-url> && cd hospital-management-saas

# 2. Start infrastructure
docker compose up -d postgres redis

# 3. Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env.local       # Edit with local values
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --port 8000

# 4. Frontend setup (separate terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev                      # http://localhost:5173

# 5. Worker (separate terminal, when needed)
cd backend
python -m worker.main
```

### 12.3 Environment Variables

**Backend (`backend/.env.local`):**

| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://hms:hms@localhost:5432/hms_dev` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `JWT_PRIVATE_KEY_PATH` | `./keys/private.pem` | RS256 private key |
| `JWT_PUBLIC_KEY_PATH` | `./keys/public.pem` | RS256 public key |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `AWS_REGION` | `ap-south-1` | AWS region |
| `S3_BUCKET` | `hms-dev-files` | File storage bucket |
| `SQS_QUEUE_URL` | `http://localhost:4566/...` | Job queue (LocalStack in dev) |
| `SES_FROM_EMAIL` | `noreply@platform.com` | Email sender |
| `RAZORPAY_KEY_ID` | `rzp_test_...` | Razorpay test key (Sprint 11) |
| `RAZORPAY_KEY_SECRET` | `...` | Razorpay test secret |
| `RAZORPAY_WEBHOOK_SECRET` | `...` | Webhook signature secret |

**Frontend (`frontend/.env.local`):**

| Variable | Example | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Backend API URL |
| `VITE_RAZORPAY_KEY_ID` | `rzp_test_...` | Razorpay public key (Sprint 11) |

### 12.4 Docker Compose Services (Local)

| Service | Port | Image |
|---------|------|-------|
| `postgres` | 5432 | `postgres:14` |
| `redis` | 6379 | `redis:7-alpine` |
| `api` | 8000 | Built from `backend/Dockerfile` |
| `worker` | — | Same image, different command |
| `frontend` | 5173 | Built from `frontend/Dockerfile` (optional) |

### 12.5 Environment Progression

| Environment | URL | Database | Purpose |
|-------------|-----|----------|---------|
| Local | `localhost:5173` | Docker PostgreSQL | Daily development |
| Staging | `{tenant}.staging.platform.com` | RDS (small) | Integration testing, demos |
| Production | `{tenant}.platform.com` | RDS Multi-AZ | Live tenants (Sprint 12+) |

---

## 13. Testing Strategy

### 13.1 Test Pyramid

```
        ╱  E2E (few)  ╲          Playwright / manual UAT
       ╱ Integration   ╲         API tests with test DB
      ╱   Unit (many)   ╲       pytest / Vitest
```

| Layer | Tool | Coverage Target | When |
|-------|------|-----------------|------|
| Unit | pytest, Vitest | ≥ 80% on services | Every sprint |
| Integration | pytest + test DB | All API endpoints | Every sprint |
| Isolation | pytest (mandatory) | 100% of tenant endpoints | Sprint 1+ |
| E2E | Manual script → Playwright | Critical paths | Sprint 4, 8, 12 |
| Load | k6 / Locust | 50 concurrent users | Sprint 12 |

### 13.2 Mandatory Test Categories

#### Cross-Tenant Isolation (Every Sprint)

```python
# Required pattern for every new tenant-scoped endpoint
def test_tenant_a_data_invisible_to_tenant_b(client, token_a, token_b, resource_in_a):
    response = client.get(f"/api/v1/resource/{resource_in_a.id}",
                          headers=auth(token_b))
    assert response.status_code == 404
```

#### RBAC (Sprint 2+)

```python
def test_receptionist_cannot_void_invoice(client, receptionist_token, invoice_id):
    response = client.post(f"/api/v1/billing/invoices/{invoice_id}/void",
                           headers=auth(receptionist_token))
    assert response.status_code == 403
```

#### Plan Limits (Sprint 11)

```python
def test_trial_patient_limit_blocks_registration(client, trial_token):
    # Create 100 patients, then assert 101st returns 402
    ...
```

### 13.3 Test Database Setup

| Concern | Approach |
|---------|----------|
| Test DB | Separate `hms_test` database; recreated per test session |
| Fixtures | `conftest.py`: create 2 test tenants (A, B) with users per role |
| RLS | Isolation tests verify RLS directly via `SET LOCAL app.tenant_id` |
| Cleanup | Transaction rollback per test (pytest fixture) |

### 13.4 CI Pipeline (GitHub Actions)

```yaml
# Triggered on push to dev and PRs to main
jobs:
  backend:
    - ruff check
    - pytest --cov=app --cov-fail-under=70
    - alembic upgrade head (on test DB)
  frontend:
    - eslint
    - tsc --noEmit
    - vitest run
```

### 13.5 Sprint Exit Test Checklist

| Sprint | Critical Test |
|--------|---------------|
| 1 | RLS hides cross-tenant rows |
| 2 | Register → login → `/auth/me`; 403 on wrong role |
| 3 | Patient CRUD + MRN uniqueness per tenant |
| 4 | E2E: patient → appointment → consult → bill → pay |
| 6 | E2E: admit → treat → discharge → invoice |
| 7 | E2E: lab order → result → report |
| 8 | E2E: prescribe → dispense → stock deducted |
| 11 | Razorpay webhook: payment success/failure; suspension flow |
| 12 | Full regression; load test 50 users; production smoke test |

### 13.6 Security Testing

| Test | When | Reference |
|------|------|-----------|
| Cross-tenant isolation suite | Every CI build | SECURITY_ARCHITECTURE.md §16.1 |
| SAST (Bandit, Semgrep) | Every PR | SECURITY_ARCHITECTURE.md §10.1 |
| Dependency scan (Snyk) | Every PR | NFR-SEC-013 |
| Pre-launch pen test | Before Sprint 12 production | SECURITY_ARCHITECTURE.md §16.2 |
| OWASP ZAP (staging) | Monthly from Sprint 6 | — |

---

## 14. Deployment Strategy

### 14.1 Infrastructure Overview

| Component | Service | Environment |
|-----------|---------|-------------|
| API | AWS ECS Fargate | Staging + Production |
| Worker | AWS ECS Fargate (separate service) | Staging + Production |
| Frontend | S3 + CloudFront | Staging + Production |
| Database | RDS PostgreSQL 14 (Multi-AZ in prod) | Staging + Production |
| Cache | ElastiCache Redis | Staging + Production |
| Files | S3 | Staging + Production |
| Queue | SQS | Staging + Production |
| Secrets | AWS Secrets Manager | All |
| DNS | Route 53 | `*.platform.com` wildcard |
| TLS | ACM certificates | Auto-renewal |
| WAF | AWS WAF | Production |
| Monitoring | CloudWatch + Sentry | All |

> Region: `ap-south-1` (Mumbai) for MVP per SYSTEM_ARCHITECTURE.md.

### 14.2 Deployment Pipeline

```mermaid
flowchart LR
    DEV["Local Dev"] -->|push dev| CI["GitHub Actions<br/>lint + test"]
    CI -->|pass| STAGING["Deploy Staging<br/>ECS + S3"]
    STAGING -->|smoke test| MANUAL["Manual Approval"]
    MANUAL -->|merge main| PROD["Deploy Production"]
    PROD --> SMOKE["Production Smoke Test"]
```

| Stage | Trigger | Approval |
|-------|---------|----------|
| Staging | Push to `dev` branch | Automatic |
| Production | Merge to `main` + tag | Manual (Sprint 12+) |

### 14.3 Deployment Steps (Staging)

```
1. CI builds Docker images → push to ECR
2. Run alembic upgrade head on staging RDS
3. ECS rolling deploy (api + worker services)
4. Upload frontend build to S3 → CloudFront invalidation
5. Run smoke test:
   - GET /health → 200
   - Login → register patient → 201
   - Cross-tenant isolation test suite
6. Notify (email/Slack) on failure
```

### 14.4 Production Launch Checklist (Sprint 12)

- [ ] RDS Multi-AZ enabled; automated backups verified (restore drill completed)
- [ ] Secrets in Secrets Manager (no env files on containers)
- [ ] WAF rules active (OWASP, rate limiting)
- [ ] TLS certificates valid; HSTS enabled
- [ ] CloudWatch alarms: API 5xx, RDS CPU, ECS health
- [ ] Sentry error tracking integrated
- [ ] SQS dead-letter queue configured with alerting
- [ ] Penetration test completed; critical/high findings fixed
- [ ] Cross-tenant isolation full regression passing
- [ ] 10 beta tenants onboarded via onboarding wizard
- [ ] Status page configured
- [ ] Incident response runbook documented

### 14.5 Rollback Strategy

| Scenario | Action | RTO |
|----------|--------|-----|
| Bad API deploy | ECS rollback to previous task definition | < 5 min |
| Bad migration | `alembic downgrade -1` + restore RDS snapshot if needed | < 30 min |
| Bad frontend deploy | CloudFront → previous S3 version | < 5 min |
| Database corruption | Restore RDS snapshot to point-in-time | < 2 hours |

### 14.6 Monitoring & Alerting

| Metric | Threshold | Alert |
|--------|-----------|-------|
| API 5xx rate | > 1% over 5 min | P1 |
| API P95 latency | > 2 seconds | P2 |
| RDS CPU | > 80% for 10 min | P2 |
| ECS task health | Unhealthy count > 0 | P1 |
| SQS DLQ messages | > 0 | P2 |
| Failed login rate | > 50/min | P2 |
| Disk usage (RDS) | > 80% | P2 |

### 14.7 Post-Launch Operations (Months 7–12)

| Activity | Frequency |
|----------|-----------|
| Bug fixes from beta feedback | Ongoing |
| Dependency updates | Monthly |
| Backup restore drill | Monthly |
| Security patch deployment | Within 48 hours (critical) |
| Performance review | Monthly |
| Advanced features (ADVANCED_FEATURES_ROADMAP) | Per phase gates |

---

## Appendix A: Document Cross-Reference

| Topic | Primary Document |
|-------|------------------|
| Sprint tasks and hour estimates | SPRINT_PLAN.md |
| API contracts | API_DESIGN.md |
| Database schema | DATABASE_DESIGN.md + `database/schema.sql` |
| Roles and permissions | RBAC_DESIGN.md |
| Tenant isolation | MULTI_TENANT_DESIGN.md |
| Security controls | SECURITY_ARCHITECTURE.md |
| SaaS billing | BILLING_SUBSCRIPTION.md |
| Post-MVP features | ADVANCED_FEATURES_ROADMAP.md |
| Product requirements | PRD.md + FUNCTIONAL_REQUIREMENTS.md |
| Non-functional requirements | NON_FUNCTIONAL_REQUIREMENTS.md |

## Appendix B: Known Gaps to Address During Implementation

| Gap | Resolution Sprint | Action |
|-----|-------------------|--------|
| OPD/IPD APIs missing from API_DESIGN.md | 4–5 | Author OpenAPI spec at sprint start |
| `database/seed-data.sql` empty | 1 | Write seed script |
| Permission namespace `lab:*` vs `laboratory:*` | 2 | Standardize on `laboratory:*` per API_DESIGN |
| `DEPLOYMENT_GUIDE.md` not yet authored | 12 | Write during production setup |
| `TESTING_STRATEGY.md` not yet authored | 1 | This document §13 serves interim guide |
| Table partitioning not in schema.sql | Post-MVP | Defer until 50+ tenants |
| Celery referenced in SYSTEM_ARCHITECTURE | 1 | Use SQS worker only |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Solution Architecture | Initial implementation plan for solo developer |

---

*This plan is the execution companion to SPRINT_PLAN.md. Follow sprint tasks for hour-level detail; follow this document for architectural decisions, build order, and engineering standards.*
