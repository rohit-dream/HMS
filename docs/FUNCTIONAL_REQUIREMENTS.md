# Functional Requirements Document (FRD)

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Last Updated** | June 2026 |
| **Tech Stack** | React.js, TypeScript, TailwindCSS (Frontend) · Python, FastAPI (Backend) · SQL Database |
| **Related Documents** | PRD.md, BUSINESS_REQUIREMENTS.md, API_DESIGN.md, DATABASE_DESIGN.md |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the **functional requirements** for the Multi-Tenant Hospital Management SaaS Platform. Each requirement is uniquely identified, categorized by module, and assigned a priority for implementation planning.

### 1.2 Requirement ID Convention

```
FR-<MODULE>-<NUMBER>

Modules: PLT (Platform), AUTH, PAT (Patient), OPD, IPD, LAB, PHR (Pharmacy),
         BIL (Billing), RPT (Reporting), ADM (Admin), SUB (Subscription), NTF (Notification)
```

### 1.3 Priority Levels

| Priority | Definition |
|----------|------------|
| **P0** | Must-have for MVP launch |
| **P1** | Required for Phase 2 |
| **P2** | Required for Phase 3 |
| **P3** | Future enhancement |

---

## 2. Platform & Multi-Tenancy

### 2.1 Tenant Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-PLT-001 | System shall allow creation of new tenant organizations via platform admin | P0 | Tenant created with unique ID, name, subdomain, and plan |
| FR-PLT-002 | System shall allow self-service tenant registration with email verification | P0 | User receives verification email; account activated on confirmation |
| FR-PLT-003 | System shall assign a unique `tenant_id` (UUID) to each organization | P0 | Every database record for a tenant includes `tenant_id` |
| FR-PLT-004 | System shall enforce `tenant_id` filter on all data queries | P0 | No API endpoint returns data from another tenant |
| FR-PLT-005 | System shall support tenant organization profile (name, logo, address, phone, timezone) | P0 | Profile editable by tenant admin; displayed on reports |
| FR-PLT-006 | System shall support multiple locations/branches per tenant | P1 | Each location has address; patients and encounters linked to location |
| FR-PLT-007 | System shall allow platform admin to suspend/reactivate tenants | P0 | Suspended tenant users cannot log in; data preserved |
| FR-PLT-008 | System shall allow tenant admin to configure working hours and holidays | P1 | Appointment slots respect configured schedule |
| FR-PLT-009 | System shall provide tenant-specific subdomain (e.g., `clinicname.platform.com`) | P1 | Tenant accessible via unique subdomain |
| FR-PLT-010 | System shall support tenant data export in standard formats (CSV, JSON) | P1 | Export includes all tenant data; downloadable within 24 hours |

### 2.2 Tenant Isolation

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-PLT-011 | All database tables containing tenant data shall include `tenant_id` column | P0 | Schema audit confirms `tenant_id` on all tenant-scoped tables |
| FR-PLT-012 | Application middleware shall inject `tenant_id` from authenticated session into all queries | P0 | Integration tests verify isolation |
| FR-PLT-013 | System shall prevent API requests with mismatched `tenant_id` in URL/body vs. session | P0 | Returns 403 Forbidden |
| FR-PLT-014 | Shared reference data (e.g., ICD codes) shall be accessible read-only across tenants | P2 | Global master data served without tenant filter |

---

## 3. Authentication & Authorization

### 3.1 Authentication

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-AUTH-001 | System shall support email/password authentication | P0 | User logs in with registered email and password |
| FR-AUTH-002 | System shall issue JWT tokens containing `user_id`, `tenant_id`, and `roles` | P0 | Token payload verified on each request |
| FR-AUTH-003 | System shall enforce password policy (min 8 chars, uppercase, number, special char) | P0 | Weak passwords rejected at registration/reset |
| FR-AUTH-004 | System shall support password reset via email link | P0 | Reset link expires in 1 hour; single use |
| FR-AUTH-005 | System shall lock account after 5 failed login attempts for 30 minutes | P0 | Lockout message displayed; auto-unlock after timeout |
| FR-AUTH-006 | System shall enforce session timeout after 30 minutes of inactivity (configurable) | P0 | User redirected to login on timeout |
| FR-AUTH-007 | System shall support "Remember Me" with extended token expiry (7 days) | P1 | Token refresh without re-login |
| FR-AUTH-008 | System shall log all login/logout events in audit trail | P0 | Audit log entry with timestamp, IP, user agent |

