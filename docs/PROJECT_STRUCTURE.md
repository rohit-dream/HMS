# Project Structure — FROZEN

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 2.0 — **FROZEN** |
| **Status** | **Approved — Do Not Restructure Without Architecture Review** |
| **Effective Date** | June 2026 |
| **Author** | Principal Software Architecture |
| **Related Documents** | SYSTEM_ARCHITECTURE.md, IMPLEMENTATION_PLAN.md, DATABASE_DESIGN.md, MULTI_TENANT_DESIGN.md, SECURITY_ARCHITECTURE.md |

---

## 1. Governance

### 1.1 Freeze Declaration

This document defines the **final, production-ready repository structure** for the Hospital Management SaaS platform. It is **frozen** for the entire project lifecycle.

| Rule | Policy |
|------|--------|
| Add files within existing folders | Allowed — follow naming conventions |
| Add new domain module (backend + frontend) | Allowed — mirror existing domain pattern |
| Rename, move, or delete top-level folders | **Requires Principal Architect approval** |
| Split monorepo into multiple repos | Post-MVP decision only |
| Introduce new top-level directory | **Requires architecture review + doc update** |

### 1.2 Design Alignment

This structure implements decisions from **SYSTEM_ARCHITECTURE.md**:

| Architecture Decision | Structural Expression |
|----------------------|----------------------|
| Modular monolith | Single `backend/app/` with isolated `domains/` |
| API-first | Thin `api/v1/` layer; business logic in `domains/` |
| Multi-tenant `tenant_id` isolation | `core/tenant/`, RLS in `database/rls/`, `TenantScopedRepository` |
| Stateless API + async workers | Separate `backend/worker/` process |
| SQS (not Celery) | `adapters/queue_adapter.py` + `worker/handlers/` |
| 8 PostgreSQL schemas | `models/` and `database/schemas/` mirror schema boundaries |
| ECS Fargate deployment | `infrastructure/` with `api`, `worker`, `frontend` images |
| React SPA client | `frontend/src/features/` mirrors backend domains |

### 1.3 Technology Stack (Fixed)

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React.js 18+, TypeScript, TailwindCSS, Vite |
| **Backend** | FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2 |
| **Database** | PostgreSQL 14+ |
| **Supporting** | Redis 7+, Amazon SQS, Amazon S3 |

---

## 2. Monorepo Root

```
hospital-management-saas/
├── backend/                    # FastAPI API + SQS worker + Alembic migrations
├── frontend/                   # React TypeScript SPA
├── database/                   # PostgreSQL baseline DDL, seeds, RLS, functions
├── infrastructure/             # Docker, Terraform, deploy scripts
├── docs/                       # Architecture and product documentation
├── .github/                    # CI/CD GitHub Actions workflows
├── docker-compose.yml          # Local dev: postgres, redis, api, worker
├── docker-compose.test.yml     # CI integration test stack
├── .editorconfig               # Editor consistency rules
├── .gitignore                  # Ignored paths (secrets, build artifacts)
└── README.md                   # Developer entry point and quick-start
```

| Folder | Purpose |
|--------|---------|
| `backend/` | All server-side runtime code: REST API, background jobs, ORM models, migrations, tests |
| `frontend/` | Browser SPA for hospital staff; consumes backend REST API exclusively |
| `database/` | Authoritative SQL artifacts: baseline schema, RLS policies, seeds, DB functions |
| `infrastructure/` | AWS infrastructure-as-code, container definitions, deployment automation |
| `docs/` | Non-runtime documentation; source of truth for design decisions |
| `.github/` | Automated quality gates and deployment pipelines |

---

