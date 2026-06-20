# User Stories

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Last Updated** | June 2026 |
| **Related Documents** | PRD.md, FUNCTIONAL_REQUIREMENTS.md, SPRINT_PLAN.md |

---

## 1. Introduction

This document contains user stories for the Multi-Tenant Hospital Management SaaS Platform, organized by epic and persona. Each story follows the standard format:

> **As a** [persona], **I want** [goal], **so that** [benefit].

Stories include **acceptance criteria**, **priority**, and **story points** (Fibonacci: 1, 2, 3, 5, 8, 13).

### 1.1 Personas Reference

| Persona | Role |
|---------|------|
| **Platform Admin** | SaaS platform operator |
| **Tenant Admin** | Hospital administrator / owner |
| **Receptionist** | Front desk / registration staff |
| **Doctor** | Consulting physician |
| **Nurse** | Nursing staff |
| **Lab Technician** | Laboratory staff |
| **Pharmacist** | Pharmacy staff |
| **Billing Staff** | Billing and finance executive |

---

## 2. Epic: Platform Onboarding & Tenant Management

### US-PLT-001: Self-Service Tenant Registration

| Field | Value |
|-------|-------|
| **As a** | Hospital Owner |
| **I want** | to register my organization on the platform |
| **So that** | I can start using the hospital management system without waiting for manual setup |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Registration form collects: organization name, admin name, email, phone, password
- [ ] Email verification link sent upon submission
- [ ] Account activated only after email verification
- [ ] Unique `tenant_id` assigned upon activation
- [ ] User redirected to onboarding wizard after activation
- [ ] Duplicate email addresses are rejected with clear error message

---

### US-PLT-002: Organization Profile Setup

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | to configure my organization's profile |
| **So that** | the system reflects our hospital's identity on reports and communications |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] Admin can set: organization name, logo, address, phone, email, timezone
- [ ] Logo displayed on invoices, receipts, and lab reports
- [ ] Timezone applied to all date/time displays
- [ ] Changes saved and reflected immediately across the platform
- [ ] Logo upload supports PNG/JPG up to 2MB

---

### US-PLT-003: Subscription Plan Selection

| Field | Value |
|-------|-------|
| **As a** | Hospital Owner |
| **I want** | to choose a subscription plan that fits my facility size |
| **So that** | I pay only for the features and capacity I need |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Plans displayed: Starter, Professional, Enterprise with feature comparison
- [ ] 14-day free trial starts automatically on plan selection
- [ ] Trial limitations enforced (5 users, 100 patients)
- [ ] Payment method collection prompted 3 days before trial expiry
- [ ] Plan upgrade available from settings at any time
- [ ] Current plan and billing cycle visible on dashboard

---

### US-PLT-004: Platform Admin Tenant Management

| Field | Value |
|-------|-------|
| **As a** | Platform Admin |
| **I want** | to view and manage all tenants on the platform |
| **So that** | I can monitor platform health and assist tenants |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] List all tenants with: name, plan, status, created date, last active
- [ ] Filter by status: Active, Trial, Suspended, Cancelled
- [ ] Suspend/reactivate tenant with reason
- [ ] View tenant subscription and billing history
- [ ] Cannot access tenant clinical data without explicit authorization

---

## 3. Epic: Authentication & User Management

### US-AUTH-001: User Login

| Field | Value |
|-------|-------|
| **As a** | Staff Member |
| **I want** | to log in with my email and password |
| **So that** | I can access the system securely |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] Login form accepts email and password
- [ ] JWT token issued on successful authentication
- [ ] Token contains `user_id`, `tenant_id`, and `roles`
- [ ] Invalid credentials show generic error (no email enumeration)
- [ ] Account locked after 5 failed attempts for 30 minutes
- [ ] Redirected to role-appropriate dashboard after login

---

### US-AUTH-002: Password Reset

| Field | Value |
|-------|-------|
| **As a** | Staff Member |
| **I want** | to reset my password via email |
| **So that** | I can regain access if I forget my password |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] "Forgot Password" link on login page
- [ ] Reset email sent within 2 minutes
- [ ] Reset link expires after 1 hour
- [ ] Reset link is single-use
- [ ] New password must meet password policy
- [ ] All active sessions invalidated after password reset

