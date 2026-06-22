# Phase Plan — Deep Breakdown

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Phases** | 0 (Setup) + 1 (MVP) + 2 (Clinical) + 3 (Growth) + Stabilization |

---

## Phase 0 — Project & Database Setup

**Duration:** Weeks 1–2  
**Sprint:** S1  
**Status:** ~80% complete

### Objectives
1. Monorepo with frozen folder structure
2. Local dev stack (Docker Compose)
3. CI pipeline
4. PostgreSQL foundation schemas + Alembic
5. FastAPI + React scaffolds
6. Tenant middleware foundation

### Deliverables Checklist

| # | Deliverable | Acceptance | Status |
|---|-------------|------------|--------|
| P0-01 | Git repo with `main` + `dev` | Clean history, no secrets | ✅ |
| P0-02 | Docker Compose Postgres + Redis | `docker compose up` works | ✅ |
| P0-03 | CI on push (lint + pytest) | Green on clean commit | ✅ |
| P0-04 | Alembic 001: schemas + extensions | `upgrade head` succeeds | ✅ |
| P0-05 | Alembic 002–004: platform + core tables | Tenants, users, RBAC exist | ✅ |
| P0-06 | SQLAlchemy models (platform + core) | No metadata drift | ✅ |
| P0-07 | Health endpoints | Envelope + readiness | ✅ |
| P0-08 | Tenant middleware | `X-Tenant-Slug` resolves | ✅ |
| P0-09 | Frontend shell | Vite builds, health page | ✅ |
| P0-10 | RLS policies in Alembic | Isolation smoke test | ⚠️ Partial |
| P0-11 | Seed scripts (system tenant, permissions) | Idempotent re-run | ⚠️ Partial |

### Phase 0 Exit — Gate G1
- [x] Docker Compose runs
- [x] CI green
- [x] Tenant creation works
- [ ] RLS fully verified (carry to S2)

---

## Phase 1 — MVP Foundation

**Duration:** Weeks 3–8  
**Sprints:** S2, S3, S4  
**Goal:** Demoable SaaS MVP on staging

### Phase 1 Modules

| Module | Sprint | Backend | Frontend | DB Tables |
|--------|--------|---------|----------|-----------|
| Authentication | S2 | ✅ | ❌ | users, user_sessions, password_reset_tokens |
| RBAC | S2 | ✅ | ❌ | roles, permissions, user_roles, role_permissions |
| Tenant provisioning | S2 | ✅ | ❌ | tenants, tenant_subscriptions, subscription_plans |
| Hospital admin | S2–3 | ✅ | ❌ | tenant_locations, tenant_settings |
| User management | S2–3 | ✅ | ❌ | users, user_roles |
| Patients | S3 | ❌ | ❌ | patients, patient_allergies, patient_contacts |
| Staff + Departments | S3 | ❌ | ❌ | staff, departments |
| Doctors | S3 | ❌ | ❌ | doctors |
| Appointments | S4 | ❌ | ❌ | appointments, doctor_schedules |
| OPD visits + queue | S4 | ❌ | ❌ | opd_visits, opd_queue, consultations |
| Patient billing | S4 | ❌ | ❌ | billing_services, invoices, payments |

### Phase 1 User Journey (Must Work E2E)

```
Register hospital → Login as owner → Invite staff →
Register patient → Book appointment → Doctor consults →
Generate invoice → Collect payment → Print receipt
```

### Phase 1 Functional Requirements Coverage

| FR Module | P0 Requirements | Target Sprint |
|-----------|-------------------|---------------|
| FR-PLT (Platform) | 001–005, 007, 011–013 | S1–S2 |
| FR-AUTH | 001–006, 008–012 | S2–S3 |
| FR-PAT (Patient) | All P0 | S3 |
| FR-OPD | All P0 | S4 |
| FR-BIL (Billing) | All P0 | S4 |
| FR-ADM (Admin) | Staff, departments, settings | S3 |
| FR-SUB (Subscription) | Trial provisioning | S2 (full billing S11) |

### Phase 1 Risks

| Risk | Mitigation |
|------|------------|
| Frontend lag blocks demo | Prioritize auth UI in S2 week 1 |
| OPD API spec missing | Draft OPD OpenAPI in S3 week 2 |
| Solo dev burnout | Strict P0/P1; defer P2 each sprint |