## 3. Backend Structure (FastAPI)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                         # App factory, lifespan hooks, middleware registration, router mount
│   │
│   ├── api/                            # HTTP presentation layer — NO business logic
│   │   ├── __init__.py
│   │   └── v1/                         # API version 1 (/api/v1)
│   │       ├── __init__.py
│   │       ├── router.py               # Aggregates all v1 routers into single APIRouter
│   │       ├── deps.py                 # Shared route dependencies (pagination, common filters)
│   │       ├── health.py               # GET /health, GET /ready — probe endpoints
│   │       ├── auth.py                 # POST /auth/* — login, register, refresh, password reset
│   │       ├── patients.py             # /patients/* — patient CRUD, allergies, import
│   │       ├── doctors.py              # /doctors/* — profiles, schedules, availability
│   │       ├── staff.py                # /staff/* — staff, departments, invites
│   │       ├── appointments.py         # /appointments/* — booking, cancel, reschedule
│   │       ├── opd.py                  # /opd/* — visits, queue, consultation, prescriptions
│   │       ├── ipd.py                  # /ipd/* — wards, beds, admissions, discharge
│   │       ├── billing.py              # /billing/* — services, invoices, payments, receipts
│   │       ├── laboratory.py           # /laboratory/* — catalog, orders, samples, reports
│   │       ├── pharmacy.py             # /pharmacy/* — medicines, dispensing, Rx queue
│   │       ├── inventory.py            # /inventory/* — stock-in, adjustments, movements
│   │       ├── reports.py              # /reports/* — dashboards, exports, analytics
│   │       ├── notifications.py        # /notifications/* — in-app, preferences
│   │       ├── locations.py            # /locations/* — tenant branches (multi-location)
│   │       ├── subscription.py         # /subscription/* — SaaS plans, billing, payment methods
│   │       ├── audit.py                # /audit/* — audit log queries
│   │       └── webhooks.py             # /webhooks/* — Razorpay callbacks (no JWT; signature auth)
│   │
│   ├── core/                           # Cross-cutting platform infrastructure
│   │   ├── __init__.py
│   │   ├── config.py                   # Pydantic Settings: env vars, feature flags, secrets references
│   │   ├── database.py                 # SQLAlchemy engine, SessionLocal, get_db() dependency
│   │   ├── security.py                 # JWT RS256, password hashing, token creation and validation
│   │   ├── dependencies.py             # FastAPI Depends: get_current_user, get_tenant, get_db
│   │   ├── permissions.py              # @requires_permission decorator, PermissionResolver
│   │   ├── middleware.py               # Middleware registration: CORS, tenant, correlation, rate limit
│   │   ├── exceptions.py               # Domain exceptions: NotFoundError, ForbiddenError, PlanLimitError
│   │   ├── exception_handlers.py       # Maps exceptions to standard API error envelope
│   │   ├── logging.py                  # Structured JSON logging, correlation ID binding
│   │   └── response.py                 # APIResponse envelope builder, pagination helpers
│   │
│   ├── core/tenant/                    # Multi-tenant isolation subsystem (dedicated)
│   │   ├── __init__.py
│   │   ├── context.py                  # SET LOCAL app.tenant_id; tenant_db_session context manager
│   │   ├── middleware.py               # Tenant resolution from JWT; subscription status gate
│   │   ├── resolver.py                 # Subdomain/slug → tenant_id lookup for login/register
│   │   └── limits.py                   # Plan limit enforcement: users, beds, patients, modules
│   │
│   ├── domains/                        # Business domain modules — scalable modular monolith
│   │   ├── __init__.py
│   │   │
│   │   ├── platform/                   # SaaS operator: tenants, subscriptions, onboarding
│   │   │   ├── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── tenant_service.py           # Tenant provisioning, settings, offboarding
│   │   │   │   ├── subscription_service.py     # Plan changes, usage metering, dunning
│   │   │   │   └── onboarding_service.py       # Onboarding wizard progress tracking
│   │   │   ├── repositories/
│   │   │   │   ├── tenant_repository.py
│   │   │   │   └── subscription_repository.py
│   │   │   └── schemas/
│   │   │       ├── tenant.py
│   │   │       └── subscription.py
│   │   │
│   │   ├── identity/                   # Authentication, users, RBAC, sessions
│   │   │   ├── services/
│   │   │   │   ├── auth_service.py             # Login, logout, refresh, password reset
│   │   │   │   ├── user_service.py             # User CRUD, invite, activation
│   │   │   │   └── rbac_service.py             # Role assignment, permission resolution
│   │   │   ├── repositories/
│   │   │   │   ├── user_repository.py
│   │   │   │   └── role_repository.py
│   │   │   └── schemas/
│   │   │       ├── auth.py
│   │   │       └── user.py
│   │   │
│   │   ├── patients/                   # Patient demographics, MRN, allergies, documents
│   │   │   ├── services/
│   │   │   │   ├── patient_service.py          # CRUD, search, duplicate detection
│   │   │   │   └── import_service.py           # CSV import validation
│   │   │   ├── repositories/
│   │   │   │   └── patient_repository.py
│   │   │   └── schemas/
│   │   │       └── patient.py
│   │   │
│   │   ├── staff/                      # Staff, departments, doctor profiles
│   │   │   ├── services/
│   │   │   │   ├── staff_service.py
│   │   │   │   └── doctor_service.py
│   │   │   ├── repositories/
│   │   │   │   ├── staff_repository.py
│   │   │   │   └── doctor_repository.py
│   │   │   └── schemas/
│   │   │       ├── staff.py
│   │   │       └── doctor.py
│   │   │
│   │   ├── clinical/                   # OPD, IPD, appointments — shared clinical domain
│   │   │   ├── services/
│   │   │   │   ├── appointment_service.py      # Booking, availability, conflicts
│   │   │   │   ├── opd_service.py              # Visits, queue, consultation, Rx
│   │   │   │   └── ipd_service.py              # Admissions, beds, nursing, discharge
│   │   │   ├── repositories/
│   │   │   │   ├── appointment_repository.py
│   │   │   │   ├── opd_repository.py
│   │   │   │   └── ipd_repository.py
│   │   │   └── schemas/
│   │   │       ├── appointment.py
│   │   │       ├── opd.py
│   │   │       └── ipd.py
│   │   │
│   │   ├── billing/                    # Hospital patient billing (NOT SaaS subscription)
│   │   │   ├── services/
│   │   │   │   └── billing_service.py          # Invoices, payments, allocations, void
│   │   │   ├── repositories/
│   │   │   │   └── billing_repository.py
│   │   │   └── schemas/
│   │   │       └── billing.py
│   │   │
│   │   ├── laboratory/                 # Lab orders, samples, results, reports
│   │   │   ├── services/
│   │   │   │   └── laboratory_service.py
│   │   │   ├── repositories/
│   │   │   │   └── laboratory_repository.py
│   │   │   └── schemas/
│   │   │       └── laboratory.py
│   │   │
│   │   ├── pharmacy/                   # Medicines, dispensing, inventory
│   │   │   ├── services/
│   │   │   │   ├── pharmacy_service.py         # Dispensing, Rx fulfillment
│   │   │   │   └── inventory_service.py        # Stock movements, alerts
│   │   │   ├── repositories/
│   │   │   │   ├── pharmacy_repository.py
│   │   │   │   └── inventory_repository.py
│   │   │   └── schemas/
│   │   │       ├── pharmacy.py
│   │   │       └── inventory.py
│   │   │
│   │   ├── communications/             # Notifications, email/SMS dispatch triggers
│   │   │   ├── services/
│   │   │   │   └── notification_service.py
│   │   │   ├── repositories/
│   │   │   │   └── notification_repository.py
│   │   │   └── schemas/
│   │   │       └── notification.py
│   │   │
│   │   ├── reporting/                  # Dashboards, aggregations, exports
│   │   │   ├── services/
│   │   │   │   └── report_service.py
│   │   │   ├── repositories/
│   │   │   │   └── report_repository.py      # Read-optimized queries; replica-ready
│   │   │   └── schemas/
│   │   │       └── report.py
│   │   │
│   │   └── audit/                      # Audit logs, PHI access logging
│   │       ├── services/
│   │       │   └── audit_service.py
│   │       ├── repositories/
│   │       │   └── audit_repository.py
│   │       └── schemas/
│   │           └── audit.py
│   │
│   ├── models/                         # SQLAlchemy ORM — organized by PostgreSQL schema
│   │   ├── __init__.py                 # Import all models for Alembic autogenerate discovery
│   │   ├── base.py                     # DeclarativeBase, TenantMixin, AuditMixin, SoftDeleteMixin
│   │   ├── platform.py                 # platform.* tables
│   │   ├── core.py                     # core.* tables (users, patients, staff, RBAC)
│   │   ├── clinical.py                 # clinical.* tables (OPD, IPD, appointments)
│   │   ├── billing.py                  # billing.* tables
│   │   ├── pharmacy.py                 # pharmacy.* tables
│   │   ├── laboratory.py               # laboratory.* tables
│   │   ├── comms.py                    # comms.* tables
│   │   └── audit.py                    # audit.* tables
│   │
│   ├── repositories/                   # Shared repository base classes
│   │   ├── __init__.py
│   │   └── base.py                     # TenantScopedRepository: _base_query(), tenant_id filter
│   │
│   └── adapters/                       # External system integrations — interface to third parties
│       ├── __init__.py
│       ├── email_adapter.py            # AWS SES transactional email
│       ├── sms_adapter.py              # MSG91 / Twilio SMS
│       ├── storage_adapter.py          # AWS S3 upload, pre-signed URLs, tenant-prefixed paths
│       ├── queue_adapter.py            # AWS SQS publish, message envelope with tenant_id
│       ├── payment_adapter.py          # Razorpay charges, subscriptions, webhook verification
│       ├── pdf_adapter.py              # PDF generation for invoices, receipts, lab reports
│       └── cache_adapter.py            # Redis: permissions cache, rate limits, dashboard TTL
│
├── worker/                             # Separate deployable process — SQS consumer
│   ├── __init__.py
│   ├── main.py                         # SQS poll loop, graceful shutdown, health signal
│   ├── registry.py                     # job_type string → handler function mapping
│   ├── context.py                      # Per-job tenant context setup (SET app.tenant_id)
│   ├── handlers/                       # Async job handlers — one file per job type
│   │   ├── __init__.py
│   │   ├── email_handler.py            # Verification, reset, billing notification emails
│   │   ├── sms_handler.py              # Appointment reminder SMS
│   │   ├── pdf_handler.py              # Invoice, receipt, lab report, discharge PDF
│   │   ├── import_handler.py           # Patient CSV bulk import
│   │   ├── billing_handler.py          # Subscription renewal, dunning retries
│   │   └── reminder_handler.py         # Daily appointment reminder batch
│   └── scheduler/                      # Cron-triggered job publishers (EventBridge / manual)
│       ├── __init__.py
│       ├── renewal_jobs.py             # Publishes subscription renewal messages to SQS
│       ├── reminder_jobs.py            # Publishes appointment reminder messages to SQS
│       └── maintenance_jobs.py         # Partition maintenance, usage snapshots
│
├── alembic/                            # Database migration control (authoritative for schema changes)
│   ├── versions/                       # Sequential revision files — never edit after deploy
│   ├── env.py                          # Alembic env: imports models, sets target_metadata
│   └── script.py.mako                  # Template for autogenerated revisions
│
├── tests/                              # Backend test suite
│   ├── __init__.py
│   ├── conftest.py                     # Fixtures: test DB, tenant A/B, role tokens, Redis mock
│   ├── unit/                           # Fast tests — no database
│   │   └── domains/                    # Mirrors app/domains/ structure
│   │       ├── platform/
│   │       ├── identity/
│   │       ├── patients/
│   │       ├── clinical/
│   │       ├── billing/
│   │       └── pharmacy/
│   ├── integration/                    # API tests with real PostgreSQL test database
│   │   ├── api/v1/                     # Mirrors app/api/v1/ routers
│   │   ├── test_tenant_isolation.py    # MANDATORY — cross-tenant leak prevention
│   │   └── test_rbac_enforcement.py    # MANDATORY — permission denial tests
│   └── fixtures/                       # Test data factories (factory-boy or manual)
│       ├── tenants.py
│       ├── users.py
│       └── patients.py
│
├── scripts/                            # Developer CLI utilities (not runtime)
│   ├── seed.py                         # Seed system tenant, plans, permissions, demo data
│   ├── create_tenant.py                # CLI: provision test tenant
│   └── generate_keys.py                # Generate RS256 JWT key pair for local development
│
├── keys/                               # Local JWT keys ONLY — gitignored except .gitkeep
│   └── .gitkeep
│
├── .env.example                        # Documented environment variable template
├── .dockerignore
├── Dockerfile                          # Multi-stage: api and worker targets
├── pyproject.toml                      # Project metadata, ruff, pytest, mypy config
├── requirements.txt                    # Production pinned dependencies
├── requirements-dev.txt                # Development and test dependencies
└── alembic.ini                         # Alembic config: script location, DB URL override
```

### 3.1 Backend Layer Responsibilities

| Layer / Folder | Responsibility | May Import From |
|----------------|----------------|-----------------|
| `api/v1/` | HTTP routing, Pydantic request validation, call domain services, return responses | `domains/`, `core/`, domain `schemas/` |
| `core/` | App infrastructure shared by all domains | `adapters/` (via interfaces) |
| `core/tenant/` | Multi-tenant context, RLS session, plan limits | `core/database.py`, `models/` |
| `domains/*/` | Business rules, orchestration, domain validation | `repositories/base`, `models/`, `adapters/`, own `schemas/` |
| `domains/*/repositories/` | Tenant-scoped data access; every query filters `tenant_id` | `models/`, `repositories/base.py` |
| `domains/*/schemas/` | Pydantic DTOs for the domain | `schemas/common` only |
| `models/` | SQLAlchemy ORM mapping to PostgreSQL tables | Nothing above repository layer |
| `repositories/base.py` | Shared `TenantScopedRepository` mixin | `models/`, `core/tenant/` |
| `adapters/` | Third-party API clients; mocked in tests | `core/config.py` |
| `worker/` | Off-request-path async processing | `domains/`, `adapters/`, `core/tenant/` |

### 3.2 Backend Request Flow

```
HTTP Request
  → core/middleware (correlation, CORS, rate limit)
  → core/tenant/middleware (JWT → tenant_id, subscription gate)
  → api/v1/{router} (validate input schema)
  → domains/{domain}/services (business logic)
  → domains/{domain}/repositories (tenant-scoped query)
  → models/ → PostgreSQL (RLS enforced)
  → Response envelope
```

### 3.3 Domain-to-PostgreSQL Schema Mapping

| Backend Domain | PostgreSQL Schema | API Router |
|----------------|-------------------|------------|
| `platform` | `platform` | `subscription.py`, `auth.py` (register) |
| `identity` | `core` (users, roles) | `auth.py`, `staff.py` |
| `patients` | `core` (patients) | `patients.py` |
| `staff` | `core` (staff, doctors) | `doctors.py`, `staff.py` |
| `clinical` | `clinical` | `opd.py`, `ipd.py`, `appointments.py` |
| `billing` | `billing` | `billing.py` |
| `laboratory` | `laboratory` | `laboratory.py` |
| `pharmacy` | `pharmacy` | `pharmacy.py`, `inventory.py` |
| `communications` | `comms` | `notifications.py` |
| `reporting` | All (read-only) | `reports.py` |
| `audit` | `audit` | `audit.py` |

### 3.4 Adding a New Backend Domain (Frozen Pattern)

When adding a post-MVP module (e.g., Operation Theater):

1. Create `app/domains/{new_domain}/` with `services/`, `repositories/`, `schemas/`
2. Add ORM models to appropriate `app/models/{schema}.py`
3. Add router `app/api/v1/{new_domain}.py` and register in `router.py`
4. Add Alembic migration in `alembic/versions/`
5. Add tests in `tests/unit/domains/{new_domain}/` and `tests/integration/api/v1/`
6. Add worker handler if async jobs required

---

## 4. Frontend Structure (React.js + TypeScript + TailwindCSS)

```
frontend/
├── public/                             # Static assets copied verbatim to build output
│   ├── favicon.ico
│   └── robots.txt
│
├── src/
│   ├── main.tsx                        # React DOM root; QueryClientProvider, RouterProvider
│   ├── App.tsx                         # Global provider tree composition
│   ├── index.css                       # Tailwind directives: @tailwind base/components/utilities
│   ├── vite-env.d.ts                   # Vite import.meta.env type declarations
│   │
│   ├── api/                            # HTTP client layer — sole gateway to backend
│   │   ├── client.ts                   # Axios instance: base URL, interceptors, 401 refresh
│   │   ├── errors.ts                   # API error parsing, toast trigger helpers
│   │   ├── types.ts                    # APIResponse<T>, PaginationMeta, ApiError types
│   │   └── endpoints/                  # One module per backend API router
│   │       ├── auth.ts
│   │       ├── patients.ts
│   │       ├── doctors.ts
│   │       ├── staff.ts
│   │       ├── appointments.ts
│   │       ├── opd.ts
│   │       ├── ipd.ts
│   │       ├── billing.ts
│   │       ├── laboratory.ts
│   │       ├── pharmacy.ts
│   │       ├── inventory.ts
│   │       ├── reports.ts
│   │       ├── notifications.ts
│   │       ├── locations.ts
│   │       ├── subscription.ts
│   │       └── audit.ts
│   │
│   ├── assets/                         # Bundled static assets (images, icons, fonts)
│   │   ├── images/
│   │   └── icons/
│   │
│   ├── components/                     # Shared UI — imported by features, never vice versa
│   │   ├── ui/                         # Design system primitives (zero business logic)
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Textarea.tsx
│   │   │   ├── Checkbox.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Pagination.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── Dropdown.tsx
│   │   │   ├── DatePicker.tsx
│   │   │   └── EmptyState.tsx
│   │   ├── layout/                     # Application shell and page structure
│   │   │   ├── AppLayout.tsx           # Authenticated layout: sidebar + header + outlet
│   │   │   ├── AuthLayout.tsx          # Unauthenticated centered layout
│   │   │   ├── Sidebar.tsx             # Role-based navigation menu
│   │   │   ├── Header.tsx              # Tenant branding, user menu, notification bell
│   │   │   ├── PageShell.tsx           # Page title, breadcrumbs, action button slot
│   │   │   └── LocationSelector.tsx    # Multi-branch location picker
│   │   └── shared/                     # Composite components used across 2+ features
│   │       ├── PermissionGuard.tsx     # Renders children only if permission granted
│   │       ├── RoleGuard.tsx           # Renders children only if role matches
│   │       ├── ConfirmDialog.tsx       # Destructive action confirmation
│   │       ├── SearchInput.tsx         # Debounced search field
│   │       ├── PatientSearchSelect.tsx # Autocomplete patient picker
│   │       ├── StatusBadge.tsx         # Tenant/subscription/record status colors
│   │       └── DataTable.tsx           # Reusable sortable table wrapper
│   │
│   ├── features/                       # Domain feature modules — mirror backend domains
│   │   ├── auth/
│   │   │   ├── index.ts                # Public exports for the feature
│   │   │   ├── pages/                  # Route-level screen components
│   │   │   ├── components/             # Feature-private UI components
│   │   │   └── hooks/                  # TanStack Query hooks for auth API
│   │   ├── patients/
│   │   │   ├── index.ts
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── opd/
│   │   │   ├── index.ts
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── ipd/
│   │   │   ├── index.ts
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── billing/
│   │   │   ├── index.ts
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── laboratory/
│   │   │   ├── index.ts
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── pharmacy/
│   │   │   ├── index.ts
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── admin/
│   │   │   ├── index.ts
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── reports/
│   │   │   ├── index.ts
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   └── subscription/
│   │       ├── index.ts
│   │       ├── pages/
│   │       ├── components/
│   │       └── hooks/
│   │
│   ├── providers/                      # React context providers (app-wide state)
│   │   ├── AppProviders.tsx            # Composes all providers in correct order
│   │   ├── AuthProvider.tsx            # User session, token, login/logout actions
│   │   ├── TenantProvider.tsx          # Tenant branding, plan, subdomain, limits
│   │   └── NotificationProvider.tsx    # Unread notification count
│   │
│   ├── hooks/                          # Global hooks (not feature-specific)
│   │   ├── useAuth.ts
│   │   ├── usePermissions.ts
│   │   ├── useTenant.ts
│   │   ├── useDebounce.ts
│   │   └── useMediaQuery.ts
│   │
│   ├── routes/                         # Routing configuration and guards
│   │   ├── index.tsx                   # Route tree with React.lazy code splitting
│   │   ├── ProtectedRoute.tsx          # Requires authentication
│   │   ├── PublicRoute.tsx             # Redirects authenticated users to dashboard
│   │   ├── PermissionRoute.tsx         # Requires specific permission
│   │   └── RoleRedirect.tsx            # Post-login landing by role
│   │
│   ├── lib/                            # Pure utilities — zero React imports
│   │   ├── constants.ts                # Role codes, plan codes, status enums
│   │   ├── formatters.ts               # Date, INR currency, phone formatting
│   │   ├── validators.ts               # Shared Zod schemas
│   │   └── permissions.ts              # canAccess(), roleNavItems mapping
│   │
│   ├── styles/                         # Global style configuration
│   │   └── tokens.ts                     # Design tokens: colors, spacing (referenced by Tailwind)
│   │
│   └── types/                          # Global TypeScript interfaces
│       ├── api.ts                      # APIResponse, Pagination, ErrorDetail
│       ├── auth.ts                     # User, Role, TokenPayload
│       ├── tenant.ts                   # Tenant, Subscription, Plan
│       ├── patient.ts
│       ├── clinical.ts
│       ├── billing.ts
│       └── index.ts                    # Re-exports all types
│
├── .env.example
├── .dockerignore
├── .eslintrc.cjs
├── .prettierrc
├── Dockerfile                          # Production: Vite build → Nginx static serve
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

### 4.1 Frontend Folder Purposes

| Folder | Purpose |
|--------|---------|
| `public/` | Files served unchanged; not processed by Vite bundler |
| `src/api/` | All HTTP communication; features never call `fetch` directly |
| `src/api/endpoints/` | Typed functions per backend module; maps 1:1 to `backend/app/api/v1/` |
| `src/assets/` | Images and icons imported into components via Vite |
| `src/components/ui/` | Design system atoms; no API calls, no domain knowledge |
| `src/components/layout/` | App shell shared by all authenticated pages |
| `src/components/shared/` | Cross-feature composites (patient search, permission guard) |
| `src/features/` | Domain screens; each subfolder is self-contained |
| `src/features/*/pages/` | Top-level route components loaded by React Router |
| `src/features/*/components/` | UI components private to the feature |
| `src/features/*/hooks/` | TanStack Query wrappers (`useQuery`, `useMutation`) |
| `src/features/*/index.ts` | Barrel export; controls public API of the feature |
| `src/providers/` | React Context for auth, tenant, notifications |
| `src/hooks/` | Global hooks consumed by multiple features |
| `src/routes/` | Route definitions, lazy imports, access guards |
| `src/lib/` | Pure functions: formatters, validators, permission helpers |
| `src/styles/` | Design token definitions consumed by Tailwind config |
| `src/types/` | TypeScript interfaces aligned with backend Pydantic schemas |

### 4.2 Frontend Import Rules (Enforced)

| Rule | Rationale |
|------|-----------|
| `features/*` may import from `components/`, `api/`, `hooks/`, `lib/`, `types/`, `providers/` | Prevents feature coupling |
| `features/*` must NOT import from other `features/*` | Domain isolation |
| `components/ui/` must NOT import from `features/` or `api/` | Design system purity |
| `lib/` must NOT import React | Testable pure functions |
| All server state via TanStack Query in `features/*/hooks/` | Consistent cache and invalidation |

### 4.3 Frontend Domain-to-Route Mapping

| Feature | Routes | Backend Domain |
|---------|--------|------------------|
| `auth` | `/login`, `/register`, `/forgot-password`, `/reset-password` | `identity`, `platform` |
| `patients` | `/patients`, `/patients/new`, `/patients/:id` | `patients` |
| `opd` | `/opd/appointments`, `/opd/queue`, `/opd/consult/:id` | `clinical` |
| `ipd` | `/ipd/wards`, `/ipd/admissions`, `/ipd/patients/:id` | `clinical` |
| `billing` | `/billing/invoices`, `/billing/collection` | `billing` |
| `laboratory` | `/lab/orders`, `/lab/results`, `/lab/reports` | `laboratory` |
| `pharmacy` | `/pharmacy/queue`, `/pharmacy/dispense`, `/pharmacy/inventory` | `pharmacy` |
| `admin` | `/dashboard`, `/admin/staff`, `/admin/settings`, `/admin/branches` | `staff`, `platform` |
| `reports` | `/reports` | `reporting` |
| `subscription` | `/admin/subscription`, `/admin/billing-history` | `platform` |

---

## 5. Database Structure (PostgreSQL)

```
database/
├── baseline/
│   └── schema.sql                      # Authoritative full DDL: 61 tables, constraints, triggers
│
├── schemas/                            # Per-schema SQL reference (subset of baseline)
│   ├── platform.sql                    # tenants, subscriptions, plans, settings, locations
│   ├── core.sql                        # users, RBAC, patients, staff, doctors
│   ├── clinical.sql                    # appointments, OPD, IPD, beds, wards
│   ├── billing.sql                     # invoices, payments, service master
│   ├── pharmacy.sql                    # medicines, inventory, dispensing
│   ├── laboratory.sql                  # test catalog, orders, samples, results
│   ├── comms.sql                       # notifications, preferences, delivery log
│   └── audit.sql                       # audit_logs, phi_access_logs
│
├── rls/                                # Row-Level Security policies
│   ├── enable_rls.sql                  # ENABLE + FORCE ROW LEVEL SECURITY on all tenant tables
│   ├── tenant_isolation.sql            # Standard tenant_id policy template
│   └── system_tenant_reads.sql         # Allow read of system tenant seed data (plans, permissions)
│
├── functions/                          # PostgreSQL stored functions and triggers
│   ├── platform_create_tenant.sql      # platform.create_tenant() — atomic provisioning
│   ├── generate_mrn.sql                # Per-tenant MRN sequence
│   ├── generate_invoice_number.sql     # Per-tenant hospital invoice numbering
│   ├── generate_visit_number.sql       # Per-tenant OPD visit numbering
│   ├── set_updated_at.sql              # Trigger function for updated_at column
│   └── enforce_tenant_self_reference.sql
│
├── indexes/                            # Performance indexes (promoted to Alembic when applied)
│   ├── tenant_isolation.sql            # UNIQUE (tenant_id, id) on all tenant tables
│   ├── patient_search.sql                # pg_trgm indexes for name/phone search
│   ├── foreign_keys.sql                # Composite FK reference documentation
│   └── report_queries.sql              # Covering indexes for dashboard aggregations
│
├── seeds/                              # Ordered seed data for development and staging
│   ├── 01_system_tenant.sql            # System tenant UUID 00000000-...-000000000001
│   ├── 02_subscription_plans.sql       # Starter, Professional, Enterprise
│   ├── 03_permissions.sql              # System permission catalog
│   ├── 04_roles.sql                    # Default role definitions
│   ├── 05_role_permissions.sql         # Role-to-permission mappings
│   ├── 06_lab_test_catalog.sql         # Common lab tests (CBC, LFT, RFT)
│   └── 07_demo_tenant.sql              # Optional demo hospital with sample data
│
├── partitions/                         # Table partitioning definitions (activate at scale)
│   └── audit_logs_partition.sql        # Monthly range partition template for audit_logs
│
├── migrations-readme.md                # How database/ relates to backend/alembic/
└── README.md                             # Setup commands, schema overview, conventions
```

### 5.1 PostgreSQL Logical Schema Layout

```
PostgreSQL Database: hms_{environment}
│
├── platform/          →  SaaS tenancy, subscriptions, tenant configuration
├── core/              →  Identity, RBAC, patients, staff, doctors
├── clinical/          →  OPD, IPD, appointments, beds
├── billing/           →  Hospital patient invoices and payments
├── pharmacy/          →  Medicines, inventory, dispensing
├── laboratory/        →  Lab orders, samples, results, reports
├── comms/             →  Notifications and delivery tracking
└── audit/             →  Immutable audit trail and PHI access logs
```

Every table in schemas `core` through `audit` includes `tenant_id UUID NOT NULL`. The `platform.tenants` table is the isolation root where `tenant_id = id`.

### 5.2 Database Folder Purposes

| Folder | Purpose |
|--------|---------|
| `baseline/schema.sql` | Complete bootstrap DDL; source of truth for initial database creation |
| `schemas/` | Per-schema SQL extracts for readability and targeted review |
| `rls/` | Row-Level Security policies; defence-in-depth tenant isolation at DB layer |
| `functions/` | Stored procedures for atomic operations (tenant creation, numbering) |
| `indexes/` | Performance index definitions; reference before creating Alembic migrations |
| `seeds/` | Ordered, idempotent seed scripts for local dev and staging environments |
| `partitions/` | Future table partitioning scripts; inactive until 50+ tenants |

### 5.3 Database Change Workflow (Frozen)

| Step | Tool | Location |
|------|------|----------|
| 1. Design change | Documentation | `docs/DATABASE_DESIGN.md` |
| 2. Update ORM models | SQLAlchemy | `backend/app/models/` |
| 3. Generate migration | Alembic | `backend/alembic/versions/` |
| 4. Update baseline reference | SQL (optional) | `database/baseline/schema.sql` (major releases only) |
| 5. Update RLS if new tenant table | SQL | `database/rls/` + Alembic migration |
| 6. Seed if reference data | SQL or Python | `database/seeds/` or `backend/scripts/seed.py` |

> **Rule:** All runtime schema changes go through **Alembic only**. Never apply ad-hoc DDL to staging or production.

### 5.4 Multi-Tenant Database Conventions (Mandatory)

| Convention | Implementation |
|------------|----------------|
| Every tenant table has `tenant_id` | Column + FK → `platform.tenants.id` |
| Business key uniqueness | `UNIQUE (tenant_id, business_key)` — e.g., MRN, invoice number |
| Cross-table references | Composite FK includes `tenant_id` on both sides |
| RLS enabled and forced | `database/rls/enable_rls.sql` on every tenant-scoped table |
| Soft delete | `deleted_at TIMESTAMPTZ` — clinical/financial records never hard-deleted |
| Audit columns | `created_at`, `created_by`, `updated_at`, `updated_by`, `version` |
| Immutable logs | `audit.audit_logs`, `audit.phi_access_logs` — append-only, no soft delete |

---

## 6. Infrastructure Structure

```
infrastructure/
├── docker/
│   ├── api/Dockerfile
│   ├── worker/Dockerfile
│   ├── frontend/Dockerfile
│   └── nginx/
│       ├── Dockerfile
│       └── nginx.conf                  # TLS, proxy_pass, rate limits, security headers
├── terraform/
│   ├── environments/
│   │   ├── staging/                    # Staging root module
│   │   └── production/                 # Production root module
│   ├── modules/                        # Reusable AWS resource modules
│   │   ├── vpc/
│   │   ├── ecs/
│   │   ├── rds/
│   │   ├── redis/
│   │   ├── s3/
│   │   ├── sqs/
│   │   ├── alb/
│   │   ├── cloudfront/
│   │   ├── route53/
│   │   ├── waf/
│   │   ├── secrets/
│   │   └── monitoring/
│   └── shared/
│       ├── providers.tf
│       └── versions.tf
├── scripts/
│   ├── deploy-staging.sh
│   ├── deploy-production.sh
│   ├── run-migrations.sh
│   ├── backup-database.sh
│   └── smoke-test.sh
└── README.md
```

```
.github/
└── workflows/
    ├── ci.yml                          # Lint + test on every PR
    ├── deploy-staging.yml              # Auto-deploy on push to dev
    ├── deploy-production.yml           # Manual production deploy
    └── security-scan.yml               # Weekly dependency vulnerability scan