---

### US-AUTH-003: Staff User Management

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | to create and manage staff user accounts |
| **So that** | each team member has appropriate system access |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Create user with: name, email, role, department
- [ ] Invitation email sent to new user
- [ ] Assign one or more predefined roles
- [ ] Deactivate user (preserves audit history)
- [ ] Cannot exceed plan's user limit
- [ ] User list with search and filter by role/department/status

---

### US-AUTH-004: Role-Based Dashboard

| Field | Value |
|-------|-------|
| **As a** | Staff Member |
| **I want** | to see a dashboard relevant to my role |
| **So that** | I can quickly access my most important tasks |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Doctor sees: today's appointments, patient queue, pending lab results
- [ ] Receptionist sees: today's appointments, registration shortcut, queue status
- [ ] Billing Staff sees: today's collections, pending bills, outstanding amounts
- [ ] Tenant Admin sees: operational overview, revenue, staff activity
- [ ] Unauthorized menu items hidden (not just disabled)

---

## 4. Epic: Patient Management

### US-PAT-001: Patient Registration

| Field | Value |
|-------|-------|
| **As a** | Receptionist |
| **I want** | to register a new patient quickly |
| **So that** | the patient can be seen by a doctor without delays |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Registration form: name, DOB, gender, phone, email (optional), address, blood group, emergency contact
- [ ] MRN auto-generated in format `MRN-YYYY-NNNNN`
- [ ] Registration completable in < 2 minutes
- [ ] Duplicate warning if phone number already exists
- [ ] Patient profile created and searchable immediately
- [ ] Optional: link to appointment or walk-in queue

---

### US-PAT-002: Patient Search

| Field | Value |
|-------|-------|
| **As a** | Receptionist |
| **I want** | to search for existing patients |
| **So that** | I can pull up their records instead of creating duplicates |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] Search by name, phone, MRN, or email
- [ ] Results returned in < 1 second
- [ ] Results show: name, MRN, phone, age, last visit date
- [ ] Click result to open patient profile
- [ ] Minimum 2 characters to trigger search
- [ ] Search scoped to current tenant only

---

### US-PAT-003: Patient Profile View

| Field | Value |
|-------|-------|
| **As a** | Doctor |
| **I want** | to view a comprehensive patient profile |
| **So that** | I have complete context before consultation |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Profile shows: demographics, allergies (highlighted), chronic conditions, visit history
- [ ] Visit history shows: date, doctor, diagnosis, prescriptions
- [ ] Vitals trend chart for recent visits
- [ ] Lab results accessible from profile
- [ ] Accessible within 2 clicks from queue or search
- [ ] Allergies displayed prominently with warning indicator

---

### US-PAT-004: Record Patient Allergies

| Field | Value |
|-------|-------|
| **As a** | Doctor |
| **I want** | to record patient allergies |
| **So that** | all staff are aware and can prevent adverse reactions |

**Priority:** P0 | **Points:** 2

**Acceptance Criteria:**
- [ ] Add allergy: substance name, severity (Mild/Moderate/Severe), reaction type
- [ ] Allergies displayed with red warning badge on patient profile
- [ ] Allergies visible during prescription entry
- [ ] Allergy list editable by doctor and nurse roles
- [ ] Audit log records who added/modified allergies

---

### US-PAT-005: Patient Data Import

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | to import existing patient data from a CSV file |
| **So that** | we can migrate from our old system without manual re-entry |

**Priority:** P1 | **Points:** 8

**Acceptance Criteria:**
- [ ] CSV template downloadable from admin panel
- [ ] Upload CSV with validation preview
- [ ] Validation errors shown per row with line number
- [ ] Successful rows imported; failed rows reported
- [ ] Import processes up to 5,000 records
- [ ] Import logged in audit trail

---

## 5. Epic: Outpatient (OPD)

### US-OPD-001: Appointment Scheduling

