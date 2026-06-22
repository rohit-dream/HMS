# Module Plan — Deep Breakdown (15 Modules)

Each module follows: **DB → Model → Repository → Service → Schema → API → Frontend → Tests**

---

## Module 1: Platform Foundation

| Field | Value |
|-------|-------|
| **Sprint** | S1 |
| **Schema** | `platform` |
| **Status** | ~90% |

### Tables
`tenants`, `tenant_locations`, `tenant_settings`, `subscription_plans`, `tenant_subscriptions`

### Backend Deliverables
| Component | Path | Status |
|-----------|------|--------|
| Models | `app/models/platform/` | ✅ |
| Tenant repository | `domains/platform/repositories/` | ✅ |
| Tenant service | `domains/platform/services/tenant_service.py` | ✅ |
| Platform API | `api/v1/platform.py` | ✅ |
| Hospital API | `api/v1/hospital.py` | ✅ |

### Frontend Deliverables
| Screen | Path | Status |
|--------|------|--------|
| Register wizard | `features/auth/pages/RegisterPage.tsx` | ❌ |
| Org settings | `features/admin/pages/SettingsPage.tsx` | ❌ |
| Branches | `features/admin/pages/BranchesPage.tsx` | ❌ |

### Tests Required
- Tenant isolation (cross-tenant 404)
- Slug uniqueness (409)
- Provision creates roles + owner user

### FR Coverage
FR-PLT-001 through FR-PLT-007, FR-PLT-011 through FR-PLT-013

---

## Module 2: Authentication

| Field | Value |
|-------|-------|
| **Sprint** | S2 |
| **Schema** | `core` |
| **Status** | Backend ✅ / Frontend ❌ |
| **Authority** | `SECURITY_ARCHITECTURE.md` |

### Tables
`users`, `user_sessions`, `password_reset_tokens`

### API Endpoints
| Method | Path | Status |
|--------|------|--------|
| POST | `/auth/login` | ✅ |
| POST | `/auth/logout` | ✅ |
| POST | `/auth/refresh` | ✅ |
| GET | `/auth/me` | ✅ |
| PATCH | `/auth/me` | ✅ |
| POST | `/auth/forgot-password` | ⚠️ |
| POST | `/auth/reset-password` | ⚠️ |

### Frontend Deliverables
| Component | Description |
|-----------|-------------|
| `AuthProvider` | Token in memory, refresh interceptor |
| `LoginPage` | Email/password, tenant slug |
| `ForgotPasswordPage` | Email form |
| `ResetPasswordPage` | Token + new password |
| Axios interceptor | 401 → refresh → retry |

### Security Requirements
- RS256 JWT, 30-min access token
- Refresh in HttpOnly cookie only
- bcrypt password hashing
- 5 failed attempts → 30-min lockout
- Permissions server-side (NOT in JWT)

### Tests
- Login/refresh/logout flow
- Lockout after 5 failures
- Refresh token rotation + reuse detection
- Cross-tenant login isolation

---

## Module 3: RBAC (Role-Based Access Control)

| Field | Value |
|-------|-------|
| **Sprint** | S2 |
| **Authority** | `RBAC_DESIGN.md` |
| **Status** | Backend ✅ / Frontend ❌ |

### Roles (9 total, 8 tenant-assignable)
`hospital_owner`, `hospital_admin`, `doctor`, `nurse`, `receptionist`, `lab_technician`, `pharmacist`, `accountant` (+ `platform_admin` system-only)

### Backend Components
| Component | Path |
|-----------|------|
| Permission catalog | `core/rbac/catalog.py` |
| Permission resolver | `core/permissions.py` |
| Authorization decorator | `core/authorization.py` |
| RBAC repository | `domains/identity/repositories/rbac_repository.py` |

### Frontend Components
| Component | Description |
|-----------|-------------|
| `usePermissions()` | Load from `/auth/me` |
| `PermissionGuard` | Hide/disable UI by permission |
| `lib/permissions.ts` | `hasPermission(user, code)` |

### Business Rules
- R-02: Max 2 `hospital_owner` per tenant
- R-03: `platform_admin` not assignable to tenants
- R-06: Cannot remove/disable last owner
- Cache invalidation on role change

---

## Module 4: User Management

| Field | Value |
|-------|-------|
| **Sprint** | S2–S3 |
| **Permission** | `admin:users` |
| **Status** | Backend ✅ / Frontend ❌ |

