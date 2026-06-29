
# Project Baseline & Current Status

| Field | Value |
|-------|-------|
| **As-of Date** | June 26, 2026 |
| **Branch** | `rohit/dev` |
| **Tests** | 143+ unit tests passing; full integration suite green in CI |
| **Alembic** | Migrations 001–026 applied (head: `026_opd_tables`) |
| **Gate G1** | **PASSED** (MVP-020) |
| **Gate G2** | **PASSED** (MVP-050) |

---

## 1. What Exists Today

### Documentation (Complete)
- 36+ markdown files in `docs/` including PRD, architecture, database, RBAC, security, API, sprints
- `docs/API_DESIGN_OPD.md` — full OPD module spec (MVP-051)
- `docs/COMPOSITE_FK_MIGRATION_CHECKLIST.md` — migration lint rules (MVP-055)
- `docs/TESTING_STRATEGY.md` and `docs/DEPLOYMENT_GUIDE.md` (MVP-010)
- Frozen folder structure (`FOLDER_STRUCTURE_FREEZE.md`)
- SDLC Planning V2 (`09_MVP_SPRINT_PLAN_V2.md`, `10_MVP_TASK_BACKLOG.md`)

### Infrastructure
| Asset | Status |
|-------|--------|
| Docker Compose (Postgres 14 + Redis 7) | Done |
| GitHub Actions CI (lint, G1, G2, isolation, OpenAPI snapshot, composite FK lint, full suite) | Done |
| Terraform / AWS production | Not started |
| SQS worker | Stub only |

### Database
| Asset | Status |
|-------|--------|
| `database/baseline/schema.sql` (61 tables) | Reference only |
| Alembic 001–024 | Applied |
| Platform + core + audit RLS | Done |
| `platform.create_tenant()` | Done (MVP-013) |
| System tenant + subscription plans seed | Done (MVP-015) |
| `audit.audit_logs` | Done (MVP-033) |
| Org tables (departments, staff, doctors, schedules) | Done (MVP-059) |
| Patient tables + pg_trgm indexes + MRN generator | Done (MVP-069–071) |
| `hms_app` role for RLS tests | Done |

### Backend (`backend/app/`)
| Module | Status | APIs |
|--------|--------|------|
| **Platform** | Implemented | `/platform/register`, tenant CRUD, activate/suspend |
| **Hospital** | Implemented | `/hospital/profile`, locations, settings |
| **Identity/Auth** | Implemented | login, refresh, logout, `/me`, forgot/reset, verify |
| **RBAC** | Implemented | Permission resolver, `require_permission`, catalog |
| **User Management** | Implemented | Full `/admin/users/*` CRUD, roles, invite, accept-invite |
| **Audit** | Implemented | Write service, mutation middleware, login audit, PHI view audit |
| **Org (S6)** | Implemented | Departments, staff, doctors, doctor schedules |
| **Patients (S7)** | Implemented | Full CRUD, allergies, contacts, chronic conditions, duplicates, visit history stub |
| **OPD** | OpenAPI stubs | 20 endpoints return `501` (MVP-052); spec in `API_DESIGN_OPD.md` |
| **Appointments (S8)** | Implemented | CRUD, availability, confirm/cancel, calendar + booking UI |
| **OPD (S9)** | ✅ Complete | Gate G3 passed (MVP-091–102) |
| **Billing/Lab/Pharmacy** | Scaffold | Sprint 9+ |

### Frontend (`frontend/src/`)
| Area | Status |
|------|--------|
| Vite + React + TS + Tailwind | Done |
| AuthProvider + login/register/forgot/reset/verify | Done (Sprint 3) |
| Protected routes, role landing, PermissionGuard | Done (Sprint 4) |
| Admin UI (settings, branches, users) | Done (MVP-049) |
| Org admin UI (departments, staff, doctors, schedules) | Done (MVP-064–066) |
| Patient UI (list, register, profile) | Done (MVP-079–081) |
| Shared UI kit (`components/ui/*`, FormField) | Done (MVP-056) |
| OPD queue board UI (`/opd/queue`, ETag polling) | Done (MVP-097) |
| OPD consult / billing workflows | Consult UI + billing placeholder pages | Sprint 9+ |
| Appointments UI (calendar, booking modal, detail) | Done (MVP-087–088) |

---

## 2. Sprint Completion Map