| Field | Value |
|-------|-------|
| **As a** | Receptionist |
| **I want** | to schedule appointments for patients with specific doctors |
| **So that** | patients know when to visit and doctors can plan their day |

**Priority:** P0 | **Points:** 8

**Acceptance Criteria:**
- [ ] Calendar view per doctor showing available slots
- [ ] Slot duration configurable per doctor (15/20/30 min)
- [ ] Book appointment: select patient, doctor, date, time slot
- [ ] Prevent double-booking of same slot
- [ ] Appointment status: Scheduled, Confirmed, Completed, Cancelled, No-Show
- [ ] Cancelled slots become available again
- [ ] Today's appointments list on receptionist dashboard

---

### US-OPD-002: Walk-In Queue Management

| Field | Value |
|-------|-------|
| **As a** | Receptionist |
| **I want** | to add walk-in patients to a doctor's queue |
| **So that** | patients are seen in an orderly fashion |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Add patient to queue: select patient, select doctor
- [ ] Token number auto-assigned sequentially
- [ ] Queue displayed in real-time for receptionist and doctor
- [ ] Queue shows: token, patient name, wait time, status
- [ ] Status flow: Waiting → In Consultation → Completed
- [ ] Doctor can call next patient from queue

---

### US-OPD-003: Doctor Consultation

| Field | Value |
|-------|-------|
| **As a** | Doctor |
| **I want** | to conduct a consultation with full patient context |
| **So that** | I can provide accurate diagnosis and treatment |

**Priority:** P0 | **Points:** 8

**Acceptance Criteria:**
- [ ] Consultation view shows patient demographics, allergies, history
- [ ] Enter: chief complaint, examination notes, diagnosis
- [ ] Record vitals: BP, pulse, temperature, weight, height, SpO2
- [ ] Select ICD-10 diagnosis codes
- [ ] Consultation auto-saved as draft every 30 seconds
- [ ] Mark consultation as complete
- [ ] Completed consultation added to patient visit history

---

### US-OPD-004: E-Prescription

| Field | Value |
|-------|-------|
| **As a** | Doctor |
| **I want** | to create electronic prescriptions |
| **So that** | patients receive accurate medication orders without handwriting errors |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Add medications: drug name (searchable), dosage, frequency, duration, instructions
- [ ] Drug search from tenant's drug master
- [ ] Multiple medications per prescription
- [ ] Prescription linked to current visit
- [ ] Printable prescription PDF generated
- [ ] Prescription sent to pharmacy module (if enabled)
- [ ] Allergy warning if prescribed drug matches patient allergy

---

### US-OPD-005: Follow-Up Scheduling

| Field | Value |
|-------|-------|
| **As a** | Doctor |
| **I want** | to schedule a follow-up appointment during consultation |
| **So that** | patient continuity of care is maintained |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] "Schedule Follow-Up" button in consultation view
- [ ] Suggest follow-up date (e.g., 1 week, 2 weeks, 1 month)
- [ ] Book follow-up in doctor's calendar
- [ ] Follow-up noted in visit summary
- [ ] Optional: send reminder to patient

---

## 6. Epic: Inpatient (IPD)

### US-IPD-001: Patient Admission

| Field | Value |
|-------|-------|
| **As a** | Receptionist |
| **I want** | to admit a patient to the hospital |
| **So that** | inpatient care can be tracked and billed properly |

**Priority:** P1 | **Points:** 8

**Acceptance Criteria:**
- [ ] Admission form: patient, admitting doctor, diagnosis, ward, bed, admission date/time
- [ ] Only available beds shown for selection
- [ ] Bed status updated to "Occupied" on admission
- [ ] Admission number auto-generated
- [ ] Patient status changed to "Admitted"
- [ ] Admission recorded in patient visit history

---

### US-IPD-002: Bed Management Dashboard

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | to see bed availability across all wards |
| **So that** | I can manage capacity and plan admissions |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] Visual dashboard showing all wards and beds
- [ ] Color-coded: Green (Available), Red (Occupied), Yellow (Maintenance)
- [ ] Click occupied bed to see patient details
- [ ] Summary: total beds, occupied, available, occupancy percentage
- [ ] Filter by ward

