# Development Checklist

## Pre-Coding Gate & Daily Development Tracker

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Active |
| **Last Updated** | June 2026 |
| **Author** | Technical Project Management |
| **Purpose** | Complete all items **before coding begins**; reuse daily to track progress and prevent rework |
| **Related Docs** | `DEVELOPMENT_READINESS_REPORT.md`, `SPRINT_1_EXECUTION_GUIDE.md`, `IMPLEMENTATION_PLAN.md`, `PROJECT_STRUCTURE.md` |

---

## How to Use This Checklist

### Before coding (one-time gate)

Complete **every section** below before writing application code. Items are ordered roughly by dependency. Do not skip ahead to Sprint 2 (auth) until the **Documentation Reconciliation** and **Database Preparation** sections are fully checked.

### Daily during development

| When | Action |
|------|--------|
| **Start of day** | Pull latest `dev`; review today's sprint task; scan unchecked items in relevant section |
| **Before each commit** | Run local lint + tests; confirm no secrets in `git diff` |
| **End of day** | Update checkboxes; note blockers in sprint journal |
| **Before merge to `dev`** | Complete the [Daily Merge Checklist](#daily-merge-checklist) at the bottom |

### Progress summary

Update these counts as you complete items:

| Section | Done | Total |
|---------|------|-------|
| Documentation Validation | 0 | 32 |
| Database Preparation | 0 | 28 |
| Backend Preparation | 0 | 35 |
| Frontend Preparation | 0 | 22 |
| Security Preparation | 0 | 26 |
| Multi-Tenant Preparation | 0 | 24 |
| RBAC Preparation | 0 | 20 |
| Git Setup | 0 | 18 |
| Environment Setup | 0 | 30 |
| **Grand total** | **0** | **235** |

> Totals are approximate — sub-items may be added as the project evolves. Update the table when items change.

---

## 1. Documentation Validation

Confirm documentation is read, understood, and conflicts resolved **before** implementation decisions are made.

### 1.1 Core documents read

- [ ] Read `PRD.md` — MVP scope, personas, and out-of-scope items understood
- [ ] Read `PROJECT_STRUCTURE.md` (frozen v2.0) — folder layout memorized; no restructuring without approval
- [ ] Read `SYSTEM_ARCHITECTURE.md` — stack, deployment model, and cross-cutting concerns understood
- [ ] Read `DATABASE_DESIGN.md` — 8 schemas, 61 tables, composite FK pattern understood
- [ ] Read `MULTI_TENANT_DESIGN.md` — tenant isolation, provisioning, RLS rules understood
- [ ] Read `RBAC_DESIGN.md` — role codes and permission matrices understood (authoritative for roles)
- [ ] Read `SECURITY_ARCHITECTURE.md` — auth, JWT, session, and permission resolution strategy understood
- [ ] Read `API_DESIGN.md` §2 — response envelope, error format, pagination conventions understood
- [ ] Read `IMPLEMENTATION_PLAN.md` — 12-sprint sequence, gates G1–G5, and solo workflow understood
- [ ] Read `SPRINT_PLAN.md` — current sprint scope and hour estimates understood
- [ ] Read `DEVELOPMENT_READINESS_REPORT.md` — known gaps, risks, and Go/No-Go verdict understood

### 1.2 Supporting guides read

- [ ] Read `SPRINT_1_EXECUTION_GUIDE.md` — Sprint 1 tasks, phases, and acceptance criteria understood
- [ ] Read `FOUNDATION_DATABASE_GUIDE.md` — tenants, users, roles, permissions model understood
- [ ] Read `AUTHENTICATION_ARCHITECTURE_GUIDE.md` — login flow, JWT claims, refresh rotation understood (Sprint 2 prep)
- [ ] Read `database/migrations-readme.md` — Alembic vs baseline SQL workflow understood
- [ ] Read root `README.md` — quick-start commands verified or flagged for update

### 1.3 Cross-document conflicts resolved (mandatory before Sprint 2)

- [ ] **C-01:** JWT strategy decided — permissions resolved **server-side** (Redis + DB), **not** in JWT (`SECURITY_ARCHITECTURE.md` wins)
- [ ] **C-02:** Role codes standardized — use `hospital_owner`, `hospital_admin`, `accountant` (not `tenant_admin`, `billing_staff`)
- [ ] **C-03:** Admin API paths aligned — follow `PROJECT_STRUCTURE.md` routers (`staff.py`, `subscription.py`)
- [ ] **C-04:** Permission namespace unified — `laboratory:*` (not `lab:*`) per `API_DESIGN.md`
- [ ] **C-05:** Inventory API path confirmed — `/api/v1/inventory` per `API_DESIGN.md`
- [ ] **C-06:** Worker technology aligned — SQS (not Celery) per `PROJECT_STRUCTURE.md`
- [ ] **C-07:** MVP scope tension acknowledged — PRD vs `IMPLEMENTATION_PLAN` timing documented in sprint journal
- [ ] **C-08:** Tenant provisioning seed roles match `RBAC_DESIGN.md` §2.2 (not `MULTI_TENANT_DESIGN.md` §3.4 examples)

### 1.4 Documentation gaps logged (do not block Sprint 1)

- [ ] Gap logged: OPD API spec missing from `API_DESIGN.md` — target Sprint 4 start
- [ ] Gap logged: IPD API spec missing — target Sprint 5 start
- [ ] Gap logged: `DEPLOYMENT_GUIDE.md` absent — target Sprint 12
- [ ] Gap logged: `TESTING_STRATEGY.md` absent — interim: `IMPLEMENTATION_PLAN.md` §13
- [ ] Gap logged: UI/UX wireframes absent — plan lightweight mockups before Sprint 2 UI
- [ ] Gap logged: Regional compliance (India PHI, consent) — legal review before beta
- [ ] PRD sign-off table status noted (stakeholder approval trail)

### 1.5 Authoritative source precedence confirmed

- [ ] **Folder structure:** `PROJECT_STRUCTURE.md` (frozen) overrides `IMPLEMENTATION_PLAN.md` §9 examples
- [ ] **Roles & permissions:** `RBAC_DESIGN.md` overrides examples in `DATABASE_DESIGN.md` and `SYSTEM_ARCHITECTURE.md`
- [ ] **Security controls:** `SECURITY_ARCHITECTURE.md` overrides JWT examples in `SYSTEM_ARCHITECTURE.md`
- [ ] **API conventions:** `API_DESIGN.md` §2 is binding for all new endpoints
- [ ] **Database schema:** `database/baseline/schema.sql` is baseline; runtime changes via Alembic only

---

## 2. Database Preparation

Confirm PostgreSQL artifacts, tooling, and seed strategy are ready before backend models are written.

### 2.1 Baseline schema review

- [ ] `database/baseline/schema.sql` exists and is treated as **read-only reference**
- [ ] Confirmed 8 PostgreSQL schemas: `platform`, `core`, `clinical`, `billing`, `laboratory`, `pharmacy`, `inventory`, `audit`
- [ ] Confirmed 61 `CREATE TABLE` statements present
- [ ] RLS policies present in baseline for tenant-scoped tables
- [ ] `platform.create_tenant()` function exists at end of `schema.sql`
- [ ] Composite foreign keys (`tenant_id` + entity `id`) verified in foundation tables
- [ ] System tenant UUID `00000000-0000-0000-0000-000000000001` documented and understood
- [ ] Skimmed table list for Sprint 1 scope: `platform.*` + `core.users`, `roles`, `permissions`, `user_roles`, `role_permissions`

### 2.2 Local database infrastructure

- [ ] `docker-compose.yml` created with `postgres:14` service (`hms_dev` database)
- [ ] `docker-compose.test.yml` created for CI (`hms_test` on separate port)
- [ ] `docker compose up -d postgres` succeeds
- [ ] `psql` connects to `hms_dev` with documented credentials
- [ ] Postgres data persisted via named Docker volume
- [ ] Postgres health verified (`SELECT version();` returns 14.x)

### 2.3 Alembic migration setup

- [ ] `backend/alembic.ini` configured with correct `DATABASE_URL`
- [ ] `backend/alembic/env.py` imports SQLAlchemy `Base` and all Sprint 1 models
- [ ] Initial revision `001_baseline.py` created from `schema.sql`
- [ ] `alembic upgrade head` succeeds on **empty** database
- [ ] `alembic downgrade -1` tested (rollback works)
- [ ] `alembic current` shows expected revision after upgrade
- [ ] Confirmed: no direct edits to production DB — all changes through Alembic versions

### 2.4 Seed data preparation

- [ ] `database/seeds/` directory structure planned per `SPRINT_1_EXECUTION_GUIDE.md`
- [ ] `database/seeds/01_system_tenant.sql` drafted or scripted
- [ ] `database/seeds/02_subscription_plans.sql` drafted (trial, basic, professional)
- [ ] `database/seeds/03_permissions.sql` drafted (~50–80 permission codes per `RBAC_DESIGN.md`)
- [ ] `backend/scripts/seed.py` created — idempotent (safe to run twice)
- [ ] Seed script inserts system tenant, plans, and permission catalog
- [ ] `python -m scripts.seed` runs without error after `alembic upgrade head`
- [ ] Seed data verified in DB: `SELECT count(*) FROM core.permissions WHERE tenant_id = system_tenant_uuid`

### 2.5 SQLAlchemy models (Sprint 1 scope)

- [ ] `backend/app/models/base.py` — `TenantMixin`, `AuditMixin`, `SoftDeleteMixin` defined
- [ ] `backend/app/models/platform.py` — `tenants`, `subscription_plans`, `tenant_subscriptions`, `tenant_settings`, `tenant_locations`
- [ ] `backend/app/models/core.py` — `users`, `roles`, `permissions`, `user_roles`, `role_permissions` (Sprint 1); patient models optional
- [ ] Model `__tablename__` and `__table_args__` match schema names (`platform.tenants`, `core.users`, etc.)
- [ ] Alembic autogenerate diff reviewed — no unexpected drift vs baseline

### 2.6 Database testing readiness

- [ ] Test database URL configured (`hms_test`) in `conftest.py`
- [ ] Integration test can run `alembic upgrade head` on test DB before tests
- [ ] `test_tenant_isolation.py` scaffold exists (even if minimal in Sprint 1)
- [ ] CI job applies migrations before running pytest

---

## 3. Backend Preparation

Confirm FastAPI scaffold, project layout, and core patterns exist before domain features.

### 3.1 Project scaffold

- [ ] `backend/` directory structure matches `PROJECT_STRUCTURE.md` §3
- [ ] `backend/app/main.py` — app factory with lifespan hooks
- [ ] `backend/pyproject.toml` — ruff, pytest, mypy (if used) configured
- [ ] `backend/requirements.txt` — FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, psycopg2/asyncpg
- [ ] `backend/requirements-dev.txt` — pytest, httpx, ruff, factory-boy (if used)
- [ ] Python virtual environment created (`.venv/`)
- [ ] `pip install -r requirements.txt -r requirements-dev.txt` succeeds
- [ ] `backend/keys/.gitkeep` exists (JWT keys generated in Sprint 2, not committed)

### 3.2 Core application layer

- [ ] `backend/app/core/config.py` — Pydantic `Settings` loads from `.env.local`
- [ ] `backend/app/core/database.py` — engine, `SessionLocal`, `get_db` dependency
- [ ] `backend/app/core/logging.py` — structured JSON logging with correlation ID
- [ ] `backend/app/core/response.py` — `APIResponse` envelope `{ data, meta, errors }`
- [ ] `backend/app/core/exceptions.py` — domain exception base classes
- [ ] `backend/app/core/exception_handlers.py` — maps exceptions to envelope + HTTP status
- [ ] `backend/app/core/middleware.py` — registers middleware chain in correct order
- [ ] `backend/app/core/security.py` — stub only (Sprint 2)
- [ ] `backend/app/core/permissions.py` — stub only (Sprint 2)

### 3.3 API layer (Sprint 1 minimum)

- [ ] `backend/app/api/v1/router.py` — aggregates v1 routers
- [ ] `backend/app/api/v1/health.py` — `GET /health` returns 200
- [ ] `backend/app/api/v1/health.py` — `GET /health/ready` checks DB connectivity
- [ ] `backend/app/api/v1/deps.py` — pagination stubs
- [ ] Routers call `domains/*/services/` only — **no direct DB access in routers**
- [ ] OpenAPI docs available at `/docs` when server runs
- [ ] CORS configured for `http://localhost:5173` (frontend dev server)

### 3.4 Domain layer (Sprint 1 minimum)

- [ ] `backend/app/domains/platform/services/tenant_service.py` — stub or minimal read
- [ ] `backend/app/domains/platform/repositories/tenant_repository.py` — tenant queries
- [ ] `backend/app/domains/platform/schemas/tenant.py` — Pydantic response schemas
- [ ] `backend/app/domains/identity/` folders created (empty — Sprint 2)
- [ ] `backend/app/repositories/base.py` — `TenantScopedRepository` injects `tenant_id` filter

### 3.5 Tenant middleware (Sprint 1 stub)

- [ ] `backend/app/core/tenant/context.py` — `tenant_db_session`, `SET LOCAL app.tenant_id`
- [ ] `backend/app/core/tenant/middleware.py` — dev stub (header or default tenant for testing)
- [ ] `backend/app/core/tenant/resolver.py` — stub (subdomain lookup in Sprint 2)

### 3.6 Backend verification

- [ ] `uvicorn app.main:app --reload --port 8000` starts without errors
- [ ] `GET http://localhost:8000/health` → 200
- [ ] `GET http://localhost:8000/health/ready` → 200 when DB is up
- [ ] Response body matches API envelope format
- [ ] Correlation ID appears in logs for each request
- [ ] `ruff check .` passes (or equivalent linter)
- [ ] `pytest` passes locally

### 3.7 Deferred backend items acknowledged (not Sprint 1)

- [ ] Not building: `worker/handlers/` (Sprint 4+)
- [ ] Not building: `api/v1/auth.py` implementation (Sprint 2)
- [ ] Not building: `infrastructure/terraform/` (Sprint 4+ staging)
- [ ] Not building: SQS adapter live integration (Sprint 4+)

---

## 4. Frontend Preparation

Confirm React SPA scaffold and API client patterns exist before feature UI.

### 4.1 Project scaffold

- [ ] `frontend/` initialized with Vite + React 18 + TypeScript
- [ ] `frontend/package.json` — scripts: `dev`, `build`, `lint`, `test`
- [ ] `frontend/vite.config.ts` — dev server port 5173; API proxy if needed
- [ ] `frontend/tsconfig.json` — strict mode enabled
- [ ] `frontend/tailwind.config.ts` — Tailwind configured
- [ ] `frontend/src/index.css` — Tailwind directives imported
- [ ] `npm install` succeeds without errors
- [ ] `npm run dev` starts at `http://localhost:5173`

### 4.2 API client layer

- [ ] `frontend/src/api/client.ts` — axios/fetch wrapper with base URL from env
- [ ] `frontend/src/api/types.ts` — `APIResponse<T>` mirrors backend envelope
- [ ] `frontend/src/api/endpoints/health.ts` — calls `GET /health`
- [ ] API client handles correlation ID header (read or generate)
- [ ] Error responses parsed from `errors` array in envelope

### 4.3 Layout and routing (Sprint 1 shell)

- [ ] `frontend/src/routes/index.tsx` — home route + 404
- [ ] `frontend/src/components/layout/AppLayout.tsx` — sidebar + header skeleton
- [ ] `frontend/src/components/layout/AuthLayout.tsx` — centered layout placeholder
- [ ] `frontend/src/lib/constants.ts` — API URL, app name
- [ ] `frontend/src/styles/tokens.ts` — color/spacing placeholders
- [ ] Home page displays health check result from API (proves end-to-end connectivity)

### 4.4 Frontend tooling

- [ ] `frontend/.env.example` created with `VITE_API_BASE_URL`
- [ ] `frontend/.env.local` created (gitignored) from example
- [ ] ESLint configured and `npm run lint` passes
- [ ] `npm run build` succeeds without errors

### 4.5 Deferred frontend items acknowledged (not Sprint 1)

- [ ] Not building: `features/` modules (Sprint 2+)
- [ ] Not building: auth pages, login form (Sprint 2)
- [ ] Not building: full design system / wireframes (iterative)
- [ ] Not building: `PermissionGuard` component (Sprint 2)

---

## 5. Security Preparation

Confirm security architecture is understood and foundational controls are planned before auth implementation.

### 5.1 Security architecture decisions locked

- [ ] Access token: JWT RS256, 30-minute TTL, stored in memory only (not localStorage)
- [ ] Refresh token: opaque, HttpOnly cookie, 7-day TTL, rotation on use
- [ ] JWT claims minimal: `sub`, `tenant_id`, `roles`, `jti` — **no permissions in JWT**
- [ ] Permissions resolved server-side via Redis cache + DB (`RBAC_DESIGN.md` + `SECURITY_ARCHITECTURE.md`)
- [ ] Password hashing: bcrypt with documented cost factor
- [ ] Account lockout policy chosen: 5 failed attempts → lockout (15 or 30 min — pick one, document it)
- [ ] Session storage: `core.user_sessions` table (Sprint 2)
- [ ] Token denylist: Redis keyed by `jti` for logout/revocation (Sprint 2)

### 5.2 Key and secret management

- [ ] `backend/keys/` directory exists; `*.pem` in `.gitignore`
- [ ] Plan for JWT key generation documented (`openssl` or script — Sprint 2)
- [ ] `.env`, `.env.local`, `backend/keys/*.pem` in `.gitignore`
- [ ] No secrets committed to git (verified with `git log` spot check)
- [ ] `.env.example` files contain placeholders only — no real credentials
- [ ] Production secrets plan: AWS Secrets Manager (documented for Sprint 12)

### 5.3 Application security controls (planned or stubbed)

- [ ] CORS allowlist configured (not `*` in production)
- [ ] Rate limiting strategy documented (`SECURITY_ARCHITECTURE.md`) — implement Sprint 2+
- [ ] Input validation strategy: Pydantic on all request bodies
- [ ] SQL injection prevention: SQLAlchemy ORM only; no raw string concatenation
- [ ] XSS prevention: React escapes by default; no `dangerouslySetInnerHTML` without review
- [ ] CSRF strategy for cookie-based refresh token documented
- [ ] Security headers plan documented (HSTS, X-Content-Type-Options — production)

### 5.4 Audit and compliance readiness

- [ ] `audit.audit_logs` table exists in baseline — wiring planned for Sprint 2+
- [ ] PHI access logging (`audit.phi_access_logs`) noted as Sprint 11 deliverable
- [ ] Soft delete pattern understood — no hard delete of clinical data
- [ ] Data retention policy (90-day cancelled tenant) understood from `MULTI_TENANT_DESIGN.md`
- [ ] 2FA for Owner/Admin noted as Sprint 11 — not blocking MVP
- [ ] Penetration test scheduled before production (Gate G5)

### 5.5 Security testing readiness

- [ ] Tenant isolation integration test scaffold exists
- [ ] RBAC denial test plan documented for Sprint 2
- [ ] No `print()` / `console.log()` with sensitive data in committed code
- [ ] Dependency vulnerability scan planned (`pip audit`, `npm audit` in CI)

---

## 6. Multi-Tenant Preparation

Confirm tenant isolation is designed, implemented at DB layer, and testable at app layer.

### 6.1 Tenancy model understood

- [ ] Shared database + `tenant_id` column on every tenant-scoped table
- [ ] Hospital = `platform.tenants` row (no separate `hospitals` table)
- [ ] Branches = `platform.tenant_locations`
- [ ] Subdomain maps to tenant (`apollo.platform.com` → `tenants.subdomain = 'apollo'`)
- [ ] JWT `tenant_id` is authoritative after login — never trust client-supplied `tenant_id` in body
- [ ] System tenant UUID used only for seed data, not real hospitals

### 6.2 Row-Level Security (RLS)

- [ ] RLS policies exist in `database/baseline/schema.sql`
- [ ] App sets `SET LOCAL app.tenant_id = '<uuid>'` at start of each DB transaction
- [ ] `tenant_db_session` context manager implemented in `core/tenant/context.py`
- [ ] RLS tested: query without `SET LOCAL` returns no tenant data (or fails safely)
- [ ] RLS tested: tenant A cannot read tenant B rows even with guessed UUID

### 6.3 Application-layer isolation

- [ ] `TenantScopedRepository` auto-filters all queries by `tenant_id`
- [ ] Composite FK pattern understood — `(tenant_id, user_id)` prevents cross-tenant links
- [ ] `UNIQUE(tenant_id, email)` on users — same email allowed at different tenants
- [ ] Tenant middleware extracts context before route handlers run
- [ ] Platform admin routes (future) bypass tenant context via explicit `is_platform_admin` check

### 6.4 Tenant provisioning flow understood

- [ ] Registration creates: tenant → subscription → primary location → cloned roles → owner user
- [ ] `platform.create_tenant()` function behavior reviewed in `schema.sql`
- [ ] Role/permission clone pattern: copy from system tenant to new tenant on signup
- [ ] Trial status and seat limits enforced per `tenant_subscriptions` (Sprint 2+)

### 6.5 Multi-tenant testing

- [ ] `tests/integration/test_tenant_isolation.py` exists
- [ ] Test creates two tenants and proves data separation
- [ ] Test verifies `TenantScopedRepository` injects correct `tenant_id`
- [ ] CI runs isolation test on every PR
- [ ] Manual test checklist documented: create two tenants, cross-access attempt returns 404/403

---

## 7. RBAC Preparation

Confirm role-based access control design is understood and seed data aligns before auth Sprint.

### 7.1 RBAC model understood

- [ ] Chain memorized: `users` → `user_roles` → `roles` → `role_permissions` → `permissions`
- [ ] Permissions are atomic actions: `{module}:{action}` (e.g. `patient:read`)
- [ ] Roles group permissions (e.g. `doctor`, `receptionist`)
- [ ] Users can have multiple roles; effective permissions = union of all role permissions
- [ ] API checks permission codes, not role names
- [ ] UI hides unauthorized actions; API always re-checks (UI is not security)

### 7.2 Standard roles confirmed

- [ ] `hospital_owner` — full tenant access
- [ ] `hospital_admin` — operations admin
- [ ] `doctor` — clinical consultation access
- [ ] `receptionist` — front desk, appointments, patient registration
- [ ] `nurse` — IPD nursing (Phase 2)
- [ ] `accountant` — billing and invoices
- [ ] `pharmacist` — pharmacy module (Phase 2)
- [ ] `lab_technician` — laboratory module (Phase 2)
- [ ] `is_system = true` on protected roles — cannot be deleted

### 7.3 Permission catalog readiness

- [ ] Full permission list reviewed in `RBAC_DESIGN.md` §3–4
- [ ] Permission codes in seeds match `RBAC_DESIGN.md` (not outdated `DATABASE_DESIGN.md` examples)
- [ ] `role_permissions` seed mappings planned per `RBAC_DESIGN.md` matrices
- [ ] Permission cache key pattern understood: `tenant:{id}:permissions:{user_id}`
- [ ] Cache invalidation on role change documented (TTL ~5 min + explicit invalidation)

### 7.4 RBAC implementation plan (Sprint 2)

- [ ] `@requires_permission("patient:read")` decorator pattern planned
- [ ] `GET /auth/me` returns user profile + effective permissions for frontend
- [ ] `PermissionGuard` React component planned for Sprint 2
- [ ] Last `hospital_owner` removal blocked by business rule
- [ ] 403 response format matches `API_DESIGN.md` error envelope

### 7.5 RBAC testing plan

- [ ] Test: user without `patient:create` gets 403 on POST `/patients`
- [ ] Test: user with `doctor` role has `opd:consult` but not `billing:void`
- [ ] Test: permission cache invalidates after role assignment change
- [ ] Test: deactivated user (`status = inactive`) cannot authenticate

---

## 8. Git Setup

Confirm version control workflow, branch strategy, and repository hygiene before daily commits.

### 8.1 Repository initialization

- [ ] Git repository initialized and remote connected (`origin`)
- [ ] `main` branch exists and is protected (no direct commits if team policy applies)
- [ ] `dev` branch created as integration branch for daily work
- [ ] Current working branch confirmed (`git branch --show-current`)
- [ ] `git pull origin dev` succeeds at start of each day

### 8.2 Ignore and editor config

- [ ] Root `.gitignore` covers: `.env`, `.env.local`, `__pycache__`, `.pytest_cache`, `node_modules`, `dist/`, `build/`, `.venv/`, `backend/keys/*.pem`
- [ ] Root `.editorconfig` exists — indent 4 for Python, 2 for TS/JSON
- [ ] No tracked files contain secrets (`git secrets` scan or manual review)
- [ ] Large binaries and build artifacts not committed

### 8.3 Branch strategy (solo developer)

- [ ] Strategy understood: `feature/*` → `dev` → `main` (sprint end)
- [ ] Feature branch naming convention agreed: `feature/sprint-N-short-description`
- [ ] No force push to `main` — team rule acknowledged
- [ ] Sprint end merge process understood: regression on staging → merge `dev` → `main` → tag

### 8.4 Commit conventions

- [ ] Conventional commit format understood: `feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`
- [ ] Commits are focused — one logical change per commit
- [ ] Commit messages describe **why**, not just what
- [ ] No WIP commits merged to `dev` without passing CI

### 8.5 CI/CD pipeline

- [ ] `.github/workflows/ci.yml` created
- [ ] CI triggers on push to `dev` and on pull requests
- [ ] CI steps: lint (ruff + eslint) → pytest → tenant isolation test
- [ ] CI uses `docker-compose.test.yml` for ephemeral Postgres
- [ ] CI status checked before end of day if code was pushed
- [ ] Failed CI blocks merge — fix before proceeding

### 8.6 Repository hygiene

- [ ] `README.md` at root documents clone, docker, backend, frontend quick-start
- [ ] No unrelated files in repo root
- [ ] Documentation lives in `docs/` — not scattered in code folders

---

## 9. Environment Setup

Confirm local machine, tools, and environment variables are ready for development.

### 9.1 Prerequisites installed

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Node.js 20 LTS installed (`node --version`)
- [ ] Docker Desktop installed and running (`docker --version`)
- [ ] Docker Compose v2 available (`docker compose version`)
- [ ] PostgreSQL client (`psql`) installed — optional but recommended
- [ ] Git installed (`git --version`)
- [ ] Code editor configured (VS Code / Cursor recommended)
- [ ] AWS CLI v2 installed — required for staging deploy (Sprint 4+)

### 9.2 Repository cloned and opened

- [ ] Repository cloned to local machine
- [ ] Opened in IDE at monorepo root (`hospital-management-saas/`)
- [ ] Terminal working directory confirmed

### 9.3 Infrastructure services running

- [ ] `docker compose up -d postgres redis` succeeds
- [ ] Postgres accessible on `localhost:5432`
- [ ] Redis accessible on `localhost:6379`
- [ ] `redis-cli ping` returns `PONG`
- [ ] Docker volumes persist data across restarts

### 9.4 Backend environment

- [ ] `backend/.env.example` created with all required variables documented
- [ ] `backend/.env.local` created from example (gitignored)
- [ ] `DATABASE_URL` points to `hms_dev` on localhost
- [ ] `REDIS_URL` points to `redis://localhost:6379/0`
- [ ] `ENVIRONMENT=development` set
- [ ] Python venv activated: `backend/.venv`
- [ ] Dependencies installed: `pip install -r requirements.txt -r requirements-dev.txt`
- [ ] `alembic upgrade head` succeeds
- [ ] `python -m scripts.seed` succeeds
- [ ] `uvicorn app.main:app --reload --port 8000` runs

### 9.5 Frontend environment

- [ ] `frontend/.env.example` created
- [ ] `frontend/.env.local` created with `VITE_API_BASE_URL=http://localhost:8000`
- [ ] `npm install` succeeds
- [ ] `npm run dev` serves at `http://localhost:5173`
- [ ] Browser shows app; health check call to API succeeds

### 9.6 Environment variable reference verified

| Variable | Set in `.env.local` | Verified |
|----------|---------------------|----------|
| `DATABASE_URL` | Backend | [ ] |
| `REDIS_URL` | Backend | [ ] |
| `ENVIRONMENT` | Backend | [ ] |
| `JWT_PRIVATE_KEY_PATH` | Backend (Sprint 2) | [ ] |
| `JWT_PUBLIC_KEY_PATH` | Backend (Sprint 2) | [ ] |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Backend (Sprint 2) | [ ] |
| `AWS_REGION` | Backend (Sprint 4+) | [ ] |
| `S3_BUCKET` | Backend (Sprint 4+) | [ ] |
| `VITE_API_BASE_URL` | Frontend | [ ] |

### 9.7 End-to-end smoke test

- [ ] Full stack starts: Docker (postgres + redis) + backend + frontend
- [ ] `GET /health` → 200 from browser or curl
- [ ] `GET /health/ready` → 200 with DB connected
- [ ] Frontend home page loads and displays API health status
- [ ] Logs show correlation ID per request
- [ ] No errors in terminal output during smoke test

### 9.8 Environment progression understood

- [ ] **Development** — local Docker, `hms_dev` database
- [ ] **Staging** — AWS ECS, push to `dev` triggers deploy (Sprint 4+)
- [ ] **Production** — manual promote from staging (Sprint 12)
- [ ] Environment-specific secrets never shared between environments

---

## Pre-Coding Gate Sign-Off

All sections above must be complete before Sprint 1 feature coding is considered **officially started**.

| Gate | Requirement | Status |
|------|-------------|--------|
| **G0 — Pre-coding** | All 9 sections checked | [ ] Not started / [ ] In progress / [ ] Complete |
| **G1 — Sprint 1** | Docker runs; Alembic baseline; isolation test scaffold passes | [ ] |
| **G2 — Sprint 2** | Auth + RBAC; doc conflicts C-01–C-08 resolved | [ ] |

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Reviewer (optional) | | | |

---

## Daily Merge Checklist

Complete before every merge to `dev` (from `IMPLEMENTATION_PLAN.md` §11.4).

- [ ] `tenant_id` filter on all new database queries
- [ ] RBAC permission decorator on all new protected endpoints (Sprint 2+)
- [ ] Pydantic validation on all new request bodies
- [ ] Unit test for new business logic
- [ ] Integration test for tenant isolation (if new data-access endpoint)
- [ ] No secrets, API keys, or `.env` files in commit
- [ ] OpenAPI docs reflect new/changed endpoints
- [ ] No debug `print()` / `console.log()` left in code
- [ ] `ruff check` / `npm run lint` passes locally
- [ ] `pytest` passes locally
- [ ] CI pipeline green on branch

---

## Sprint Journal Template

Copy this block into your daily notes:

```
Date: ___________
Sprint: ___  Day: ___

Today's goal:
- 

Checklist sections touched:
- [ ] Documentation  [ ] Database  [ ] Backend  [ ] Frontend
- [ ] Security  [ ] Multi-Tenant  [ ] RBAC  [ ] Git  [ ] Environment

Completed today:
- 

Blockers:
- 

Tomorrow:
- 
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Technical Project Management | Initial development checklist |

---

*Update checkbox counts in the Progress Summary when items are added or removed. For sprint-specific task detail, see `SPRINT_1_EXECUTION_GUIDE.md`.*