### 3.2 Role-Based Access Control (RBAC)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-AUTH-009 | System shall provide predefined roles: Super Admin, Tenant Admin, Doctor, Nurse, Receptionist, Lab Tech, Pharmacist, Billing Staff | P0 | Each role has defined permission set |
| FR-AUTH-010 | Tenant admin shall assign roles to users | P0 | Role assignment reflected immediately on next request |
| FR-AUTH-011 | System shall enforce permissions at API endpoint level | P0 | Unauthorized role receives 403 Forbidden |
| FR-AUTH-012 | System shall enforce permissions at UI component level | P0 | Unauthorized actions hidden or disabled |
| FR-AUTH-013 | Tenant admin shall create custom roles with granular permissions (Phase 2) | P2 | Custom role with selected permissions functional |
| FR-AUTH-014 | System shall support multi-role assignment per user | P1 | User with Doctor + Admin roles has combined permissions |

---

## 4. Subscription Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-SUB-001 | System shall offer subscription plans: Starter, Professional, Enterprise | P0 | Plans displayed with features and pricing |
| FR-SUB-002 | System shall provide 14-day free trial on signup | P0 | Trial starts on account creation; countdown visible |
| FR-SUB-003 | System shall collect payment method before trial expiry | P0 | Payment form integrated; card/UPI stored securely |
| FR-SUB-004 | System shall process automatic monthly billing on renewal date | P0 | Invoice generated and payment charged automatically |
| FR-SUB-005 | System shall send billing reminders 7 days and 1 day before renewal | P0 | Email notifications sent per schedule |
| FR-SUB-006 | System shall enforce plan limits (max users, max beds, module access) | P0 | Creating resource beyond limit returns error with upgrade prompt |
| FR-SUB-007 | System shall support plan upgrade with immediate effect and prorated charge | P1 | New features available immediately; prorated invoice generated |
| FR-SUB-008 | System shall support plan downgrade effective next billing cycle | P1 | Downgrade scheduled; confirmation email sent |
| FR-SUB-009 | System shall suspend tenant after 7-day grace period on payment failure | P0 | Tenant status changes to suspended; users see payment notice |
| FR-SUB-010 | System shall provide billing history and invoice download for tenant admin | P0 | List of invoices with PDF download |
| FR-SUB-011 | System shall support annual billing with discount | P1 | Annual plan option with 10-15% discount applied |

---

## 5. Patient Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-PAT-001 | System shall register new patients with: name, DOB, gender, phone, email, address, blood group, emergency contact | P0 | All fields saved; MRN auto-generated |
| FR-PAT-002 | System shall auto-generate unique MRN per tenant in format `MRN-YYYY-NNNNN` | P0 | Sequential MRN unique within tenant |
| FR-PAT-003 | System shall detect potential duplicate patients by phone number and name similarity | P0 | Warning displayed; user can proceed or merge |
| FR-PAT-004 | System shall support patient search by name, phone, MRN, email | P0 | Results returned in < 1 second for 100K records |
| FR-PAT-005 | System shall display patient profile with demographics, visit history, allergies, chronic conditions | P0 | Profile page loads all sections |
| FR-PAT-006 | System shall allow recording patient allergies and chronic conditions | P0 | Allergies flagged prominently in consultation view |
| FR-PAT-007 | System shall support patient photo upload | P1 | Photo displayed on profile and queue |
| FR-PAT-008 | System shall support document attachments (reports, ID proof, consent forms) | P1 | Files uploaded, stored, and downloadable |
| FR-PAT-009 | System shall record patient consent for data processing | P1 | Consent timestamp and method recorded |
| FR-PAT-010 | System shall support patient family/linking (guardian for minors) | P2 | Linked patients visible on profile |
| FR-PAT-011 | System shall maintain complete visit history chronologically | P0 | All OPD/IPD visits listed with date, doctor, diagnosis |
| FR-PAT-012 | System shall support patient import via CSV | P1 | CSV template provided; validation errors reported per row |

