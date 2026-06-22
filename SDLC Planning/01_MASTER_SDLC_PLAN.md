# Master SDLC Plan

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Planning Horizon** | 12 months active + 6 months stabilization |
| **Team** | 1 solo full-stack developer |
| **Capacity** | ~56 net dev hours / 2-week sprint |

---

## 1. Vision & Success Definition

**Vision:** Production-ready multi-tenant HMS SaaS for SMB hospitals in India — register → patient → OPD/IPD → lab → pharmacy → billing → reports → subscription monetization.

**MVP Success (Gate G2 — End Sprint 4):**
- Self-service tenant signup + login
- Patient registration + search
- OPD appointment → consultation → e-prescription
- Invoice + payment + receipt
- RBAC enforced; tenant isolation proven

**Launch Success (Gate G5 — End Sprint 12):**
- 10 paying beta tenants on production AWS
- 99.9% uptime target
- Razorpay subscription billing live
- Security self-assessment complete

---

## 2. Delivery Model

### 2.1 Vertical Slice Pattern

Never build all backend before frontend. Each module ships:

```
Database migration → ORM model → Repository → Service → API → Frontend feature → Integration test
```

### 2.2 Weekly Rhythm (Solo Developer)

| Day | Focus |
|-----|-------|
| Monday | Backend: models, repositories, services |
| Tuesday | Backend: API routes, unit tests |
| Wednesday | Backend: integration tests, staging deploy |
| Thursday | Frontend: pages, forms, API hooks |
| Friday | E2E smoke, polish, sprint review, next sprint prep |

### 2.3 Technology Stack (Frozen)

| Layer | Choice |
|-------|--------|
| Frontend | React 18, TypeScript, Vite, Tailwind, TanStack Query, React Hook Form, Zod |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, pytest |
| Database | PostgreSQL 14+, 8 schemas, RLS |
| Cache/Rate limit | Redis 7 |
| Auth | JWT RS256 + HttpOnly refresh cookie |
| Jobs | SQS worker (not Celery) |
| Payments | Razorpay (India) |
| Cloud | AWS ECS, RDS Multi-AZ, S3, SES, CloudWatch |

---

## 3. Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 0 — Setup          │ Weeks 1–2   │ DS-001–DS-015  │ ~80% COMPLETE   │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 1 — MVP            │ Weeks 3–8   │ DS-016–DS-054  │ Sprints 2–4     │
│   Auth, RBAC, Tenant,    │             │                │ Backend ~60%    │
│   Hospital, Users,       │             │                │ Frontend ~10%   │
│   Patients, OPD, Billing │             │                │                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2 — Clinical       │ Weeks 9–16  │ DS-055–DS-068  │ Sprints 5–8     │
│   IPD, Lab, Pharmacy     │             │                │ Not started     │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 3 — Growth         │ Weeks 17–24 │ DS-069–DS-080  │ Sprints 9–12    │
│   Reports, Notifications,│             │                │ Not started     │
│   Subscriptions, Launch  │             │                │                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ STABILIZATION            │ Months 7–12 │ —              │ Beta support    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Module Build Order (Critical Path)

| # | Module | Sprint | Gate | Depends On |
|---|--------|--------|------|------------|
| 1 | Platform foundation | S1 | G1 | — |
| 2 | Authentication | S2 | — | 1 |
| 3 | RBAC | S2 | — | 2 |
| 4 | Tenant provisioning | S2 | — | 1, 3 |
| 5 | Hospital admin | S2–3 | — | 4 |
| 6 | User management | S2–3 | — | 3, 4 |
| 7 | **Frontend auth** | **S2** | — | 2 (**BLOCKER**) |
| 8 | Patients | S3 | — | 6, 7 |
| 9 | Staff + Doctors | S3 | — | 6 |
| 10 | Appointments + OPD | S4 | G2 | 8, 9 |
| 11 | Patient billing | S4 | G2 | 8, 10 |
| 12 | IPD | S5–6 | G3 | 8, 11 |
| 13 | Laboratory | S7 | G3 | 8, 11 |
| 14 | Pharmacy + inventory | S8 | G3 | 10, 11 |
| 15 | Reports + dashboard | S9 | — | All clinical |
| 16 | Notifications | S10 | — | 10, 11 |
| 17 | SaaS subscriptions | S11 | G4 | 4 |
| 18 | Production launch | S12 | G5 | All |

