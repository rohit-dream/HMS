# Sprint Plan — Detailed (All 12 Sprints)

> **⚠️ SUPERSEDED:** This is the **v1** sprint plan (included IPD/Lab/Pharmacy in 12 sprints; missing security/compliance tasks).  
> **Use [`09_MVP_SPRINT_PLAN_V2.md`](./09_MVP_SPRINT_PLAN_V2.md) for all development.**  
> Task tracking: [`10_MVP_TASK_BACKLOG.md`](./10_MVP_TASK_BACKLOG.md) (MVP-001–MVP-120).

> **Capacity:** ~56 net hours/sprint | **Ceremony:** 4 hrs | **Velocity:** 18–25 story points

---

## Sprint 1 — Foundation & Multi-Tenancy ✅ ~80%

**Weeks 1–2 | 21 pts | Gate G1**

### Objectives
- Monorepo, Docker, CI
- PostgreSQL + Alembic foundation
- Tenant middleware + health API
- React shell + API client

### Task Breakdown

| ID | Task | Layer | Hrs | Status |
|----|------|-------|-----|--------|
| S1-T01 | Monorepo + folder freeze | Setup | 2 | ✅ |
| S1-T02 | Docker Compose (PG + Redis) | Infra | 3 | ✅ |
| S1-T03 | Env templates | Setup | 1 | ✅ |
| S1-T04 | Backend scaffold (FastAPI) | Backend | 4 | ✅ |
| S1-T05 | Frontend scaffold (Vite) | Frontend | 3 | ✅ |
| S1-T06 | CI pipeline | DevOps | 2 | ✅ |
| S1-T07 | Alembic 001 schemas | DB | 2 | ✅ |
| S1-T08 | Alembic 002–004 foundation tables | DB | 10 | ✅ |
| S1-T09 | RLS policies | DB | 3 | ⚠️ |
| S1-T10 | SQLAlchemy models | Backend | 6 | ✅ |
| S1-T11 | Core infra (config, logging, envelope) | Backend | 8 | ✅ |
| S1-T12 | Tenant middleware | Backend | 4 | ✅ |
| S1-T13 | Health endpoints | Backend | 2 | ✅ |
| S1-T14 | Frontend shell + health page | Frontend | 10 | ✅ |
| S1-T15 | Pytest + tenant isolation test | Test | 6 | ✅ |
| S1-T16 | Seed scripts | DB | 4 | ⚠️ |

### Deliverables
- [x] `docker compose up` works
- [x] CI green
- [x] Health API with envelope
- [ ] RLS smoke test documented
- [ ] Staging environment

---

## Sprint 2 — Authentication, RBAC & Onboarding 🔄 ~55%

**Weeks 3–4 | 23 pts**

### Objectives
- Complete auth flow (backend done; **frontend is priority**)
- RBAC enforcement
- Self-service tenant registration
- Login + registration UI

### Task Breakdown

| ID | Task | Layer | Hrs | Status |
|----|------|-------|-----|--------|
| S2-T01 | Auth DB (sessions, reset tokens) | DB | 3 | ✅ |
| S2-T02 | JWT RS256 + bcrypt security module | Backend | 4 | ✅ |
| S2-T03 | Auth service (sessions, refresh rotation) | Backend | 6 | ✅ |
| S2-T04 | Auth API (login, logout, refresh, me) | Backend | 8 | ✅ |
| S2-T05 | Tenant resolver (slug → tenant_id) | Backend | 4 | ✅ |
| S2-T06 | RBAC seed + permission catalog | DB | 4 | ✅ |
| S2-T07 | Permission resolver + Redis cache | Backend | 6 | ✅ |
| S2-T08 | `require_permission` decorator | Backend | 4 | ✅ |
| S2-T09 | Tenant provisioning service | Backend | 8 | ✅ |
| S2-T10 | Platform register API | Backend | 4 | ✅ |
| S2-T11 | Hospital profile + locations API | Backend | 10 | ✅ |
| S2-T12 | User management API | Backend | 12 | ✅ |
| S2-T13 | Subscription status middleware | Backend | 3 | ⚠️ |
| S2-T14 | Email adapter (SES stub) | Backend | 4 | ❌ |
| S2-T15 | **AuthProvider + login page** | Frontend | 8 | ❌ |
| S2-T16 | **Registration wizard** | Frontend | 8 | ❌ |
| S2-T17 | **Protected routes + token refresh** | Frontend | 4 | ❌ |
| S2-T18 | Permission hooks + PermissionGuard | Frontend | 4 | ❌ |
| S2-T19 | Auth + RBAC integration tests | Test | 6 | ✅ |
| S2-T20 | E2E: register → login → /me | Test | 2 | ❌ |

