# Task Backlog — DS-001 to DS-080

| Field | Value |
|-------|-------|
| **Total Tasks** | 80 |
| **Completed** | ~32 |
| **In Progress** | ~5 |
| **Remaining** | ~43 |

**Status Legend:** ✅ Done | 🔄 Partial | ❌ Not Started | ⏸️ Deferred

---

## Phase 0 — Setup (DS-001 – DS-015)

| ID | Task | Sprint | Hrs | Status | Notes |
|----|------|--------|-----|--------|-------|
| DS-001 | Monorepo + Git foundation | S1 | 2 | ✅ | |
| DS-002 | Docker Compose infrastructure | S1 | 3 | ✅ | |
| DS-003 | Environment variable templates | S1 | 1 | ✅ | |
| DS-004 | Backend Python scaffold | S1 | 3 | ✅ | |
| DS-005 | FastAPI app factory | S1 | 2 | ✅ | |
| DS-006 | Frontend Vite scaffold | S1 | 2 | ✅ | |
| DS-007 | CI pipeline scaffold | S1 | 2 | ✅ | |
| DS-008 | PostgreSQL extensions + schemas | S1 | 2 | ✅ | Alembic 001 |
| DS-009 | Phase 1 foundation tables | S1 | 6 | ✅ | Alembic 002–004 |
| DS-010 | Row-Level Security policies | S1 | 3 | 🔄 | Partial in migrations |
| DS-011 | Bootstrap function + system seeds | S1 | 4 | 🔄 | `seed_auth_dev.py` only |
| DS-012 | SQLAlchemy models (platform + core) | S1 | 6 | ✅ | |
| DS-013 | Backend core infrastructure | S1 | 8 | ✅ | |
| DS-014 | Tenant context middleware | S1 | 6 | ✅ | |
| DS-015 | Frontend foundation shell | S1 | 10 | ✅ | |

**Gate G1:** DS-001–DS-015 → Foundation complete

---

## Phase 1 — Authentication (DS-016 – DS-022)

| ID | Task | Sprint | Hrs | Status | Notes |
|----|------|--------|-----|--------|-------|
| DS-016 | Auth database objects | S2 | 3 | ✅ | Alembic 005 |
| DS-017 | JWT keys + security module | S2 | 4 | ✅ | |
| DS-018 | Session + refresh token service | S2 | 6 | ✅ | |
| DS-019 | Auth API endpoints | S2 | 8 | ✅ | forgot/reset partial |
| DS-020 | Tenant resolution on login | S2 | 4 | ✅ | X-Tenant-Slug |
| DS-021 | Frontend authentication layer | S2 | 12 | ❌ | **CRITICAL BLOCKER** |
| DS-022 | Auth integration tests | S2 | 4 | ✅ | 43 tests pass |

---

## Phase 1 — RBAC (DS-023 – DS-027)

| ID | Task | Sprint | Hrs | Status | Notes |
|----|------|--------|-----|--------|-------|
| DS-023 | Role + permission seed data | S2 | 4 | ✅ | catalog.py |
| DS-024 | Permission resolver + cache | S2 | 6 | ✅ | |
| DS-025 | RBAC middleware + decorator | S2 | 4 | ✅ | |
| DS-026 | Frontend permission hooks | S2 | 4 | ❌ | |
| DS-027 | RBAC integration tests | S2 | 3 | ✅ | |

---

## Phase 1 — Tenant Management (DS-028 – DS-032)

| ID | Task | Sprint | Hrs | Status | Notes |
|----|------|--------|-----|--------|-------|
| DS-028 | Subscription plans schema + seeds | S2 | 4 | 🔄 | Schema partial |
| DS-029 | Tenant provisioning service | S2 | 8 | ✅ | |
| DS-030 | Tenant registration API | S2 | 4 | ✅ | |
| DS-031 | Subscription status middleware | S2 | 3 | 🔄 | |
| DS-032 | Frontend registration wizard | S2 | 8 | ❌ | |

---

## Phase 1 — Hospital Management (DS-033 – DS-035)

| ID | Task | Sprint | Hrs | Status | Notes |
|----|------|--------|-----|--------|-------|
| DS-033 | Hospital profile API | S2 | 5 | ✅ | /hospital/profile |
| DS-034 | Branch management API | S2 | 5 | ✅ | /hospital/locations |
| DS-035 | Hospital management UI | S3 | 8 | ❌ | |

---

## Phase 1 — User Management (DS-036 – DS-039)

| ID | Task | Sprint | Hrs | Status | Notes |
|----|------|--------|-----|--------|-------|
| DS-036 | User management API | S2–3 | 8 | ✅ | Full CRUD |
| DS-037 | Email adapter (invites, reset) | S2 | 4 | ❌ | |
| DS-038 | User management UI | S3 | 8 | ❌ | |
| DS-039 | Protected routes + role landing | S2 | 3 | ❌ | |

---

## Phase 2 — Patient Management (DS-040 – DS-042)

| ID | Task | Sprint | Hrs | Status |
|----|------|--------|-----|--------|
| DS-040 | Patient database extensions | S3 | 4 | ❌ |
| DS-041 | Patient API (full CRUD) | S3 | 10 | ❌ |
| DS-042 | Patient management UI | S3 | 12 | ❌ |

