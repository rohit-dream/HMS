# Cursor Composer Master Prompts

Copy-paste these prompts into **Cursor Composer** (Agent mode) to execute planning or implementation work.

---

## PROMPT 1 — Generate / Refresh Full SDLC Plan (Use Once)

```
Act as a Senior Project Manager with 20+ years of experience in healthcare SaaS delivery.

PROJECT: Multi-Tenant Hospital Management SaaS
PATH: c:\My-Dream\HMS\hospital-management-saas
TEAM: 1 solo full-stack developer
STACK: FastAPI + PostgreSQL + React + TypeScript + Tailwind + Redis + AWS

STEP 1 — RESEARCH (read-only, do not skip any file):
Read and synthesize ALL markdown research files in:
- docs/ (all 30 files — PRD, FRD, NFR, USER_STORIES, SYSTEM_ARCHITECTURE, DATABASE_DESIGN, RBAC_DESIGN, SECURITY_ARCHITECTURE, API_DESIGN, MULTI_TENANT_DESIGN, BILLING_SUBSCRIPTION, SPRINT_PLAN, ROADMAP, IMPLEMENTATION_PLAN, DEVELOPMENT_SEQUENCE, DEVELOPMENT_CHECKLIST, PROJECT_STRUCTURE, FOLDER_STRUCTURE_FREEZE, and all others)
- database/README.md, database/migrations-readme.md
- backend/README.md, frontend/README.md
- SDLC Planning/ (if exists — update, don't duplicate)

STEP 2 — AUDIT CURRENT CODE STATE:
Scan backend/app/ and frontend/src/ to determine what is implemented vs stub vs not started.
Count: Alembic migrations, API routes, domain modules, tests, frontend features.

STEP 3 — CREATE/UPDATE "SDLC Planning/" folder with these files:
1. README.md — index and quick status
2. 00_PROJECT_BASELINE_AND_STATUS.md — living status doc
3. 01_MASTER_SDLC_PLAN.md — executive overview, critical path, sprint calendar
4. 02_PHASE_PLAN.md — Phase 0–3 + stabilization with exit criteria
5. 03_SPRINT_PLAN_DETAILED.md — all 12 sprints with task IDs, hours, deliverables, status
6. 04_MODULE_PLAN.md — 15 modules: DB → API → UI → tests per module
7. 05_TASK_BACKLOG.md — DS-001 to DS-080 with status tracking
8. 06_DEPENDENCY_MATRIX.md — module graph, migration order, blockers
9. 07_GATES_RISKS_DOD.md — gates G1–G5, risk register, Definition of Done
10. 08_CURSOR_COMPOSER_MASTER_PROMPT.md — this file

PLANNING REQUIREMENTS:
- Phase-wise (0: Setup, 1: MVP, 2: Clinical, 3: Growth, Stabilization)
- Sprint-wise (12 two-week sprints, ~56 hrs each)
- Module-wise (15 modules with layer breakdown)
- Task-wise (numbered DS-001 to DS-080 with dependencies, hours, status)
- Mark completed work based on actual code audit (not stale docs)
- Identify critical path and current blockers
- Align with authoritative doc hierarchy: SECURITY > RBAC > DATABASE > API > SPRINT_PLAN

OUTPUT QUALITY:
- Enterprise depth suitable for a solo developer execution guide
- Every task has: ID, description, sprint, hours, dependencies, status, acceptance criteria
- Include mermaid diagrams for dependency graphs
- Do NOT write application code — planning documents only
- Do NOT create git commits unless asked

After completion, give me:
1. Summary of current project status (% complete per phase)
2. Top 5 next tasks in strict order
3. List of planning files created
```

---

## PROMPT 2 — Sprint Execution (Use Per Sprint)

```
Act as a Senior Full-Stack Architect executing Sprint [SPRINT_NUMBER] of the Hospital Management SaaS.

BEFORE CODING — Read these files:
1. SDLC Planning/03_SPRINT_PLAN_DETAILED.md — Sprint [SPRINT_NUMBER] section
2. SDLC Planning/05_TASK_BACKLOG.md — task statuses
3. SDLC Planning/04_MODULE_PLAN.md — relevant modules
4. SDLC Planning/06_DEPENDENCY_MATRIX.md — verify dependencies met
5. docs/RBAC_DESIGN.md + docs/SECURITY_ARCHITECTURE.md + docs/DATABASE_DESIGN.md + docs/API_DESIGN.md

CURRENT SPRINT: [SPRINT_NUMBER] — [SPRINT_THEME]
TASKS TO COMPLETE: [LIST TASK IDs, e.g., DS-021, DS-039, DS-032]

EXECUTION RULES:
- Follow vertical slice: DB migration → model → repository → service → schema → API → frontend → tests
- Backend Mon–Wed pattern: models/repos/services Tue: APIs Wed: tests
- Frontend Thu–Fri: pages, forms, hooks
- Every endpoint: tenant_id scoped + require_permission + standard envelope
- Every migration: RLS enabled
- Match existing code conventions in backend/app/
- Frontend: no fetch outside src/api/; use TanStack Query + RHF + Zod
- Write integration tests for every new API
- Do not skip tasks; do not start next sprint tasks

FOR EACH TASK:
1. State what you're building and why
2. List files to create/modify
3. Implement
4. Write tests
5. Update SDLC Planning/05_TASK_BACKLOG.md status to ✅
6. Update SDLC Planning/00_PROJECT_BASELINE_AND_STATUS.md

DEFINITION OF DONE (from SDLC Planning/07_GATES_RISKS_DOD.md):
- tenant_id isolation verified
- RBAC enforced
- Tests pass: python -m pytest tests/ -q
- Frontend: npm run typecheck passes
- No secrets committed

When sprint tasks are done, provide:
- Completion summary per task
- Test count
- What's ready for demo
- Remaining gaps for sprint deliverables
```

