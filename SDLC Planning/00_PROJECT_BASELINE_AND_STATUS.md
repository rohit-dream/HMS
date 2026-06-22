
# Project Baseline & Current Status

| Field | Value |
|-------|-------|
| **As-of Date** | June 2026 |
| **Branch** | `rohit/dev` |
| **Tests** | 101 passing |
| **Alembic** | Migrations 001–011 applied (head: `011_system_tenant_plans_seed`) |
| **Gate G1** | **PASSED** (MVP-020) |

---

## 1. What Exists Today

### Documentation (Complete)
- 36+ markdown files in `docs/` including PRD, architecture, database, RBAC, security, API, sprints
- `docs/TESTING_STRATEGY.md` and `docs/DEPLOYMENT_GUIDE.md` (MVP-010)
- Frozen folder structure (`FOLDER_STRUCTURE_FREEZE.md`)
- SDLC Planning V2 (`09_MVP_SPRINT_PLAN_V2.md`, `10_MVP_TASK_BACKLOG.md`)

### Infrastructure
| Asset | Status |
|-------|--------|
| Docker Compose (Postgres 14 + Redis 7) | Done |
| GitHub Actions CI (lint, G1, isolation, full suite) | Done |
| Terraform / AWS production | Not started |
| SQS worker | Stub only |

### Database
| Asset | Status |
|-------|--------|
| `database/baseline/schema.sql` (61 tables) | Reference only |
| Alembic 001–011 | Applied |
| Platform RLS (FORCE on 5 tables) | Done (MVP-012) |
| `platform.create_tenant()` | Done (MVP-013) |
| System tenant + subscription plans seed | Done (MVP-015) |
| `hms_app` role for RLS tests | Done |

### Backend (`backend/app/`)
| Module | Status | APIs |
|--------|--------|------|
| **Platform** | Implemented | `/platform/register`, tenant CRUD, activate/suspend |
| **Hospital** | Implemented | `/hospital/profile`, locations, settings |
| **Identity/Auth** | Implemented | login, refresh, logout, `/me`, PATCH `/me` |
| **RBAC** | Implemented | Permission resolver, `require_permission`, catalog |
| **User Management** | Implemented | Full `/admin/users/*` CRUD, roles, reset |
| **Multi-tenant RLS** | Implemented | `TenantScopedRepository`, session `SET app.tenant_id` |
| **Patients** | Stub | GET/POST placeholders only |
| **Staff/Clinical/Billing/Lab/Pharmacy** | Scaffold | Empty domain folders |
| **Audit** | Stub | `/admin/audit` placeholder |

### Frontend (`frontend/src/`)
| Area | Status |
|------|--------|
| Vite + React + TS + Tailwind | Done |
| App shell (layout, routing) | Done |
| Health page (API connectivity) | Done |
| AuthProvider | **Stub** (`isAuthenticated: false`) |
| `features/` modules | **0 files** |
| Login/Register/Protected routes | Not started |

---

## 2. Sprint Completion Map

| Sprint | Theme | Backend | Frontend | DB | Overall |
|--------|-------|---------|----------|-----|---------|
| **S1** Foundation | Scaffold, health, CI, docs | 100% | 70% | 100% | **~95%** |
| **S2** Multi-tenant + RLS + seeds | Platform tables, RLS, G1 | **100%** | 0% | **100%** | **~85%** |
| **S3** Auth vertical slice | Email verify, frontend auth | 60% | 0% | 20% | **~25%** |
| **S4** OPD + Billing MVP | Appointments, consult, invoice | 0% | 0% | 0% | **0%** |
| **S5–S8** Clinical depth | IPD, lab, pharmacy | 0% | 0% | 0% | **0%** |
| **S9–S12** Growth + launch | Reports, notifications, Razorpay | 0% | 0% | 0% | **0%** |

---

## 3. Sprint 2 Completion (MVP-011 – MVP-020)

| ID | Task | Status |
|----|------|--------|
| MVP-011 | Platform subscription tables | ✅ |
| MVP-012 | RLS on platform tables | ✅ |
| MVP-013 | `platform.create_tenant()` | ✅ |
| MVP-014 | TenantScopedRepository + RLS session | ✅ |
| MVP-015 | System tenant + plans seed | ✅ |
| MVP-016 | Tenant middleware | ✅ |
| MVP-017 | Platform register API | ✅ |
| MVP-018 | SQLAlchemy platform models | ✅ |
| MVP-019 | Cross-tenant isolation test | ✅ |
| MVP-020 | Gate G1 verification | ✅ |

**Gate G1 verdict:** PASSED — safe to proceed with Sprint 3 feature work.

Verify locally: `python backend/scripts/verify_gate_g1.py`

---

## 4. Execution Plan (V2)

**Authoritative roadmap:** [`09_MVP_SPRINT_PLAN_V2.md`](./09_MVP_SPRINT_PLAN_V2.md)  
**Task backlog:** [`10_MVP_TASK_BACKLOG.md`](./10_MVP_TASK_BACKLOG.md) (MVP-001–MVP-135)

**Current position:** **Sprint 3** — auth vertical slice (frontend auth gap is P0).

---

## 5. Immediate Next Steps (Sprint 3)

| Priority | Task | MVP IDs |
|----------|------|---------|
| P0 | Frontend auth (login, refresh, AuthProvider) | MVP-030–031 |
| P0 | Email verification flow | MVP-022, MVP-026 |
| P0 | Protected routes + permission hooks | MVP-029 |
| P1 | Registration wizard UI | MVP-032 |
| P1 | `audit.audit_logs` migration | MVP-021 |

---

## 6. Known Gaps

| Gap | Impact | Resolution Sprint |
|-----|--------|-------------------|
| Frontend auth not started | No demoable login UI | Sprint 3 |
| OPD/IPD not in `API_DESIGN.md` | API contract ambiguity | Before Sprint 4 |
| Email adapter missing | Invite/reset blocked in prod | Sprint 3 |
| Patient/staff modules stub only | No clinical workflows | Sprint 3–4 |

---

## 7. Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Backend tests | 101 | Growing; never regress |
| Alembic head | 011 | +1 per schema sprint |
| Gate G1 (CF-01 isolation) | PASS | Mandatory every PR |
| Open P0 bugs | 0 | 0 at sprint end |