### Sprint 2 Priority Order (Remaining)
1. S2-T15 → S2-T17 (auth UI — **BLOCKER**)
2. S2-T16 (registration wizard)
3. S2-T18 (permission guards)
4. S2-T14 (email stub)
5. S2-T13 (subscription middleware)
6. S2-T20 (E2E)

### Deliverables
- [x] Backend login/refresh/logout
- [x] RBAC 403 on missing permission
- [ ] User can register + login via UI
- [ ] Password reset email (staging)
- [ ] Login/registration on staging

---

## Sprint 3 — Patients, Staff & Administration

**Weeks 5–6 | 24 pts**

### Objectives
- Full patient CRUD + MRN + search
- Staff, departments, doctor profiles
- Patient + admin UI screens
- Hospital settings UI

### Task Breakdown

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S3-T01 | Patient tables migration + MRN function | DB | 4 |
| S3-T02 | Patient repository + service | Backend | 6 |
| S3-T03 | Patient API (7 endpoints + allergies) | Backend | 8 |
| S3-T04 | Staff + departments migration | DB | 2 |
| S3-T05 | Staff + departments API | Backend | 5 |
| S3-T06 | Doctor profile API | Backend | 4 |
| S3-T07 | Plan limit: trial patient cap (100) | Backend | 3 |
| S3-T08 | PHI access audit log writes | Backend | 2 |
| S3-T09 | Patient list + search UI | Frontend | 5 |
| S3-T10 | Patient registration form (RHF + Zod) | Frontend | 5 |
| S3-T11 | Patient profile page | Frontend | 4 |
| S3-T12 | Admin: departments + staff pages | Frontend | 4 |
| S3-T13 | Hospital settings + branches UI | Frontend | 8 |
| S3-T14 | User management UI | Frontend | 8 |
| S3-T15 | Patient API integration tests | Test | 3 |
| S3-T16 | MRN uniqueness test | Test | 1 |
| S3-T17 | Form validation component tests | Test | 2 |

### Deliverables
- [ ] Receptionist registers patient < 2 min
- [ ] MRN unique per tenant
- [ ] Admin manages departments, staff, doctors
- [ ] Patient + admin modules on staging

---

## Sprint 4 — OPD, Billing & MVP Release 🎯 Gate G2

**Weeks 7–8 | 25 pts**

### Objectives
- OPD: appointments, queue, consultation, e-Rx
- Billing: services, invoice, payment, receipt
- E2E: patient → appointment → consult → bill → pay

### Task Breakdown

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S4-T01 | Clinical + billing tables migration | DB | 4 |
| S4-T02 | Appointments API (CRUD, availability) | Backend | 6 |
| S4-T03 | OPD visits + queue API | Backend | 5 |
| S4-T04 | Consultation API (vitals, notes, e-Rx) | Backend | 6 |
| S4-T05 | Billing service master API | Backend | 3 |
| S4-T06 | Invoice CRUD + finalize + void | Backend | 5 |
| S4-T07 | Payments API + allocations | Backend | 4 |
| S4-T08 | PDF: invoice + receipt | Backend | 2 |
| S4-T09 | Seed default billing services on onboarding | DB | 2 |
| S4-T10 | Appointment calendar + booking modal | Frontend | 5 |
| S4-T11 | OPD queue board | Frontend | 4 |
| S4-T12 | Doctor consultation screen | Frontend | 6 |
| S4-T13 | Billing: invoice + payment + receipt UI | Frontend | 5 |
| S4-T14 | Role dashboards (receptionist, doctor, accountant) | Frontend | 4 |
| S4-T15 | E2E: full MVP workflow test | Test | 4 |
| S4-T16 | Cross-tenant isolation regression | Test | 2 |
| S4-T17 | UAT script + 3 demo tenants | Ops | 4 |
| S4-T18 | MVP demo video | Ops | 2 |