---

### US-IPD-003: Patient Discharge

| Field | Value |
|-------|-------|
| **As a** | Doctor |
| **I want** | to discharge a patient with a complete summary |
| **So that** | the patient has documentation for continued care |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] Discharge form: diagnosis, treatment summary, medications, follow-up instructions
- [ ] Discharge summary PDF generated
- [ ] Bed status updated to "Available"
- [ ] Final IPD bill generated
- [ ] Patient status changed to "Discharged"
- [ ] Length of stay calculated and recorded

---

## 7. Epic: Laboratory

### US-LAB-001: Lab Test Ordering

| Field | Value |
|-------|-------|
| **As a** | Doctor |
| **I want** | to order lab tests during consultation |
| **So that** | the lab team knows what tests to perform |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] Search and select tests from lab catalog
- [ ] Order multiple tests in single order
- [ ] Order linked to patient and visit
- [ ] Order visible in lab module immediately
- [ ] Order charges added to patient bill
- [ ] Print sample collection labels

---

### US-LAB-002: Sample Collection & Processing

| Field | Value |
|-------|-------|
| **As a** | Lab Technician |
| **I want** | to track samples from collection to result |
| **So that** | no samples are lost and TAT is monitored |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] View pending orders queue
- [ ] Mark sample as collected with timestamp
- [ ] Unique sample ID generated per test
- [ ] Status tracking: Ordered → Collected → Processing → Completed
- [ ] Filter orders by status, date, patient

---

### US-LAB-003: Lab Result Entry

| Field | Value |
|-------|-------|
| **As a** | Lab Technician |
| **I want** | to enter test results |
| **So that** | doctors and patients can access accurate reports |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] Result entry form with fields per test type
- [ ] Normal range displayed alongside input
- [ ] Abnormal values highlighted automatically
- [ ] Critical values trigger alert to ordering doctor
- [ ] Results saved and report generatable
- [ ] Ordering doctor notified when results ready

---

### US-LAB-004: Lab Report Generation

| Field | Value |
|-------|-------|
| **As a** | Lab Technician |
| **I want** | to generate professional lab reports |
| **So that** | patients and doctors receive clear, branded reports |

**Priority:** P1 | **Points:** 3

**Acceptance Criteria:**
- [ ] PDF report with tenant logo and details
- [ ] Report includes: patient info, test name, result, reference range, flag
- [ ] Authorized signatory name and designation
- [ ] Report downloadable and printable
- [ ] Report accessible from patient profile

---

## 8. Epic: Pharmacy

### US-PHR-001: Prescription Dispensing

| Field | Value |
|-------|-------|
| **As a** | Pharmacist |
| **I want** | to view and fulfill e-prescriptions |
| **So that** | patients receive correct medications promptly |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] View pending prescriptions queue
- [ ] Prescription details: patient, doctor, medications, dosages
- [ ] Mark each medication as dispensed with quantity
- [ ] Stock deducted from inventory on dispense
- [ ] Dispensing charges added to patient bill
- [ ] Partial dispensing supported with remaining quantity tracked

---

### US-PHR-002: Inventory Management

| Field | Value |
|-------|-------|
| **As a** | Pharmacist |
| **I want** | to manage drug inventory |
| **So that** | we never run out of essential medications |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] View current stock levels for all drugs
- [ ] Record stock receipt (purchase entry)
- [ ] Stock automatically deducted on dispensing
- [ ] Low stock alert when quantity below reorder level
- [ ] Expiry date tracking with alerts at 90/60/30 days
- [ ] Stock adjustment with reason (damage, expiry, correction)

---

## 9. Epic: Billing & Finance

### US-BIL-001: OPD Bill Generation

