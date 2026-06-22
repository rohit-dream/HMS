# MVP Coverage Maps — Tables, APIs, Frontend

| Version | 2.0 |
| Companion | `09_MVP_SPRINT_PLAN_V2.md` |

---

## A. Database Table → Sprint Map (MVP Only — 48 tables)

| # | Table | Sprint | Migration |
|---|-------|--------|-----------|
| 1 | `platform.tenants` | S2 | 002 |
| 2 | `platform.subscription_plans` | S2 | 002 |
| 3 | `platform.tenant_subscriptions` | S2 | 002 |
| 4 | `platform.tenant_locations` | S2 | 002 |
| 5 | `platform.tenant_settings` | S2 | 002 |
| 6 | `core.users` | S3 | 003 |
| 7 | `core.user_sessions` | S3 | 003 |
| 8 | `core.password_reset_tokens` | S3 | 003 |
| 9 | `core.email_verification_tokens` | S3 | 003 |
| 10 | `audit.audit_logs` | **S3** | 003 |
| 11 | `core.roles` | S4 | 004 |
| 12 | `core.permissions` | S4 | 004 |
| 13 | `core.role_permissions` | S4 | 004 |
| 14 | `core.user_roles` | S4 | 004 |
| 15 | `core.user_invite_tokens` | S4 | 004 |
| 16 | `core.departments` | S6 | 005 |
| 17 | `core.staff` | S6 | 005 |
| 18 | `core.doctors` | S6 | 005 |
| 19 | `core.doctor_schedules` | S6 | 005 |
| 20 | `core.patients` | S7 | 006 |
| 21 | `core.patient_allergies` | S7 | 006 |
| 22 | `core.patient_contacts` | S7 | 006 |
| 23 | `core.patient_documents` | S7 | 006 |
| 24 | `clinical.appointments` | S8 | 007 |
| 25–31 | `clinical.opd_*` (7 tables) | S9 | 008 |
| 32–37 | `billing.*` (6 tables) | S10 | 009 |
| 38 | `audit.phi_access_logs` | S11 | 010 |
| 39–42 | `comms.*` (4 tables) | S11 | 010 |
| 43 | `platform.subscription_invoices` | S12 | 011 |
| 44 | `platform.payment_methods` | S12 | 011 |
| 45 | `platform.subscription_payments` | S12 | 011 |

**Post-MVP tables (61 − 42 = 19):** All IPD, pharmacy, laboratory tables → Phase 2.

---

## B. API Module → Sprint Map

| API Module | Base Path | Sprint | Doc Reference |
|------------|-----------|--------|---------------|
| Health | `/health` | S1 | — |
| Platform | `/api/v1/platform` | S2, S12 | API_DESIGN |
| Auth | `/api/v1/auth` | S3, S12 | API_DESIGN §3, AUTH guide |
| Hospital | `/api/v1/hospital` | S4 | API_DESIGN |
| Admin Users | `/api/v1/admin/users` | S4 | API_DESIGN |
| Admin Departments | `/api/v1/admin/departments` | S6 | API_DESIGN §11 |
| Staff | `/api/v1/staff` | S6 | API_DESIGN §11 |
| Doctors | `/api/v1/doctors` | S6 | API_DESIGN §5 |
| Patients | `/api/v1/patients` | S7 | API_DESIGN §4 |
| Appointments | `/api/v1/appointments` | S8 | API_DESIGN §6 |
| OPD | `/api/v1/opd` | S9 | API_DESIGN_OPD.md |
| Billing | `/api/v1/billing` | S10 | API_DESIGN §7 |
| Reports | `/api/v1/reports` | S11 | API_DESIGN (extend) |
| Audit | `/api/v1/admin/audit` | S11 | RBAC_DESIGN |
| Files | `/api/v1/files` | S11 | SYSTEM_ARCHITECTURE §9 |
| Notifications | `/api/v1/notifications` | S11 | — |
| Subscription | `/api/v1/platform/subscription` | S12 | BILLING_SUBSCRIPTION.md |
| Webhooks | `/api/v1/webhooks/razorpay` | S12 | BILLING_SUBSCRIPTION.md |

**Post-MVP API modules:** Pharmacy §8, Inventory §9, Laboratory §10, IPD (new doc).

---

## C. Frontend Feature → Sprint Map

| Feature Folder | Pages | Sprint |
|----------------|-------|--------|
| `features/auth` | login, register, forgot, reset, verify | S3–S4 |
| `features/admin` | settings, branches, users, departments, staff, doctors, audit, subscription | S4, S6, S11, S12 |
| `features/patients` | list, new, profile, documents | S7, S11 |
| `features/appointments` | calendar, detail | S8 |
| `features/opd` | queue, consult, visit summary | S9 |
| `features/billing` | services, invoices, receipt | S10 |
| `features/reports` | dashboard, reports | S11 |
| `features/notifications` | bell, preferences | S11 |
| `features/onboarding` | wizard | S12 |
| `components/ui` | shared design system | S5 |
| `api/` | typed API client | S1–S3 |

---

## D. Cross-Cutting Concerns → Sprint Map

| Concern | Sprint(s) |
|---------|-----------|
| Error handling envelope | S1 |
| Structured logging | S1 |
| RLS per migration | S2, S3, S4, S6–S11 |
| `SET app.tenant_id` | S2 |
| Tenant isolation tests | S2 + every sprint |
| Audit mutation logging | S5, S11 |
| PHI access logging | S7 (writes), S11 (table) |
| Rate limiting | S3 (auth), S12 (global) |
| Security headers | S12 |
| 2FA | S12 |
| OpenAPI docs | S5 + each API sprint |
| Docker local | S1 |
| CI | S1 |
| Staging AWS | S12 |
| Production AWS | S12 |
| Email (SES) | S4, S11 |
| S3 files | S11 |
| PDF generation | S10 |
| Razorpay | S12 |