---

## PROMPT 3 — Module Implementation (Use Per Module)

```
Act as a Senior Backend Architect.

Implement the [MODULE_NAME] module for the Hospital Management SaaS platform.

REQUIREMENTS:
Read and follow:
- SDLC Planning/04_MODULE_PLAN.md — [MODULE_NAME] section
- docs/DATABASE_DESIGN.md — relevant tables
- docs/API_DESIGN.md — endpoint contracts
- docs/RBAC_DESIGN.md — permissions for this module
- docs/SECURITY_ARCHITECTURE.md — auth and PHI rules
- docs/FUNCTIONAL_REQUIREMENTS.md — FR IDs for this module

SCOPE FOR [MODULE_NAME]:
[LIST specific capabilities, e.g., "Create Patient, Update Patient, Search, MRN generation, allergies"]

GENERATE:
- Alembic migration (with RLS)
- SQLAlchemy models
- Pydantic schemas (create, update, response, list)
- TenantScopedRepository
- Service with business rules
- API routes with require_permission
- Integration tests (CRUD + tenant isolation + RBAC denial)
- Frontend feature folder (if UI requested): pages, hooks, api endpoints

ENSURE:
- Tenant-aware: all queries filter by tenant_id
- RBAC: correct permissions from RBAC_DESIGN.md
- Validation: Pydantic + Zod
- Response: standard envelope per API_DESIGN.md §2.3
- Audit: PHI access logged where required

DO NOT:
- Change unrelated modules
- Skip tests
- Use platform_admin for tenant users
- Store permissions in JWT

After implementation:
- Run pytest
- Update SDLC Planning/05_TASK_BACKLOG.md
- List all API endpoints created with permissions
```

---

## PROMPT 4 — Frontend Feature Slice

```
Act as a Senior Frontend Architect.

Implement the frontend for [FEATURE_NAME] in the Hospital Management SaaS React app.

READ FIRST:
- SDLC Planning/04_MODULE_PLAN.md — frontend section
- frontend/README.md — folder conventions
- docs/PROJECT_STRUCTURE.md — features/ layout
- Existing: frontend/src/api/client.ts, providers/, layouts/

BACKEND APIs AVAILABLE:
[LIST endpoints, e.g., POST /auth/login, GET /admin/users, etc.]

BUILD:
1. src/features/[feature]/api/ — TanStack Query hooks per endpoint
2. src/features/[feature]/pages/ — route pages
3. src/features/[feature]/components/ — forms, tables, modals
4. src/features/[feature]/schemas/ — Zod validation
5. Wire routes in App router
6. Add PermissionGuard where needed (permissions: [LIST])

PATTERNS TO FOLLOW:
- AuthProvider for token (memory only, not localStorage)
- Axios interceptor: 401 → refresh → retry
- React Hook Form + Zod for all forms
- TanStack Query for all API calls
- Tailwind + design tokens from styles/tokens.ts
- X-Tenant-Slug header on all API calls

ALSO IMPLEMENT (if not done):
- ProtectedRoute wrapper
- usePermissions hook
- PermissionGuard component
- Role-based post-login redirect

TEST:
- npm run typecheck
- npm run lint
- Manual smoke: login → navigate to feature → CRUD operation

Update SDLC Planning/05_TASK_BACKLOG.md when done.
```

---

## PROMPT 5 — Close Sprint 2 Gap (IMMEDIATE — Copy This Now)