### Phase 1 Exit Criteria (G2)
- [ ] End-to-end workflow < 5 minutes
- [ ] OpenAPI published on staging
- [ ] Known issues log for Phase 2

---

## Sprint 5 — IPD Foundation

**Weeks 9–10 | 22 pts**

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S5-T01 | Wards/rooms/beds migration | DB | 2 |
| S5-T02 | Wards/rooms/beds CRUD API | Backend | 6 |
| S5-T03 | Bed availability dashboard API | Backend | 3 |
| S5-T04 | Admissions API | Backend | 8 |
| S5-T05 | Bed plan limit enforcement | Backend | 2 |
| S5-T06 | Admission transfers API | Backend | 4 |
| S5-T07 | Ward/bed admin UI | Frontend | 5 |
| S5-T08 | Bed availability dashboard UI | Frontend | 5 |
| S5-T09 | Admission form + bed selector | Frontend | 5 |
| S5-T10 | Admitted patients list | Frontend | 3 |
| S5-T11 | Admission integration tests | Test | 5 |

---

## Sprint 6 — IPD Clinical & Discharge Billing

**Weeks 11–12 | 23 pts**

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S6-T01 | Nursing notes API | Backend | 4 |
| S6-T02 | IPD vitals API + chart data | Backend | 4 |
| S6-T03 | Discharge summary API + PDF | Backend | 5 |
| S6-T04 | Discharge workflow (release bed) | Backend | 4 |
| S6-T05 | IPD daily charges job | Backend | 4 |
| S6-T06 | IPD final invoice generation | Backend | 6 |
| S6-T07 | Nurse vitals + notes UI | Frontend | 9 |
| S6-T08 | Doctor discharge summary UI | Frontend | 5 |
| S6-T09 | Accountant running bill + discharge invoice | Frontend | 4 |
| S6-T10 | IPD discharge E2E test | Test | 4 |

---

## Sprint 7 — Laboratory

**Weeks 13–14 | 24 pts**

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S7-T01 | Laboratory schema migration | DB | 2 |
| S7-T02 | Lab test catalog API | Backend | 4 |
| S7-T03 | Lab orders + items API | Backend | 6 |
| S7-T04 | Sample collection + barcode API | Backend | 4 |
| S7-T05 | Results entry + abnormal detection | Backend | 5 |
| S7-T06 | Critical value notification | Backend | 3 |
| S7-T07 | Lab report PDF + finalize | Backend | 4 |
| S7-T08 | Lab charges → invoice integration | Backend | 2 |
| S7-T09 | Lab catalog admin UI | Frontend | 3 |
| S7-T10 | Doctor: order labs from consultation | Frontend | 3 |
| S7-T11 | Lab tech queue + sample collection UI | Frontend | 5 |
| S7-T12 | Result entry + report view UI | Frontend | 7 |
| S7-T13 | Lab workflow E2E test | Test | 4 |

---

## Sprint 8 — Pharmacy & Phase 2 Release 🎯 Gate G3

**Weeks 15–16 | 24 pts**

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S8-T01 | Pharmacy schema migration | DB | 2 |
| S8-T02 | Medicines CRUD API | Backend | 4 |
| S8-T03 | Pending prescriptions queue | Backend | 3 |
| S8-T04 | Dispense API (stock deduction) | Backend | 8 |
| S8-T05 | Inventory stock-in + adjust API | Backend | 6 |
| S8-T06 | Purchase order basic API | Backend | 3 |
| S8-T07 | Pharmacy → invoice integration | Backend | 4 |
| S8-T08 | Medicine master admin UI | Frontend | 3 |
| S8-T09 | Prescription queue + dispense UI | Frontend | 9 |
| S8-T10 | Inventory list + stock-in UI | Frontend | 4 |
| S8-T11 | Low-stock alert widget | Frontend | 2 |
| S8-T12 | Prescribe → dispense → bill E2E | Test | 2 |
| S8-T13 | Phase 2 release notes | Ops | 2 |