---

## 6. Outpatient Department (OPD)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-OPD-001 | System shall support doctor-wise appointment scheduling with configurable time slots | P0 | Calendar view per doctor; slots based on duration config |
| FR-OPD-002 | System shall allow appointment booking by receptionist and walk-in registration | P0 | Appointment created with patient, doctor, date, time |
| FR-OPD-003 | System shall send appointment confirmation and reminder notifications | P1 | SMS/email sent on booking and 1 day before |
| FR-OPD-004 | System shall manage patient queue with token numbers per doctor | P0 | Queue displayed in real-time; token auto-assigned |
| FR-OPD-005 | System shall allow queue reordering and priority marking | P1 | Receptionist can move patients in queue |
| FR-OPD-006 | System shall provide consultation interface for doctors | P0 | Doctor sees patient info, history, vitals entry |
| FR-OPD-007 | System shall support clinical notes entry (chief complaint, examination, diagnosis) | P0 | Notes saved and linked to visit |
| FR-OPD-008 | System shall support ICD-10 diagnosis code selection | P1 | Searchable ICD code dropdown |
| FR-OPD-009 | System shall support vitals recording (BP, pulse, temperature, weight, height, SpO2) | P0 | Vitals saved per visit; trend visible on profile |
| FR-OPD-010 | System shall support e-prescription with drug name, dosage, frequency, duration, instructions | P0 | Prescription generated; sent to pharmacy module |
| FR-OPD-011 | System shall support lab test ordering from consultation | P1 | Lab order created and visible in lab module |
| FR-OPD-012 | System shall support follow-up appointment scheduling from consultation | P0 | Follow-up date suggested and bookable |
| FR-OPD-013 | System shall track consultation status: Waiting → In Consultation → Completed | P0 | Status transitions update queue in real-time |
| FR-OPD-014 | System shall support referral to another doctor (internal) | P1 | Referral note attached; receiving doctor notified |
| FR-OPD-015 | System shall generate visit summary printable PDF | P1 | PDF includes diagnosis, prescription, follow-up |

---

## 7. Inpatient Department (IPD)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-IPD-001 | System shall support patient admission with admission date, admitting doctor, diagnosis, bed assignment | P1 | Admission record created; bed marked occupied |
| FR-IPD-002 | System shall manage ward and bed master (ward name, bed number, type, status) | P1 | Admin configures wards/beds; status: Available, Occupied, Maintenance |
| FR-IPD-003 | System shall display bed availability dashboard | P1 | Visual ward map with color-coded bed status |
| FR-IPD-004 | System shall support nursing notes and vitals charting at configurable intervals | P1 | Vitals recorded with timestamp; chart displayed |
| FR-IPD-005 | System shall support inter-ward/department patient transfer | P2 | Transfer updates bed status; transfer record created |
| FR-IPD-006 | System shall support discharge workflow with discharge summary | P1 | Discharge summary includes diagnosis, treatment, medications, follow-up |
| FR-IPD-007 | System shall calculate length of stay automatically | P1 | LOS displayed on admission record |
| FR-IPD-008 | System shall support IPD daily charges (room, nursing, procedures) | P1 | Daily charges auto-applied to patient bill |
| FR-IPD-009 | System shall track admission status: Admitted → Under Treatment → Discharged | P1 | Status transitions logged |

---