**Current blocker:** Module #7 (Frontend auth) — backend auth exists but no UI.

---

## 5. Sprint Calendar

| Sprint | Weeks | Calendar | Theme | Story Pts | Gate |
|--------|-------|----------|-------|-----------|------|
| S1 | 1–2 | Jul 2026 | Foundation & multi-tenancy | 21 | G1 |
| S2 | 3–4 | Jul 2026 | Auth, RBAC, onboarding | 23 | — |
| S3 | 5–6 | Aug 2026 | Patients, staff, admin | 24 | — |
| S4 | 7–8 | Aug 2026 | OPD, billing, MVP release | 25 | **G2** |
| S5 | 9–10 | Sep 2026 | IPD wards, beds, admissions | 22 | — |
| S6 | 11–12 | Sep 2026 | IPD clinical, discharge billing | 23 | — |
| S7 | 13–14 | Oct 2026 | Laboratory | 24 | — |
| S8 | 15–16 | Oct 2026 | Pharmacy, inventory, Phase 2 | 24 | **G3** |
| S9 | 17–18 | Nov 2026 | Reporting & dashboard | 20 | — |
| S10 | 19–20 | Nov 2026 | Notifications, multi-location | 21 | — |
| S11 | 21–22 | Dec 2026 | Subscription billing, security | 22 | **G4** |
| S12 | 23–24 | Dec 2026 | Production launch, UAT | 20 | **G5** |

**Total:** 249 story points over 24 weeks (~56 hrs/sprint = ~672 dev hours)

---

## 6. Layer Responsibilities Per Sprint

Every sprint allocates hours across five workstreams:

| Workstream | Typical % | Examples |
|------------|-----------|----------|
| Database | 10–15% | Migrations, indexes, seeds, RLS |
| Backend | 45–50% | Models, repos, services, APIs |
| Frontend | 30–35% | Pages, forms, hooks, guards |
| Testing | 10–15% | Unit, integration, E2E smoke |
| DevOps | 5% | CI, staging deploy, monitoring |

---

## 7. Quality Standards (All Sprints)

- `tenant_id` on every tenant-scoped table and query
- RBAC `require_permission` on every mutating endpoint
- Standard API envelope (`data`, `meta`, `errors`)
- Integration test for tenant isolation on new resources
- OpenAPI auto-docs updated
- No secrets in git
- Frontend: no raw `fetch` outside `src/api/`

---

## 8. Post-MVP Roadmap (Months 7–18)

Per `ROADMAP.md` and `ADVANCED_FEATURES_ROADMAP.md`:

| Phase | Timeline | Focus |
|-------|----------|-------|
| Phase 4 | Q2 2027 | AI-assisted clinical features |
| Phase 5 | Q3–Q4 2027 | Mobile apps, API marketplace, integrations |
| Ecosystem | 2027+ | HL7/FHIR, telemedicine, white-label |

**Rule:** No Phase 4+ work until G5 passed and 10 paying tenants onboarded.

---

## 9. Planning Artifacts Cross-Reference

| Need | Read |
|------|------|
| Sprint tasks + hours | `03_SPRINT_PLAN_DETAILED.md` |
| Module DB/API/UI breakdown | `04_MODULE_PLAN.md` |
| Task IDs + status | `05_TASK_BACKLOG.md` |
| What blocks what | `06_DEPENDENCY_MATRIX.md` |
| Go/no-go gates | `07_GATES_RISKS_DOD.md` |
| Cursor implementation prompts | `08_CURSOR_COMPOSER_MASTER_PROMPT.md` |
| Original research | `docs/` folder |