---

## Sprint 9 — Reporting & Dashboard

**Weeks 17–18 | 20 pts**

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S9-T01 | Report query views + indexes | DB | 6 |
| S9-T02 | Dashboard stats API (Redis cache) | Backend | 5 |
| S9-T03 | OPD + IPD report endpoints | Backend | 5 |
| S9-T04 | Lab + pharmacy report endpoints | Backend | 4 |
| S9-T05 | Financial reports API | Backend | 4 |
| S9-T06 | CSV + PDF export service | Backend | 4 |
| S9-T07 | Admin dashboard UI (charts) | Frontend | 8 |
| S9-T08 | Reports page with filters + export | Frontend | 8 |
| S9-T09 | Role-specific dashboard routing | Frontend | 4 |
| S9-T10 | Report accuracy + performance tests | Test | 5 |

---

## Sprint 10 — Notifications & Multi-Location

**Weeks 19–20 | 21 pts**

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S10-T01 | Comms schema migration | DB | 1 |
| S10-T02 | Notification service API | Backend | 5 |
| S10-T03 | SQS worker: email + SMS | Backend | 6 |
| S10-T04 | Appointment reminder cron job | Backend | 4 |
| S10-T05 | Notification preferences API | Backend | 3 |
| S10-T06 | Location scoping on queries | Backend | 4 |
| S10-T07 | Notification bell UI | Frontend | 4 |
| S10-T08 | Preferences + branch management UI | Frontend | 7 |
| S10-T09 | Location selector in header | Frontend | 3 |
| S10-T10 | Reminder + location filter tests | Test | 5 |

---

## Sprint 11 — Subscription Billing & Security 🎯 Gate G4

**Weeks 21–22 | 22 pts**

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S11-T01 | Razorpay integration (customer, sub, webhook) | Backend | 8 |
| S11-T02 | Plan upgrade/downgrade + proration | Backend | 4 |
| S11-T03 | Suspension on payment failure | Backend | 3 |
| S11-T04 | Usage metering API | Backend | 3 |
| S11-T05 | Audit log list API | Backend | 3 |
| S11-T06 | Rate limiting (Redis) | Backend | 2 |
| S11-T07 | Patient CSV import (SQS job) | Backend | 5 |
| S11-T08 | Subscription + payment UI | Frontend | 9 |
| S11-T09 | Audit log viewer UI | Frontend | 3 |
| S11-T10 | Razorpay webhook + isolation regression tests | Test | 8 |

---

## Sprint 12 — Production Launch 🎯 Gate G5

**Weeks 23–24 | 20 pts**

| ID | Task | Layer | Hrs |
|----|------|-------|-----|
| S12-T01 | Terraform AWS (ECS, RDS, Redis, S3) | DevOps | 12 |
| S12-T02 | CloudWatch monitoring + alerts | DevOps | 4 |
| S12-T03 | Production deployment | DevOps | 4 |
| S12-T04 | UAT with 10 beta tenants | QA | 8 |
| S12-T05 | P0/P1 bug fixes from beta | All | 12 |
| S12-T06 | Deployment runbook | Docs | 4 |
| S12-T07 | User onboarding guide | Docs | 4 |
| S12-T08 | Onboarding wizard UI | Frontend | 6 |
| S12-T09 | Performance baseline test | Test | 4 |
| S12-T10 | Security checklist completion | Security | 4 |

### Launch Checklist
- [ ] Production AWS live
- [ ] 10 beta tenants onboarded
- [ ] All G2–G4 criteria still pass
- [ ] Runbook + onboarding guide published
- [ ] **PRODUCTION LAUNCH**