```

| Folder | Purpose |
|--------|---------|
| `infrastructure/docker/` | Container image definitions for api, worker, frontend, nginx |
| `infrastructure/terraform/` | AWS infrastructure as code; modules composed per environment |
| `infrastructure/scripts/` | Operational shell scripts for deploy, migrate, backup |
| `.github/workflows/` | CI/CD automation |

---

## 7. Documentation Structure

```
docs/
├── PRD.md                              # Product vision and requirements
├── BUSINESS_REQUIREMENTS.md
├── FUNCTIONAL_REQUIREMENTS.md
├── NON_FUNCTIONAL_REQUIREMENTS.md
├── USER_STORIES.md
├── SYSTEM_ARCHITECTURE.md              # High-level architecture (companion to this doc)
├── DATABASE_DESIGN.md
├── API_DESIGN.md
├── MULTI_TENANT_DESIGN.md
├── RBAC_DESIGN.md
├── SECURITY_ARCHITECTURE.md
├── BILLING_SUBSCRIPTION.md
├── IMPLEMENTATION_PLAN.md
├── PROJECT_STRUCTURE.md                # This document — FROZEN
├── SPRINT_PLAN.md
├── ROADMAP.md
├── ADVANCED_FEATURES_ROADMAP.md
├── AI_FEATURES.md
└── PROJECT_REVIEW.md
```

---

## 8. Cross-Stack Domain Alignment

All three tiers use the **same domain vocabulary**:

| Domain | Backend `domains/` | Frontend `features/` | PostgreSQL Schema | API Prefix |
|--------|-------------------|---------------------|-------------------|------------|
| Platform | `platform/` | `subscription/`, `admin/` | `platform` | `/subscription` |
| Identity | `identity/` | `auth/` | `core` | `/auth` |
| Patients | `patients/` | `patients/` | `core` | `/patients` |
| Staff | `staff/` | `admin/` | `core` | `/staff`, `/doctors` |
| Clinical | `clinical/` | `opd/`, `ipd/` | `clinical` | `/opd`, `/ipd`, `/appointments` |
| Billing | `billing/` | `billing/` | `billing` | `/billing` |
| Laboratory | `laboratory/` | `laboratory/` | `laboratory` | `/laboratory` |
| Pharmacy | `pharmacy/` | `pharmacy/` | `pharmacy` | `/pharmacy`, `/inventory` |
| Communications | `communications/` | `admin/` (notifications) | `comms` | `/notifications` |
| Reporting | `reporting/` | `reports/`, `admin/` | All (read) | `/reports` |
| Audit | `audit/` | `admin/` | `audit` | `/audit` |

---

## 9. Naming Conventions (Frozen)

| Asset | Convention | Example |
|-------|------------|---------|
| Python module | `snake_case.py` | `patient_service.py` |
| Python class | `PascalCase` | `PatientService` |
| React component | `PascalCase.tsx` | `PatientForm.tsx` |
| React page | `PascalCase` + `Page` | `PatientListPage.tsx` |
| React hook | `use` + `PascalCase` | `usePatients.ts` |
| API endpoint file | `snake_case.py` / `camelCase.ts` | `patients.py` / `patients.ts` |
| PostgreSQL schema | `lowercase` | `clinical` |
| PostgreSQL table | `snake_case` | `opd_visits` |
| Alembic revision | `NNN_description` | `003_add_phi_access_logs` |
| SQS handler | `{job}_handler.py` | `pdf_handler.py` |

---

## 10. Quick Reference — Where to Put New Code

| Task | Location |
|------|----------|
| New REST endpoint | `backend/app/api/v1/{module}.py` |
| Business logic | `backend/app/domains/{domain}/services/` |
| Database query | `backend/app/domains/{domain}/repositories/` |
| Request/response shape | `backend/app/domains/{domain}/schemas/` |
| ORM table | `backend/app/models/{pg_schema}.py` |
| External integration | `backend/app/adapters/{service}_adapter.py` |
| Background job | `backend/worker/handlers/{job}_handler.py` |
| Scheduled cron | `backend/worker/scheduler/{job}_jobs.py` |
| Schema migration | `backend/alembic/versions/` |
| New UI page | `frontend/src/features/{feature}/pages/` |
| Design system component | `frontend/src/components/ui/` |
| API client function | `frontend/src/api/endpoints/{module}.ts` |
| React Query hook | `frontend/src/features/{feature}/hooks/` |
| RLS policy | `database/rls/` + Alembic migration |
| Seed data | `database/seeds/` |

---

## Revision History

| Version | Date | Status | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Superseded | Initial structure |
| **2.0** | **June 2026** | **FROZEN** | Production-ready structure: domain-driven backend, dedicated `core/tenant/`, schema-organized database, cross-stack domain alignment |

---

*This structure is frozen. Deviations require Principal Architect approval and a version increment of this document.*
