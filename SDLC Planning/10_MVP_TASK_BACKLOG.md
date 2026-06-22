# MVP Task Backlog V2 — MVP-001 to MVP-135

| Field | Value |
|-------|-------|
| **Version** | 2.1 |
| **Status** | Authoritative (replaces DS-001–DS-080 for remaining work) |
| **Source** | `09_MVP_SPRINT_PLAN_V2.md` |
| **Legend** | ✅ Done | 🔄 Partial | ❌ Not Started |

---

## Sprint 1 — Foundation (MVP-001 – MVP-010)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-001 | Monorepo + folder freeze | 2 | ✅ |
| MVP-002 | Docker Compose PG + Redis | 3 | ✅ |
| MVP-003 | Env templates | 1 | ✅ |
| MVP-004 | Backend FastAPI scaffold | 4 | ✅ |
| MVP-005 | Frontend Vite scaffold | 3 | ✅ |
| MVP-006 | CI pipeline | 2 | ✅ |
| MVP-007 | Alembic 001 foundation | 2 | ✅ |
| MVP-008 | Health + envelope + exceptions | 4 | ✅ |
| MVP-009 | Structured logging | 3 | ✅ |
| MVP-010 | TESTING_STRATEGY + DEPLOYMENT_GUIDE | 4 | ✅ |

## Sprint 2 — Multi-Tenant (MVP-011 – MVP-020)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-011 | Alembic 002 platform tables | 4 | ✅ |
| MVP-012 | RLS on platform tables | 3 | ✅ |
| MVP-013 | platform.create_tenant() | 2 | ✅ |
| MVP-014 | TenantScopedRepository + SET app.tenant_id | 4 | ✅ |
| MVP-015 | System tenant + plans seed | 3 | ✅ |
| MVP-016 | Tenant middleware | 3 | ✅ |
| MVP-017 | Platform register API | 4 | ✅ |
| MVP-018 | SQLAlchemy platform models | 4 | ✅ |
| MVP-019 | Cross-tenant isolation test | 4 | ✅ |
| MVP-020 | Gate G1 verification | 2 | ✅ |

## Sprint 3 — Auth Vertical Slice (MVP-021 – MVP-032)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-021 | Alembic 003 auth tables + RLS | 3 | 🔄 |
| MVP-022 | email_verification_tokens table | 1 | ❌ |
| MVP-023 | JWT RS256 + bcrypt module | 4 | ✅ |
| MVP-024 | Auth service sessions + refresh | 6 | ✅ |
| MVP-025 | Auth API (login/logout/refresh/me) | 6 | ✅ |
| MVP-026 | Forgot/reset password API | 4 | 🔄 |
| MVP-027 | Email verify + resend API | 3 | ❌ |
| MVP-028 | CAPTCHA on register | 2 | ❌ |
| MVP-029 | Auth rate limiting Redis | 2 | ❌ |
| MVP-030 | Frontend AuthProvider + login | 8 | ❌ |
| MVP-031 | Frontend forgot/reset/verify pages | 4 | ❌ |
| MVP-032 | Auth integration + E2E tests | 6 | 🔄 |
| MVP-033 | audit_logs migration + login audit writes | 3 | ❌ |
| MVP-034 | Session idle timeout (frontend) | 2 | ❌ |
| MVP-035 | JWT key generation script | 1 | ❌ |

## Sprint 4 — RBAC + Hospital Admin (MVP-036 – MVP-050)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-036 | Alembic 004 RBAC + invite tokens + RLS | 4 | 🔄 |
| MVP-037 | Permission catalog seed (+ opd:queue) | 3 | ✅ |
| MVP-038 | Permission resolver + Redis | 4 | ✅ |
| MVP-039 | require_permission decorator | 3 | ✅ |
| MVP-040 | User management API | 8 | ✅ |
| MVP-041 | accept-invite API + invite flow | 4 | ❌ |
| MVP-042 | Hospital profile/locations/settings API | 8 | ✅ |
| MVP-043 | Email adapter (SES stub) | 4 | ❌ |
| MVP-044 | Subscription status middleware | 3 | 🔄 |
| MVP-045 | Privacy/terms acceptance on register | 2 | ❌ |
| MVP-046 | Registration wizard UI | 8 | ❌ |
| MVP-047 | Protected routes + role landing | 4 | ❌ |
| MVP-048 | PermissionGuard + usePermissions | 4 | ❌ |
| MVP-049 | Hospital + user + system config UI | 12 | ❌ |
| MVP-050 | Gate G2 E2E test | 4 | ❌ |

## Sprint 5 — API Standards + OPD Spec (MVP-051 – MVP-058)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-051 | API_DESIGN_OPD.md complete spec | 8 | ❌ |
| MVP-052 | OPD OpenAPI router stubs | 4 | ❌ |
| MVP-053 | Audit write service (uses S3 table) | 4 | ❌ |
| MVP-054 | Mutation audit middleware | 3 | ❌ |
| MVP-055 | Composite FK migration checklist | 2 | ❌ |
| MVP-056 | Shared UI components | 8 | ❌ |
| MVP-057 | OpenAPI snapshot test | 2 | ❌ |
| MVP-058 | Update stale planning docs | 2 | ❌ |

## Sprint 6 — Org Structure (MVP-059 – MVP-068)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-059 | Alembic 005 org tables + RLS | 3 | ❌ |
| MVP-060 | Departments API | 3 | ❌ |
| MVP-061 | Staff API | 4 | ❌ |
| MVP-062 | Doctors API | 4 | ❌ |
| MVP-063 | Doctor schedules API | 4 | ❌ |
| MVP-064 | Departments UI | 3 | ❌ |
| MVP-065 | Staff UI | 5 | ❌ |
| MVP-066 | Doctors + schedule UI | 6 | ❌ |
| MVP-067 | Org integration tests | 4 | ❌ |
| MVP-068 | Org isolation tests | 2 | ❌ |