```
Act as a Senior Full-Stack Architect.

The Hospital Management SaaS backend is ahead of frontend. Sprint 2 is ~55% complete.
Backend auth, RBAC, tenant provisioning, hospital admin, and user management APIs are DONE.
Frontend auth is the CRITICAL BLOCKER.

READ:
- SDLC Planning/00_PROJECT_BASELINE_AND_STATUS.md
- SDLC Planning/05_TASK_BACKLOG.md (DS-021, DS-032, DS-026, DS-039)
- docs/SECURITY_ARCHITECTURE.md
- docs/RBAC_DESIGN.md
- backend/app/api/v1/auth.py (existing endpoints)
- frontend/src/ (current shell)

IMPLEMENT IN ORDER:

TASK DS-021 — Frontend Authentication Layer (12 hrs):
- src/providers/AuthProvider.tsx — real auth state, access token in memory
- src/hooks/useAuth.ts
- src/api/endpoints/auth.ts — login, logout, refresh, me
- src/features/auth/pages/LoginPage.tsx — email, password, tenant slug
- Axios interceptor: attach Bearer token, 401 → refresh → retry
- Token must NOT be stored in localStorage

TASK DS-039 — Protected Routes (3 hrs):
- src/routes/ProtectedRoute.tsx
- src/routes/RoleRedirect.tsx — post-login redirect per role
- Redirect unauthenticated users to /login

TASK DS-032 — Registration Wizard (8 hrs):
- src/features/auth/pages/RegisterPage.tsx
- Multi-step: org name, slug, admin email/password
- Call POST /api/v1/platform/register
- Redirect to login on success

TASK DS-026 — Permission Guards (4 hrs):
- src/hooks/usePermissions.ts — from GET /auth/me permissions array
- src/components/shared/PermissionGuard.tsx
- src/lib/permissions.ts

TASK DS-037 — Email Adapter Stub (4 hrs):
- backend/app/adapters/email_adapter.py — log-only in dev
- Wire to user invite and password reset flows

RULES:
- Follow existing frontend conventions
- Match API envelope: response.data, response.meta
- X-Tenant-Slug header required
- npm run typecheck must pass
- Do not rebuild backend auth — consume existing APIs

After completion:
- Update task statuses in SDLC Planning/05_TASK_BACKLOG.md
- Provide manual test steps: register → login → see permissions → protected route works
```

---

## PROMPT 6 — Patient Module Vertical Slice (Sprint 3)

```
Act as a Senior Full-Stack Architect.

Implement the complete Patient Management vertical slice (Sprint 3).

READ:
- SDLC Planning/04_MODULE_PLAN.md — Module 5: Patient Management
- docs/DATABASE_DESIGN.md — patients, patient_allergies, patient_contacts
- docs/API_DESIGN.md §4 — patient endpoints
- docs/RBAC_DESIGN.md — patient:* permissions
- docs/FUNCTIONAL_REQUIREMENTS.md — FR-PAT section
- backend/app/api/v1/patients.py (current stub — replace)

BACKEND (DS-040, DS-041):
- Alembic migration: patients, allergies, contacts + MRN function + pg_trgm indexes + RLS
- Models, schemas, repository, service, full API
- MRN format: MRN-YYYY-NNNNN per tenant
- Duplicate phone warning (not block)
- Soft delete
- Trial plan: 100 patient cap → 402 response
- PHI audit log on patient read
- Replace stub endpoints with real implementation
- Integration tests: CRUD, isolation, RBAC, MRN uniqueness

FRONTEND (DS-042):
- src/features/patients/ — list, registration form, profile page
- Search by name/phone with pagination
- Allergies sub-section on profile
- PermissionGuard: patient:create, patient:read, patient:update

TESTS:
- pytest for all backend scenarios
- npm run typecheck

Update SDLC Planning/05_TASK_BACKLOG.md: DS-040, DS-041, DS-042 → ✅
```

---

## PROMPT 7 — Weekly Status Update (Use Every Friday)

```
Act as Project Manager.

Update the SDLC Planning folder for the Hospital Management SaaS project.

1. Scan backend/app/, frontend/src/, tests/, alembic/versions/ for changes this week
2. Update SDLC Planning/00_PROJECT_BASELINE_AND_STATUS.md with current %
3. Update SDLC Planning/05_TASK_BACKLOG.md — mark completed tasks ✅, add notes
4. Update SDLC Planning/03_SPRINT_PLAN_DETAILED.md — sprint task statuses
5. Identify blockers and update SDLC Planning/07_GATES_RISKS_DOD.md risk register

Provide weekly report:
- Sprint: [current]
- Tasks completed this week: [list]
- Tests: [count] passing
- Sprint velocity: [pts]
- % complete: Phase [X], Sprint [Y]
- Blockers: [list]
- Next week plan: [top 5 tasks]
- Gate status: G1 [✅/❌], G2 [✅/❌], etc.

Do NOT write code. Planning docs only.
```

---

## How to Use These Prompts

| When | Use Prompt |
|------|------------|
| First time / refresh all planning | **PROMPT 1** |
| Starting a new sprint | **PROMPT 2** (fill sprint number + tasks) |
| Building one backend module | **PROMPT 3** |
| Building one frontend feature | **PROMPT 4** |
| **Right now — close frontend gap** | **PROMPT 5** |
| Sprint 3 patient module | **PROMPT 6** |
| Every Friday status update | **PROMPT 7** |

## Tips for Cursor Composer

1. **Use Agent mode** for implementation prompts (2–6)
2. **Attach context**: @docs/RBAC_DESIGN.md @SDLC Planning/05_TASK_BACKLOG.md
3. **One sprint at a time** — don't combine S2 + S3 in one session
4. **Verify tests** after each prompt: `python -m pytest tests/ -q`
5. **Update backlog** after every session (Prompt 7 lite)