| Field | Value |
|-------|-------|
| **As a** | Billing Staff |
| **I want** | to generate bills for OPD visits |
| **So that** | patients are charged accurately for services received |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Bill auto-populated from visit: consultation fee, procedures, lab orders, pharmacy
- [ ] Manual addition of extra charges from service master
- [ ] Tax (GST) calculated per line item
- [ ] Bill preview before finalization
- [ ] Finalized bill cannot be edited (only voided)
- [ ] Unique bill number generated per tenant

---

### US-BIL-002: Payment Collection

| Field | Value |
|-------|-------|
| **As a** | Billing Staff |
| **I want** | to collect payments against bills |
| **So that** | revenue is recorded and receipts are issued |

**Priority:** P0 | **Points:** 5

**Acceptance Criteria:**
- [ ] Payment modes: Cash, Card, UPI, Bank Transfer
- [ ] Full and partial payments supported
- [ ] Receipt auto-generated with unique receipt number
- [ ] Receipt printable and downloadable as PDF
- [ ] Outstanding balance updated after payment
- [ ] Payment recorded with user, timestamp, and mode

---

### US-BIL-003: Daily Collection Report

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | to view today's collection summary |
| **So that** | I can monitor daily revenue and reconcile cash |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] Report shows: total collection, breakdown by payment mode
- [ ] Filter by date (default: today)
- [ ] Shows: number of bills, total billed, total collected, outstanding
- [ ] Export to CSV and PDF
- [ ] Accessible from admin dashboard

---

### US-BIL-004: Service Master Configuration

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | to configure chargeable services and their prices |
| **So that** | billing reflects our current fee schedule |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] CRUD operations on service master
- [ ] Fields: name, code, category, price, tax rate, active/inactive
- [ ] Categories: Consultation, Procedure, Lab, Pharmacy, Room, Nursing, Other
- [ ] Inactive services not available for new bills but preserved in history
- [ ] Bulk import via CSV

---

### US-BIL-005: Bill Void/Cancellation

| Field | Value |
|-------|-------|
| **As a** | Billing Staff |
| **I want** | to void an incorrect bill |
| **So that** | financial records remain accurate with proper audit trail |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] Void action requires reason (mandatory text)
- [ ] Voided bill marked clearly (not deleted)
- [ ] Payments against voided bill flagged for refund processing
- [ ] Void action logged in audit trail with user and reason
- [ ] Only bills from today or with admin approval can be voided

---

## 10. Epic: Reporting & Analytics

### US-RPT-001: Operational Dashboard

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | an operational dashboard with key metrics |
| **So that** | I can monitor hospital performance at a glance |

**Priority:** P1 | **Points:** 8

**Acceptance Criteria:**
- [ ] Widgets: today's patients, revenue, appointments, bed occupancy
- [ ] Trend charts: patient volume (7 days), revenue (7 days)
- [ ] Doctor-wise patient count for today
- [ ] Data refreshes on page load (manual refresh button)
- [ ] Date range filter for historical view

---

### US-RPT-002: Audit Log Report

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | to view audit logs of all system actions |
| **So that** | I can ensure compliance and investigate issues |

**Priority:** P0 | **Points:** 3

**Acceptance Criteria:**
- [ ] Log entries: timestamp, user, action, entity type, entity ID, IP address
- [ ] Filter by: user, action type, date range, entity type
- [ ] Export to CSV
- [ ] Logs are read-only (cannot be modified or deleted)
- [ ] Retained for minimum 7 years

---

## 11. Epic: Subscription & Billing (Platform)

### US-SUB-001: Automated Subscription Billing

| Field | Value |
|-------|-------|
| **As a** | Platform Admin |
| **I want** | subscriptions to bill automatically |
| **So that** | revenue collection is reliable and requires no manual intervention |

**Priority:** P0 | **Points:** 8

**Acceptance Criteria:**
- [ ] Payment charged automatically on renewal date
- [ ] Invoice generated and emailed to tenant admin
- [ ] Failed payment triggers retry (3 attempts over 7 days)
- [ ] Tenant suspended after grace period
- [ ] Billing history accessible to tenant admin

---

### US-SUB-002: Plan Upgrade