## 8. Laboratory

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-LAB-001 | System shall maintain configurable lab test catalog (name, code, category, price, normal range) | P1 | Admin manages test master; tests searchable |
| FR-LAB-002 | System shall create lab orders from OPD/IPD consultations or standalone | P1 | Order linked to patient and ordering doctor |
| FR-LAB-003 | System shall generate sample ID/barcode for each ordered test | P1 | Unique sample ID generated; printable label |
| FR-LAB-004 | System shall track sample status: Ordered → Collected → Processing → Completed | P1 | Status updates reflected in order tracking |
| FR-LAB-005 | System shall allow result entry by lab technician with validation against normal ranges | P1 | Abnormal values flagged; results saved |
| FR-LAB-006 | System shall generate lab reports in PDF with tenant branding | P1 | Report includes patient info, results, reference ranges, signature |
| FR-LAB-007 | System shall notify ordering doctor when results are available | P1 | In-app and email notification sent |
| FR-LAB-008 | System shall alert on critical/panic values | P2 | Immediate notification to ordering doctor |
| FR-LAB-009 | System shall support bulk result entry for panel tests | P2 | Panel test results entered in single form |
| FR-LAB-010 | System shall track turnaround time (TAT) per test | P2 | TAT report available for lab manager |

---

## 9. Pharmacy

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-PHR-001 | System shall maintain drug master (name, generic, category, unit, price) | P1 | Admin manages drug catalog |
| FR-PHR-002 | System shall receive e-prescriptions from OPD/IPD for dispensing | P1 | Prescription visible in pharmacy queue |
| FR-PHR-003 | System shall support prescription fulfillment with quantity and batch tracking | P1 | Stock deducted on dispense; batch recorded |
| FR-PHR-004 | System shall manage pharmacy inventory (stock in, stock out, current stock) | P1 | Stock levels updated on purchase and dispense |
| FR-PHR-005 | System shall alert when drug stock falls below reorder level | P1 | Low stock notification to pharmacy admin |
| FR-PHR-006 | System shall support purchase order creation and goods receipt | P2 | PO workflow: Create → Approve → Receive → Stock Updated |
| FR-PHR-007 | System shall track drug expiry dates | P2 | Expiry alert 90/60/30 days before |
| FR-PHR-008 | System shall support substitute drug suggestion based on generic name | P2 | Generic match suggested when brand unavailable |

---

## 10. Billing & Finance

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-BIL-001 | System shall maintain service/charge master (name, code, category, price, tax rate) | P0 | Admin configures services; used in billing |
| FR-BIL-002 | System shall generate OPD bills from consultation services and prescriptions | P0 | Bill auto-populated from visit; editable before finalization |
| FR-BIL-003 | System shall generate IPD bills with itemized daily charges | P1 | Running bill updated daily; final bill on discharge |
| FR-BIL-004 | System shall support multiple payment modes: Cash, Card, UPI, Bank Transfer, Insurance | P0 | Payment recorded with mode and reference number |
| FR-BIL-005 | System shall support partial payments and track outstanding balance | P0 | Balance calculated; payment history maintained |
| FR-BIL-006 | System shall generate receipt on payment with unique receipt number | P0 | Receipt printable/PDF; number sequential per tenant |
| FR-BIL-007 | System shall apply configurable tax (GST) on applicable services | P0 | Tax calculated per line item; total tax shown |
| FR-BIL-008 | System shall support discounts (percentage or flat) with authorization | P1 | Discount > 10% requires admin approval |
| FR-BIL-009 | System shall support bill cancellation/void with reason and audit trail | P0 | Voided bill marked; reason recorded; audit logged |
| FR-BIL-010 | System shall provide daily collection report | P0 | Report shows total collection by payment mode for selected date |
| FR-BIL-011 | System shall provide outstanding/due report | P1 | List of patients with unpaid balances |
| FR-BIL-012 | System shall provide revenue report by department, doctor, service category | P1 | Filterable report with date range |
| FR-BIL-013 | System shall support insurance/TPA billing (basic claim tracking) | P2 | Insurance details on patient; claim status tracked |

---