---

## Phase 2 — Staff & Doctors (DS-043 – DS-044)

| ID | Task | Sprint | Hrs | Status |
|----|------|--------|-----|--------|
| DS-043 | Staff + department schema + API | S3 | 6 | ❌ |
| DS-044 | Doctor profile API | S3 | 5 | ❌ |

---

## Phase 2 — Appointments & OPD (DS-045 – DS-048)

| ID | Task | Sprint | Hrs | Status |
|----|------|--------|-----|--------|
| DS-045 | Appointments schema + API | S4 | 6 | ❌ |
| DS-046 | OPD visits + queue API | S4 | 5 | ❌ |
| DS-047 | Consultation + e-prescription API | S4 | 6 | ❌ |
| DS-048 | Appointments + OPD UI | S4 | 11 | ❌ |

**Gate G2:** DS-021 through DS-048 → MVP demo

---

## Phase 2 — Patient Billing (DS-049 – DS-054)

| ID | Task | Sprint | Hrs | Status |
|----|------|--------|-----|--------|
| DS-049 | Billing schema migration | S4 | 2 | ❌ |
| DS-050 | Service master + invoice API | S4 | 8 | ❌ |
| DS-051 | Payments + receipt API | S4 | 4 | ❌ |
| DS-052 | PDF generation (invoice, receipt) | S4 | 2 | ❌ |
| DS-053 | Billing UI | S4 | 5 | ❌ |
| DS-054 | MVP E2E test + demo tenants | S4 | 8 | ❌ |

---

## Phase 3 — IPD (DS-055 – DS-060)

| ID | Task | Sprint | Hrs | Status |
|----|------|--------|-----|--------|
| DS-055 | IPD schema (wards, beds, admissions) | S5 | 2 | ❌ |
| DS-056 | Wards/beds/admissions API | S5 | 14 | ❌ |
| DS-057 | IPD foundation UI | S5 | 13 | ❌ |
| DS-058 | Nursing notes + IPD vitals API | S6 | 8 | ❌ |
| DS-059 | Discharge workflow + IPD billing | S6 | 15 | ❌ |
| DS-060 | IPD clinical UI | S6 | 13 | ❌ |

---

## Phase 3 — Laboratory (DS-061 – DS-063)

| ID | Task | Sprint | Hrs | Status |
|----|------|--------|-----|--------|
| DS-061 | Laboratory schema migration | S7 | 2 | ❌ |
| DS-062 | Lab orders + results API | S7 | 22 | ❌ |
| DS-063 | Laboratory UI | S7 | 13 | ❌ |

---

## Phase 3 — Pharmacy (DS-064 – DS-066)

| ID | Task | Sprint | Hrs | Status |
|----|------|--------|-----|--------|
| DS-064 | Pharmacy schema migration | S8 | 2 | ❌ |
| DS-065 | Dispensing + inventory API | S8 | 21 | ❌ |
| DS-066 | Pharmacy UI | S8 | 13 | ❌ |

**Gate G3:** DS-055 through DS-066 → Clinical suite complete

---

## Phase 4 — Growth (DS-067 – DS-080)

| ID | Task | Sprint | Hrs | Status |
|----|------|--------|-----|--------|
| DS-067 | Report views + dashboard API | S9 | 18 | ❌ |
| DS-068 | Reporting UI | S9 | 12 | ❌ |
| DS-069 | Notification service + worker | S10 | 15 | ❌ |
| DS-070 | Multi-location scoping | S10 | 7 | ❌ |
| DS-071 | Notifications UI | S10 | 10 | ❌ |
| DS-072 | Razorpay integration | S11 | 8 | ❌ |
| DS-073 | Plan limits + usage metering | S11 | 7 | ❌ |
| DS-074 | Audit log viewer | S11 | 6 | ❌ |
| DS-075 | Security hardening | S11 | 6 | ❌ |
| DS-076 | Patient CSV import job | S11 | 5 | ❌ |
| DS-077 | AWS Terraform production | S12 | 12 | ❌ |
| DS-078 | CloudWatch monitoring | S12 | 4 | ❌ |
| DS-079 | UAT + beta onboarding | S12 | 8 | ❌ |
| DS-080 | Launch docs + onboarding wizard | S12 | 10 | ❌ |

**Gate G4:** DS-072–DS-075 | **Gate G5:** DS-077–DS-080

---

## Backlog Summary by Status

| Status | Count | % |
|--------|-------|---|
| ✅ Done | 28 | 35% |
| 🔄 Partial | 5 | 6% |
| ❌ Not Started | 47 | 59% |

## Next 10 Tasks (Strict Order)

1. **DS-021** — Frontend auth layer (12 hrs) ← START HERE
2. **DS-039** — Protected routes (3 hrs)
3. **DS-032** — Registration wizard (8 hrs)
4. **DS-026** — Permission hooks (4 hrs)
5. **DS-037** — Email adapter stub (4 hrs)
6. **DS-031** — Subscription middleware (3 hrs)
7. **DS-040** — Patient DB migration (4 hrs)
8. **DS-041** — Patient API (10 hrs)
9. **DS-042** — Patient UI (12 hrs)
10. **DS-043** — Staff + departments API (6 hrs)