### Phase 1 Exit — Gate G2 (End S4)

| Criterion | Required |
|-----------|----------|
| Tenant signup + login (UI) | Yes |
| Patient CRUD + search | Yes |
| OPD appointment → consultation | Yes |
| Invoice + payment | Yes |
| RBAC on all endpoints | Yes |
| Tenant isolation tests | Yes |
| 3 demo tenants on staging | Yes |
| MVP demo video | Yes |

---

## Phase 2 — Clinical Depth

**Duration:** Weeks 9–16  
**Sprints:** S5, S6, S7, S8  
**Goal:** Full hospital operations — IPD + Lab + Pharmacy

### Phase 2 Modules

| Module | Sprint | Key Features |
|--------|--------|--------------|
| IPD Foundation | S5 | Wards, rooms, beds, admissions |
| IPD Clinical | S6 | Nursing notes, vitals, discharge, IPD billing |
| Laboratory | S7 | Test catalog, orders, samples, results, PDF reports |
| Pharmacy | S8 | Medicines, dispensing, inventory, stock movements |

### Phase 2 Database Schemas

| Schema | New Tables (from 61-table design) |
|--------|-----------------------------------|
| `clinical` | wards, rooms, beds, admissions, nursing_notes, ipd_vitals, discharge_summaries |
| `laboratory` | lab_tests, lab_orders, lab_samples, lab_results |
| `pharmacy` | medicines, prescriptions, dispensings, inventory_batches, stock_movements |

### Phase 2 User Journeys

**IPD:** Admit patient → assign bed → nursing vitals → doctor rounds → discharge → final bill  
**Lab:** Doctor orders test → sample collected → results entered → critical alert → PDF report  
**Pharmacy:** E-Rx from OPD → pharmacist dispenses → stock deducted → charge on invoice

### Phase 2 Exit — Gate G3 (End S8)

| Criterion | Required |
|-----------|----------|
| IPD admit → discharge → bill | Yes |
| Lab order → report | Yes |
| Prescription → dispense → stock update | Yes |
| 5 beta tenants on Professional plan | Yes |

---

## Phase 3 — Growth & Launch

**Duration:** Weeks 17–24  
**Sprints:** S9, S10, S11, S12  
**Goal:** Monetization, observability, production launch

### Phase 3 Modules

| Module | Sprint | Key Features |
|--------|--------|--------------|
| Reporting | S9 | Dashboards, OPD/IPD/lab/pharmacy/financial reports, CSV/PDF export |
| Notifications | S10 | In-app, email, SMS reminders, multi-location |
| SaaS billing | S11 | Razorpay, plan limits, audit viewer, security hardening |
| Production | S12 | AWS Terraform, UAT, onboarding guide, launch |

### Phase 3 Exit — Gates G4 + G5

**G4 (S11):** Trial → paid conversion via Razorpay; plan limits enforced  
**G5 (S12):** Production live; 10 beta tenants; pen test; runbooks published

---

## Stabilization Phase

**Duration:** Months 7–12 (post Sprint 12)  
**Capacity:** 20% buffer for support, bug fixes, onboarding

### Activities

| Activity | Frequency |
|----------|-----------|
| Beta tenant support | Daily |
| P0/P1 bug fixes | Within 24–48 hrs |
| Performance tuning | Monthly |
| Documentation updates | Per release |
| Feature backlog grooming | Bi-weekly |
| Security patches | As needed |

### Stabilization Success Metrics

| Metric | Target |
|--------|--------|
| Uptime | ≥ 99.9% |
| P0 incidents | < 2/month |
| Tenant churn | < 5% |
| NPS | ≥ 40 |
| Paying tenants | 50 by Q1 2027 |

---

## Phase Effort Summary

| Phase | Sprints | Est. Hours | Story Points |
|-------|---------|------------|--------------|
| Phase 0 | S1 | 56 | 21 |
| Phase 1 | S2–S4 | 168 | 72 |
| Phase 2 | S5–S8 | 224 | 93 |
| Phase 3 | S9–S12 | 224 | 83 |
| **Total** | **12** | **~672** | **~269** |