### Capabilities
1. Create user (active + password)
2. Invite user (inactive)
3. Update profile
4. Disable user (+ revoke sessions)
5. Assign/remove roles
6. Admin reset password
7. Generate reset token
8. Self profile (`PATCH /auth/me`)

### API Endpoints (all under `/admin/users`)
| Endpoint | Status |
|----------|--------|
| GET (search/list) | ✅ |
| POST (create) | ✅ |
| POST /invite | ✅ |
| GET /{id} | ✅ |
| PATCH /{id} | ✅ |
| POST /{id}/disable | ✅ |
| POST /{id}/roles | ✅ |
| DELETE /{id}/roles/{code} | ✅ |
| POST /{id}/reset-password | ✅ |
| POST /{id}/reset-token | ✅ |

### Frontend Screens
- User list with search + status filter
- Invite modal (email, name, roles)
- User detail drawer (roles, disable, reset)
- Role assignment chips

---

## Module 5: Patient Management

| Field | Value |
|-------|-------|
| **Sprint** | S3 |
| **Schema** | `core` |
| **Permission** | `patient:*` |
| **Status** | Stub only |

### Tables
`patients`, `patient_allergies`, `patient_contacts`

### API Endpoints (per `API_DESIGN.md` §4)
| Method | Path | Permission |
|--------|------|------------|
| GET | `/patients` | `patient:read` |
| POST | `/patients` | `patient:create` |
| GET | `/patients/{id}` | `patient:read` |
| PATCH | `/patients/{id}` | `patient:update` |
| DELETE | `/patients/{id}` | `patient:delete` |
| GET/POST | `/patients/{id}/allergies` | `patient:update` |
| GET/POST | `/patients/{id}/contacts` | `patient:update` |

### Business Logic
- MRN auto-generation: `MRN-YYYY-NNNNN` per tenant
- Duplicate phone warning (not block)
- Soft delete only
- Trial plan: 100 patient cap
- PHI access audit log on read

### Frontend Screens
- Patient list (search, pagination, status)
- Registration form (demographics, emergency contact)
- Profile page (allergies, visit history stub)

### File Structure
```
backend/app/domains/patients/
  models/ repositories/ services/ schemas/
backend/app/api/v1/patients.py
frontend/src/features/patients/
  pages/ components/ hooks/ api/
```

---

## Module 6: Staff & Departments

| Field | Value |
|-------|-------|
| **Sprint** | S3 |
| **Schema** | `core` |
| **Permission** | `admin:staff`, `admin:departments` |

### Tables
`staff`, `departments`

### API
- Departments CRUD
- Staff CRUD (link to department, location, optional user account)

### Frontend
- Department master page
- Staff list + form
- Link staff to user account (optional)

---

## Module 7: Doctor Management

| Field | Value |
|-------|-------|
| **Sprint** | S3–S4 |
| **Schema** | `core` |
| **Permission** | `admin:doctors`, `doctor:*` |

### Tables
`doctors` (extends staff)

### API
- Create doctor from staff record
- List doctors (for appointment calendar)
- Update: specialization, registration_no, consultation_fee

### Frontend
- Doctor list in admin
- Doctor selector in appointment booking

---

## Module 8: Appointments & OPD

| Field | Value |
|-------|-------|
| **Sprint** | S4 |
| **Schema** | `clinical` |
| **Permission** | `appointment:*`, `opd:*` |
| **Note** | Extend `API_DESIGN.md` — OPD spec missing |

### Tables
`appointments`, `doctor_schedules`, `opd_visits`, `opd_queue`, `consultations`, `prescriptions`

### Workflows
1. **Book appointment** — doctor + slot + patient
2. **Walk-in queue** — token number assignment
3. **Consultation** — vitals, notes, diagnosis, e-Rx
4. **Complete visit** — trigger billing

### API (to be specified)
- Appointments CRUD + availability check
- Queue: add, call next, complete
- Consultation: start, vitals, notes, prescribe, complete

### Frontend
- Appointment calendar (week view)
- OPD queue board (receptionist + doctor)
- Doctor consultation screen (patient context panel)

---

## Module 9: Patient Billing

| Field | Value |
|-------|-------|
| **Sprint** | S4, S6 (IPD) |
| **Schema** | `billing` |
| **Permission** | `billing:*` |

### Tables
`billing_services`, `invoices`, `invoice_line_items`, `payments`, `payment_allocations`

### Workflows
1. Service master setup (consultation fee, registration)
2. Invoice draft from OPD visit
3. Finalize invoice (immutable)
4. Collect payment (cash, UPI, card)
5. Generate receipt PDF
6. Daily collection report

