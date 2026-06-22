# SDLC Planning — Hospital Management SaaS

| Field | Value |
|-------|-------|
| **Version** | 2.0 |
| **Created** | June 2026 |
| **MVP Plan** | **`09_MVP_SPRINT_PLAN_V2.md` — AUTHORITATIVE** |
| **Owner** | Project Planning (PM) |
| **Team** | 1 Solo Full-Stack Developer |
| **Duration** | 12 sprints (24 weeks) + 6 months stabilization |
| **Source of Truth** | `docs/` research files (36 markdown documents) |

---

## Purpose

This folder is the **single operational planning hub** for delivering the Multi-Tenant Hospital Management SaaS Platform. It synthesizes all research documents into actionable, sprint-ready plans.

**Use this folder when you need:**
- What to build next (task order)
- Sprint goals and hour estimates
- Module-by-module deliverables
- Dependency and gate decisions
- Cursor Composer prompts for implementation

---

## Document Index

| # | Document | Purpose |
|---|----------|---------|
| **09** | **[MVP_SPRINT_PLAN_V2.md](./09_MVP_SPRINT_PLAN_V2.md)** | **⭐ AUTHORITATIVE — Production-ready MVP roadmap (S1–S12)** |
| **10** | [MVP_TASK_BACKLOG.md](./10_MVP_TASK_BACKLOG.md) | MVP-001–MVP-120 task registry |
| **11** | [MVP_COVERAGE_MAPS.md](./11_MVP_COVERAGE_MAPS.md) | Table / API / frontend sprint maps |
| 00 | [PROJECT_BASELINE_AND_STATUS.md](./00_PROJECT_BASELINE_AND_STATUS.md) | Current code state vs plan (living document) |
| 01 | [MASTER_SDLC_PLAN.md](./01_MASTER_SDLC_PLAN.md) | Executive overview (v1 reference) |
| 02 | [PHASE_PLAN.md](./02_PHASE_PLAN.md) | Phase breakdown (v1 reference) |
| 03 | [SPRINT_PLAN_DETAILED.md](./03_SPRINT_PLAN_DETAILED.md) | **Superseded by 09** — v1 archive |
| 04 | [MODULE_PLAN.md](./04_MODULE_PLAN.md) | Module breakdown reference |
| 05 | [TASK_BACKLOG.md](./05_TASK_BACKLOG.md) | **Superseded by 10** — DS-001–DS-080 archive |
| 06 | [DEPENDENCY_MATRIX.md](./06_DEPENDENCY_MATRIX.md) | Dependency graph |
| 07 | [GATES_RISKS_DOD.md](./07_GATES_RISKS_DOD.md) | Gates G1–G5, risks, Definition of Done |
| 08 | [CURSOR_COMPOSER_MASTER_PROMPT.md](./08_CURSOR_COMPOSER_MASTER_PROMPT.md) | Cursor Composer prompts |

**New docs (project root `docs/`):** `TESTING_STRATEGY.md`, `DEPLOYMENT_GUIDE.md`, `API_DESIGN_OPD.md`

---

## Authoritative Research References

When planning conflicts arise, resolve in this order:

1. `docs/SECURITY_ARCHITECTURE.md`
2. `docs/RBAC_DESIGN.md`
3. `docs/DATABASE_DESIGN.md` + `database/baseline/schema.sql`
4. `docs/API_DESIGN.md` + `docs/API_DESIGN_OPD.md`
5. `docs/BILLING_SUBSCRIPTION.md` (SaaS billing, not patient billing)
6. **`SDLC Planning/09_MVP_SPRINT_PLAN_V2.md`** (execution order)

---

## Quick Status (June 2026)

| Area | Progress |
|------|----------|
| Sprint 1 Foundation | ~95% (backend ahead; RLS/seeds partial) |
| Sprint 2 Auth/RBAC | ~80% backend; ~0% frontend |
| Sprint 2–3 Tenant/Hospital/User | Backend largely done; frontend not started |
| Sprint 3+ Clinical | Not started (stubs only) |
| **Critical path now** | Frontend auth → patients → OPD → billing |

---

## How to Update This Folder

1. After each sprint: update `00_PROJECT_BASELINE_AND_STATUS.md` and task statuses in `10_MVP_TASK_BACKLOG.md`.
2. When scope changes: update sprint doc + module plan; log in risk register.
3. Before Composer sessions: use prompts from `08_CURSOR_COMPOSER_MASTER_PROMPT.md`.