## 11. Reporting & Analytics

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-RPT-001 | System shall provide operational dashboard with key metrics | P1 | Dashboard shows: today's patients, revenue, appointments, bed occupancy |
| FR-RPT-002 | System shall provide OPD report (patient count, doctor-wise, diagnosis-wise) | P1 | Filterable by date range |
| FR-RPT-003 | System shall provide IPD report (admissions, discharges, bed occupancy, ALOS) | P1 | Filterable by date range and ward |
| FR-RPT-004 | System shall provide lab report (tests performed, TAT, revenue) | P2 | Filterable by date range and test category |
| FR-RPT-005 | System shall provide pharmacy report (dispensing, stock, revenue) | P2 | Filterable by date range |
| FR-RPT-006 | System shall support report export to CSV and PDF | P1 | Export button on all reports |
| FR-RPT-007 | System shall provide doctor performance report (patients seen, revenue generated) | P2 | Per-doctor metrics for admin review |
| FR-RPT-008 | System shall provide audit log report for compliance | P0 | Filterable by user, action, date range |

---

## 12. Administration

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-ADM-001 | System shall manage staff/employee records (name, role, department, contact, joining date) | P0 | Staff profile created and linked to user account |
| FR-ADM-002 | System shall manage department master (name, code, head) | P0 | Departments configurable per tenant |
| FR-ADM-003 | System shall manage doctor profiles (specialization, qualification, consultation fee, schedule) | P0 | Doctor profile linked to user; schedule configurable |
| FR-ADM-004 | System shall provide system configuration (date format, currency, tax settings, MRN prefix) | P0 | Settings applied tenant-wide |
| FR-ADM-005 | System shall maintain comprehensive audit log (user, action, entity, timestamp, IP) | P0 | All CRUD operations logged; searchable |
| FR-ADM-006 | System shall support backup notification and data retention policy configuration | P1 | Admin sees last backup date; retention policy displayed |
| FR-ADM-007 | System shall provide user activity report (logins, actions per user) | P1 | Report filterable by user and date |

---

## 13. Notifications

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-NTF-001 | System shall send email notifications for: account creation, password reset, billing reminders | P0 | Emails delivered within 5 minutes |
| FR-NTF-002 | System shall send SMS notifications for: appointment reminders, lab results ready | P1 | SMS delivered via configured gateway |
| FR-NTF-003 | System shall provide in-app notification center | P1 | Bell icon with unread count; notification list |
| FR-NTF-004 | System shall allow users to configure notification preferences | P2 | User can enable/disable notification types |
| FR-NTF-005 | System shall send critical alerts (panic lab values, system errors) immediately | P2 | Real-time push to relevant users |

---

## 14. Cross-Module Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-XMOD-001 | Patient record shall be accessible across all modules (OPD, IPD, Lab, Pharmacy, Billing) | P0 | Single patient ID links all module data |
| FR-XMOD-002 | Billing shall auto-populate charges from OPD consultation, lab orders, pharmacy dispensing, IPD daily charges | P0 | Charges flow from source modules to billing |
| FR-XMOD-003 | All modules shall respect tenant configuration (currency, tax, date format) | P0 | Consistent formatting across modules |
| FR-XMOD-004 | All modules shall enforce RBAC permissions | P0 | Module access controlled by role |
| FR-XMOD-005 | All modules shall record actions in audit log | P0 | Audit entries created for all write operations |

---

## 15. Feature Scope Summary

### 15.1 MVP (Phase 1) — P0 Requirements

- Platform: Tenant management, isolation, organization profile
- Auth: Login, JWT, RBAC (predefined roles), password reset, audit logging
- Subscription: Plans, trial, billing, limits, suspension
- Patient: Registration, search, profile, visit history, allergies
- OPD: Appointments, queue, consultation, vitals, e-prescription
- Billing: Service master, OPD billing, payments, receipts, daily collection
- Admin: Staff, departments, doctors, configuration, audit logs
- Reporting: Audit log report, daily collection report

### 15.2 Phase 2 — P1 Requirements

- IPD: Admission, beds, nursing notes, discharge
- Laboratory: Test catalog, orders, results, reports
- Pharmacy: Drug master, dispensing, inventory
- Extended reporting and dashboards
- Notifications (SMS, in-app)
- Multi-location support

### 15.3 Phase 3+ — P2/P3 Requirements

- Insurance/TPA billing
- Custom roles
- Advanced analytics
- AI features
- API marketplace

---

## 16. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Product Team | Initial FRD |