### Business Rules
- Invoice number per tenant sequence
- Void only before payment
- Partial payments supported
- Accountant role: `billing:*` without `billing:void`

---

## Module 10: IPD (Inpatient)

| Field | Value |
|-------|-------|
| **Sprint** | S5–S6 |
| **Schema** | `clinical` |
| **Permission** | `ipd:*` |

### Sub-modules
| Sub | Sprint | Features |
|-----|--------|----------|
| IPD Foundation | S5 | Wards, rooms, beds, admissions |
| IPD Clinical | S6 | Nursing notes, vitals, discharge |
| IPD Billing | S6 | Daily charges, running bill, discharge invoice |

### Key Workflows
- Bed availability dashboard
- Admit → assign bed → treat → discharge → release bed → final bill
- Plan limit: `max_beds` per subscription tier

---

## Module 11: Laboratory

| Field | Value |
|-------|-------|
| **Sprint** | S7 |
| **Schema** | `laboratory` |
| **Permission** | `lab:*` |

### Workflow
Order → sample collection → processing → result entry → critical flag → PDF report → billing link

### Roles
- Doctor: order labs
- Lab technician: collect, process, enter results
- Doctor: notified on critical values

---

## Module 12: Pharmacy & Inventory

| Field | Value |
|-------|-------|
| **Sprint** | S8 |
| **Schema** | `pharmacy` |
| **Permission** | `pharmacy:*`, `inventory:*` |

### Workflow
E-Rx queue → dispense (batch selection) → stock deduction → movement ledger → invoice line item

### Inventory
- Stock-in (goods receipt)
- Manual adjustment
- Low-stock + expiring-soon alerts
- Immutable movement ledger

---

## Module 13: Reporting & Analytics

| Field | Value |
|-------|-------|
| **Sprint** | S9 |
| **Schema** | Read models / views |
| **Permission** | `reports:clinical`, `reports:financial` |

### Reports
| Report | Role |
|--------|------|
| Admin dashboard | hospital_owner, hospital_admin |
| OPD summary | hospital_admin |
| IPD occupancy + ALOS | hospital_admin |
| Lab TAT summary | hospital_admin |
| Pharmacy dispensing | hospital_admin |
| Daily collection | accountant |
| Outstanding balances | accountant |

### Performance
- Redis cache on dashboard (2-min TTL)
- Target: dashboard < 3s with seed data

---

## Module 14: Notifications & Communications

| Field | Value |
|-------|-------|
| **Sprint** | S10 |
| **Schema** | `communications` |
| **Adapters** | SES (email), MSG91/Twilio (SMS) |

### Notification Types
- Appointment reminder (1 day before)
- Lab result ready
- Critical lab value alert
- Password reset / invite (from auth)

### Infrastructure
- SQS worker for async delivery
- Delivery log for audit
- User preference toggles

---

## Module 15: SaaS Subscription Billing

| Field | Value |
|-------|-------|
| **Sprint** | S11 |
| **Authority** | `BILLING_SUBSCRIPTION.md` |
| **Gateway** | Razorpay |

### Plans
| Plan | Users | Beds | Patients | Price |
|------|-------|------|----------|-------|
| Starter | 5 | 10 | 500 | ₹2,999/mo |
| Professional | 25 | 50 | 5,000 | ₹7,999/mo |
| Enterprise | Unlimited | Unlimited | Unlimited | Custom |

### Workflows
- 14-day trial on registration
- Trial → paid conversion
- Plan upgrade/downgrade
- Payment failure → grace → suspension
- Usage metering vs limits

**Note:** This is SaaS billing (tenant pays platform). Distinct from Module 9 (patient pays hospital).

---

## Module Implementation Template

Use this checklist for every new module:

```
□ Read FR IDs from FUNCTIONAL_REQUIREMENTS.md
□ Read API spec from API_DESIGN.md (or draft if missing)
□ Read tables from DATABASE_DESIGN.md
□ Create Alembic migration with RLS
□ Create SQLAlchemy models
□ Create Pydantic schemas (create, update, response)
□ Create TenantScopedRepository
□ Create Service with business rules
□ Create API routes with require_permission
□ Write integration tests (CRUD + isolation)
□ Create frontend feature folder
□ Create API endpoint hooks (TanStack Query)
□ Create pages + forms (RHF + Zod)
□ Add PermissionGuard on actions
□ E2E smoke test
□ Update OpenAPI / this planning doc
```