## Sprint 7 — Patients (MVP-069 – MVP-082)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-069 | Alembic 006 patient tables + RLS | 4 | ❌ |
| MVP-070 | pg_trgm extension + search indexes | 2 | ❌ |
| MVP-071 | MRN generator function | 2 | ❌ |
| MVP-072 | Patient CRUD API | 6 | ❌ |
| MVP-073 | Allergies + contacts API | 3 | ❌ |
| MVP-074 | Chronic conditions API | 2 | ❌ |
| MVP-075 | Visit history API | 3 | ❌ |
| MVP-076 | Duplicate detection API | 3 | ❌ |
| MVP-077 | Consent on registration | 2 | ❌ |
| MVP-078 | Trial patient cap | 2 | ❌ |
| MVP-079 | Patient list + search UI | 5 | ❌ |
| MVP-080 | Registration form UI | 5 | ❌ |
| MVP-081 | Patient profile UI | 4 | ❌ |
| MVP-082 | Patient tests | 5 | ❌ |

## Sprint 8 — Appointments (MVP-083 – MVP-090)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-083 | Alembic 007 appointments + RLS | 2 | ❌ |
| MVP-084 | Appointments CRUD API | 6 | ❌ |
| MVP-085 | Availability check API | 4 | ❌ |
| MVP-086 | Confirm/cancel endpoints | 2 | ❌ |
| MVP-087 | Appointment calendar UI | 6 | ❌ |
| MVP-088 | Booking modal UI | 4 | ❌ |
| MVP-089 | Conflict 409 tests | 2 | ❌ |
| MVP-090 | Appointment integration tests | 4 | ❌ |

## Sprint 9 — OPD (MVP-091 – MVP-102)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-091 | Alembic 008 OPD tables + RLS | 4 | ❌ |
| MVP-092 | OPD visits API | 5 | ❌ |
| MVP-093 | Queue API | 5 | ❌ |
| MVP-094 | Vitals + notes API | 5 | ❌ |
| MVP-095 | E-prescription API | 5 | ❌ |
| MVP-096 | Queue polling endpoint | 2 | ❌ |
| MVP-097 | OPD queue board UI | 5 | ❌ |
| MVP-098 | Doctor consultation UI | 8 | ❌ |
| MVP-099 | Patient visit history UI | 3 | ❌ |
| MVP-100 | PHI access on consult | 2 | ❌ |
| MVP-101 | OPD workflow integration test | 4 | ❌ |
| MVP-102 | Gate G3 E2E | 3 | ❌ |

## Sprint 10 — Billing (MVP-103 – MVP-115)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-103 | Alembic 009 billing + RLS | 3 | ❌ |
| MVP-104 | Service master API | 3 | ❌ |
| MVP-105 | Invoice CRUD + finalize + void | 6 | ❌ |
| MVP-106 | Approve-discount API | 2 | ❌ |
| MVP-107 | Payments + allocations API | 5 | ❌ |
| MVP-108 | Invoice from OPD visit | 4 | ❌ |
| MVP-109 | PDF invoice + receipt | 4 | ❌ |
| MVP-110 | Billing UI | 8 | ❌ |
| MVP-111 | Idempotency on payments | 2 | ❌ |
| MVP-112 | Default services seed | 2 | ❌ |
| MVP-113 | Billing integration tests | 4 | ❌ |
| MVP-114 | Void audit test | 2 | ❌ |
| MVP-115 | Gate G4 E2E | 4 | ❌ |

## Sprint 11 — Reports, Audit, Files, Notifications (MVP-116 – MVP-124)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-116 | Alembic 010 comms/phi + RLS | 3 | ❌ |
| MVP-117 | PHI access log API | 3 | ❌ |
| MVP-118 | Audit list API + viewer | 4 | ❌ |
| MVP-119 | Dashboard + reports APIs | 6 | ❌ |
| MVP-120 | S3 file upload flow | 5 | ❌ |
| MVP-121 | SQS worker + email jobs | 6 | ❌ |
| MVP-122 | Dashboard + reports UI | 8 | ❌ |
| MVP-123 | Notification bell UI | 3 | ❌ |
| MVP-124 | Report accuracy tests | 4 | ❌ |

## Sprint 12 — Launch (MVP-125 – MVP-135)

| ID | Task | Hrs | Status |
|----|------|-----|--------|
| MVP-125 | Alembic 011 SaaS billing tables + RLS | 3 | ❌ |
| MVP-126 | Razorpay + payment methods API | 8 | ❌ |
| MVP-127 | Auto-billing + reminder cron jobs | 4 | ❌ |
| MVP-128 | 2FA TOTP + security hardening | 6 | ❌ |
| MVP-129 | Bandit SAST in CI | 2 | ❌ |
| MVP-130 | Terraform staging + production | 12 | ❌ |
| MVP-131 | Docker/ECR build pipeline | 4 | ❌ |
| MVP-132 | Backup restore drill | 3 | ❌ |
| MVP-133 | Load test + OWASP ZAP staging | 4 | ❌ |
| MVP-134 | UAT + beta tenants + bug fixes | 12 | ❌ |
| MVP-135 | Gate G5 launch + docs complete | 8 | ❌ |

---

## Progress Summary

| Sprint | Tasks | Done | Remaining |
|--------|-------|------|-----------|
| S1 | 10 | 8 | 2 |
| S2 | 10 | 4 | 6 |
| S3 | 15 | 4 | 11 |
| S4 | 15 | 6 | 9 |
| S5–S12 | 85 | 0 | 85 |
| **Total** | **135** | **~22** | **~113** |