| Sprint | Theme | Backend | Frontend | DB | Overall |
|--------|-------|---------|----------|-----|---------|
| **S1** Foundation | Scaffold, health, CI, docs | 100% | 100% | 100% | **100%** |
| **S2** Multi-tenant + RLS + seeds | Platform tables, RLS, G1 | 100% | — | 100% | **100%** |
| **S3** Auth vertical slice | JWT, sessions, audit_logs | 100% | 100% | 100% | **100%** |
| **S4** RBAC + hospital admin | Users, hospital API, G2 | 100% | 100% | 100% | **100%** |
| **S5** API standards + OPD spec | OPD spec/stubs, audit framework, UI kit | 100% | 100% | — | **100%** |
| **S6** Org structure | Departments, staff, doctors | 100% | 100% | 100% | **100%** |
| **S7** Patient management | CRUD, search, duplicates, consent | 100% | 95% | 100% | **~98%** |
| **S8** Appointments | CRUD, availability, calendar, booking, E2E tests | 100% | 100% | 100% | **100%** |
| **S9–S12** OPD, billing, launch | — | 0% | 0% | 0% | **0%** |

---

## 3. Recent Sprint Completions

### Sprint 6 — Org Structure (MVP-059 – MVP-068) ✅

Departments, staff, doctors, doctor schedules — full API + admin UI + integration/isolation tests.

### Sprint 7 — Patient Management (MVP-069 – MVP-082) ✅

Patient CRUD, allergies, contacts, chronic conditions, duplicate detection, consent, trial cap, MRN generator with tenant prefix, PHI access audit on patient read, patient list/register/profile UI.

### Sprint 5 — API Standards + OPD Spec (MVP-051 – MVP-058) ✅

OPD OpenAPI stubs, audit middleware, shared UI components, OpenAPI snapshot tests.

### Sprint 4 — Gate G2 (MVP-036 – MVP-050) ✅

Hospital admin vertical slice with RBAC, registration wizard, protected routes.

Verify: `python backend/scripts/verify_gate_g2.py`

---

### Sprint 8 — Appointments (MVP-083 – MVP-090) ✅

Appointment tables + RLS, CRUD/availability/confirm/cancel APIs, calendar + booking modal UI, conflict 409 tests, full lifecycle E2E workflow tests.

---

## 4. Execution Plan (V2)

**Authoritative roadmap:** [`09_MVP_SPRINT_PLAN_V2.md`](./09_MVP_SPRINT_PLAN_V2.md)  
**Task backlog:** [`10_MVP_TASK_BACKLOG.md`](./10_MVP_TASK_BACKLOG.md) (MVP-001–MVP-135)

**Current position:** **Sprint 9** — OPD workflows.

---

## 5. Immediate Next Steps (Sprint 9)

| Priority | Task | MVP IDs |
|----------|------|---------|
| P0 | Alembic OPD tables + RLS | MVP-091 |
| P0 | OPD visits + queue + vitals APIs | MVP-092–095 |
| P1 | Doctor consultation UI | MVP-098 |
| P1 | OPD workflow integration + Gate G3 | MVP-101–102 |

---

## 6. Known Gaps (Sprint 7 residual)

| Gap | Impact | Resolution |
|-----|--------|------------|
| Patient demographics edit UI | `PATCH /patients` API exists; no edit form on profile | Optional S8 polish or S7.1 |
| `phi_access_logs` dedicated table | PHI logged to `audit.audit_logs` with `phi_access` flag | Sprint 11 (MVP-116) |
| 10K patient search perf smoke test | Not automated locally | Add when CI has perf budget |
| Accept-invite UI page | API-only; invite token shown in dev banner | Low priority |
| OPD consult UI + visit history | Sprint 9 complete — Gate G3 passed | Sprint 10 (billing) |
| AWS / production deploy | No staging environment | Sprint 12 |

---

## 7. Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Backend unit tests | 143+ passing | Growing; never regress |
| Alembic head | 026 | +1 per schema sprint |
| Gate G1 (CF-01 isolation) | PASS | Mandatory every PR |
| Gate G2 (admin E2E) | PASS | Mandatory every PR |
| OpenAPI snapshot | PASS | Update snapshot on intentional API changes |
| Frontend build | PASS | `npm run build` |
| Open P0 bugs | 0 | 0 at sprint end |