| Field | Value |
|-------|-------|
| **As a** | Tenant Admin |
| **I want** | to upgrade my subscription plan |
| **So that** | I can access more features as my hospital grows |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] View current plan and available upgrades
- [ ] Upgrade takes effect immediately
- [ ] Prorated charge calculated and displayed before confirmation
- [ ] New features/modules unlocked immediately
- [ ] User and bed limits updated
- [ ] Confirmation email sent

---

## 12. Epic: Notifications

### US-NTF-001: Appointment Reminders

| Field | Value |
|-------|-------|
| **As a** | Receptionist |
| **I want** | patients to receive appointment reminders |
| **So that** | no-show rates are reduced |

**Priority:** P1 | **Points:** 5

**Acceptance Criteria:**
- [ ] SMS/email reminder sent 1 day before appointment
- [ ] Reminder includes: date, time, doctor name, hospital name
- [ ] Reminder sent only if patient has phone/email on file
- [ ] Tenant admin can enable/disable reminders
- [ ] Delivery status tracked

---

## 13. Story Summary by Priority

### P0 — MVP (Phase 1)

| Story ID | Title | Points |
|----------|-------|--------|
| US-PLT-001 | Self-Service Tenant Registration | 5 |
| US-PLT-002 | Organization Profile Setup | 3 |
| US-PLT-003 | Subscription Plan Selection | 5 |
| US-PLT-004 | Platform Admin Tenant Management | 5 |
| US-AUTH-001 | User Login | 3 |
| US-AUTH-002 | Password Reset | 3 |
| US-AUTH-003 | Staff User Management | 5 |
| US-AUTH-004 | Role-Based Dashboard | 5 |
| US-PAT-001 | Patient Registration | 5 |
| US-PAT-002 | Patient Search | 3 |
| US-PAT-003 | Patient Profile View | 5 |
| US-PAT-004 | Record Patient Allergies | 2 |
| US-OPD-001 | Appointment Scheduling | 8 |
| US-OPD-002 | Walk-In Queue Management | 5 |
| US-OPD-003 | Doctor Consultation | 8 |
| US-OPD-004 | E-Prescription | 5 |
| US-OPD-005 | Follow-Up Scheduling | 3 |
| US-BIL-001 | OPD Bill Generation | 5 |
| US-BIL-002 | Payment Collection | 5 |
| US-BIL-003 | Daily Collection Report | 3 |
| US-BIL-004 | Service Master Configuration | 3 |
| US-BIL-005 | Bill Void/Cancellation | 3 |
| US-RPT-002 | Audit Log Report | 3 |
| US-SUB-001 | Automated Subscription Billing | 8 |
| **Total** | | **102** |

### P1 — Phase 2

| Story ID | Title | Points |
|----------|-------|--------|
| US-PAT-005 | Patient Data Import | 8 |
| US-IPD-001 | Patient Admission | 8 |
| US-IPD-002 | Bed Management Dashboard | 5 |
| US-IPD-003 | Patient Discharge | 5 |
| US-LAB-001 | Lab Test Ordering | 5 |
| US-LAB-002 | Sample Collection & Processing | 5 |
| US-LAB-003 | Lab Result Entry | 5 |
| US-LAB-004 | Lab Report Generation | 3 |
| US-PHR-001 | Prescription Dispensing | 5 |
| US-PHR-002 | Inventory Management | 5 |
| US-RPT-001 | Operational Dashboard | 8 |
| US-SUB-002 | Plan Upgrade | 5 |
| US-NTF-001 | Appointment Reminders | 5 |
| **Total** | | **72** |

---

## 14. Definition of Done

A user story is considered **Done** when:

1. All acceptance criteria are met and verified
2. Code is peer-reviewed and merged to main branch
3. Unit tests written with ≥ 80% coverage for new backend logic
4. API endpoint documented in OpenAPI/Swagger
5. UI matches design specifications
6. `tenant_id` isolation verified for all new endpoints
7. RBAC permissions enforced and tested
8. No critical or high-severity bugs open
9. Deployed to staging and smoke-tested
10. Product Owner acceptance obtained

---

## 15. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Product Team | Initial user stories |
