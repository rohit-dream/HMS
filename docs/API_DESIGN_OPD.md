# OPD API Design (MVP)

## Outpatient Department — REST Contract

| Field | Value |
|-------|-------|
| **Document Version** | 2.0 |
| **Status** | **Complete (Sprint 5 — MVP-051)** |
| **Last Updated** | June 2026 |
| **Base Path** | `/api/v1/opd` |
| **OpenAPI Tag** | `OPD` |
| **Implements** | FR-OPD-001 through FR-OPD-013 (P0); FR-OPD-005, FR-OPD-014 (P1 partial) |
| **Related** | `API_DESIGN.md` §6 Appointments, §7 Billing · `DATABASE_DESIGN.md` §4.4 · `RBAC_DESIGN.md` §5 |

---

## 1. Introduction

This document defines the **authoritative REST contract** for the Outpatient Department (OPD) module. It extends global conventions from `API_DESIGN.md` (envelope, headers, pagination, error format).

### 1.1 Design Principles

| Principle | OPD Implementation |
|-----------|-------------------|
| Tenant isolation | `tenant_id` from JWT only; cross-tenant resource IDs return `404` |
| Visit-centric resources | Vitals, notes, and prescriptions nest under `/opd/visits/{visit_id}` |
| Queue per doctor per day | Token numbers scoped to `(tenant_id, doctor_id, queue_date)` |
| Status machines | Enforced server-side; invalid transitions return `409` |
| Clinical immutability | Completed visits: notes/vitals read-only; prescriptions locked |
| Billing hook | `POST .../complete` may return `billing_invoice_id` when auto-billing enabled |
| Implementation | **Sprint 5:** OpenAPI stubs (`501`); **Sprint 9:** full business logic |

### 1.2 Dependencies

| Prerequisite module | Required for |
|--------------------|--------------|
| Patients (`/api/v1/patients`) | Walk-in visit creation |
| Doctors (`/api/v1/doctors`) | Visit assignment, queue |
| Appointments (`/api/v1/appointments`) | Appointment-linked visits |
| Billing (`/api/v1/billing/invoices`) | Post-consultation invoicing (Sprint 10) |
| Pharmacy (`/api/v1/pharmacy`) | Prescription dispensing (Sprint 8) |

---

## 2. Scope

### 2.1 In Scope (MVP)

| Capability | FR IDs |
|------------|--------|
| OPD visits (walk-in + appointment-linked) | FR-OPD-002, FR-OPD-013 |
| Doctor-wise token queue | FR-OPD-004, FR-OPD-005 |
| Consultation lifecycle (start / complete) | FR-OPD-006, FR-OPD-013 |
| Vitals recording | FR-OPD-009 |
| Clinical notes (complaint, exam, diagnosis, plan) | FR-OPD-007 |
| E-prescription (header + line items) | FR-OPD-010 |
| Visit complete → billing hook (optional auto-draft) | Billing integration |

### 2.2 Out of Scope (Post-MVP)

| Capability | Target |
|------------|--------|
| WebSocket real-time queue | Post-MVP (`opd:queue:{doctor_id}:{date}` channel) |
| ICD-10 coded diagnosis search | FR-OPD-008 (P1) |
| Lab orders from consultation | FR-OPD-011 (Sprint 7) |
| Follow-up appointment auto-book | FR-OPD-012 (uses Appointments API) |
| Referral notifications | FR-OPD-014 (P1) |
| Visit summary PDF | FR-OPD-015 (P1) |
| IPD admissions | Sprint 11+ |

---

## 3. RBAC & Authorization

### 3.1 Permission Matrix

| Permission | Roles (typical) | Operations |
|------------|-----------------|------------|
| `opd:read` | Doctor, Nurse, Receptionist, Admin | List/get visits, vitals, notes, prescriptions |
| `opd:create` | Receptionist, Admin | Create walk-in visits |
| `opd:update` | Receptionist, Admin | Update visit metadata before consultation |
| `opd:queue` | Receptionist, Nurse, Admin | Queue board, call, skip, reorder |
| `opd:consult` | Doctor, Admin | Start/complete consultation, vitals, notes |
| `opd:prescribe` | Doctor, Admin | Create prescriptions |

Wildcard `*:*` (hospital owner) and `opd:*` (if added) grant all OPD actions.

### 3.2 Role Restrictions

| Rule | Enforcement |
|------|-------------|
| Receptionist cannot `opd:consult` or `opd:prescribe` | `403` on write endpoints |
| Doctor cannot `opd:queue` reorder (optional tenant setting) | `403` if restricted |
| Completed visit | `409` on vitals/notes/prescription writes |

---

## 4. Shared Schemas

### 4.1 Enumerations

```typescript
// Visit
type OpdVisitType = "walk_in" | "appointment";
type OpdVisitStatus = "waiting" | "in_consultation" | "completed" | "cancelled";

// Queue
type OpdQueueStatus = "waiting" | "called" | "in_consultation" | "completed" | "skipped";
type OpdQueuePriority = "normal" | "urgent";

// Clinical notes
type OpdNoteType = "examination" | "diagnosis" | "plan" | "general";

// Prescription
type OpdPrescriptionStatus = "active" | "dispensed" | "partially_dispensed" | "cancelled";
type MedicineRoute = "oral" | "topical" | "iv" | "im" | "sc" | "inhalation" | "other";
```

### 4.2 Core Resource Objects

#### `OpdVisit`

```json
{
  "id": "f6a7b8c9-d0e1-2345-f012-456789012345",
  "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "visit_number": "OPD-2026-00482",
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "patient_name": "Anita Sharma",
  "patient_mrn": "MRN-000128",
  "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "doctor_name": "Dr. Vikram Patel",
  "appointment_id": null,
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
  "location_name": "Main Branch",
  "visit_date": "2026-06-20",
  "visit_type": "walk_in",
  "status": "waiting",
  "token_number": 12,
  "chief_complaint": "Fever and cough for 3 days",
  "started_at": null,
  "completed_at": null,
  "queue_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-06-20T08:15:00Z",
  "updated_at": "2026-06-20T08:15:00Z"
}
```

#### `OpdQueueEntry`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "opd_visit_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
  "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "patient_name": "Anita Sharma",
  "token_number": 12,
  "queue_date": "2026-06-20",
  "status": "waiting",
  "priority": "normal",
  "chief_complaint": "Fever and cough for 3 days",
  "called_at": null,
  "visit_status": "waiting"
}
```

#### `OpdVitals`

```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "opd_visit_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
  "recorded_at": "2026-06-20T09:05:00Z",
  "recorded_by_user_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
  "blood_pressure_systolic": 120,
  "blood_pressure_diastolic": 80,
  "pulse_rate": 78,
  "temperature": 37.2,
  "temperature_unit": "celsius",
  "respiratory_rate": 16,
  "spo2": 98,
  "weight_kg": 62.5,
  "height_cm": 165.0,
  "bmi": 22.9,
  "notes": "Patient appears alert"
}
```

#### `OpdClinicalNote`

```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "opd_visit_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
  "note_type": "diagnosis",
  "content": "Upper respiratory tract infection",
  "icd_code": null,
  "icd_description": null,
  "is_final": false,
  "created_by_user_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "created_at": "2026-06-20T09:20:00Z"
}
```

#### `OpdPrescription` (with items)

```json
{
  "id": "d4e5f6a7-b8c9-0123-def0-234567890123",
  "opd_visit_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "prescription_number": "RX-2026-00089",
  "prescribed_at": "2026-06-20T09:25:00Z",
  "status": "active",
  "notes": "Take after meals",
  "items": [
    {
      "id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
      "medicine_id": null,
      "medicine_name": "Paracetamol 500mg",
      "dosage": "500mg",
      "frequency": "twice daily",
      "duration": "5 days",
      "route": "oral",
      "instructions": "After food",
      "quantity": 10
    }
  ]
}
```

---

## 5. Status Machines

### 5.1 Visit Status

```
                    ┌─────────────┐
     create ───────►│   waiting   │
                    └──────┬──────┘
                           │ POST /start (opd:consult)
                           ▼
                    ┌──────────────────┐
                    │ in_consultation  │
                    └────────┬─────────┘
                             │ POST /complete
                             ▼
                    ┌─────────────┐
                    │  completed  │  (terminal)
                    └─────────────┘

  waiting | in_consultation ──POST /cancel──► cancelled (terminal)
```

| From | To | Action | Permission |
|------|-----|--------|------------|
| — | `waiting` | Create visit | `opd:create` |
| `waiting` | `in_consultation` | Start consultation | `opd:consult` |
| `in_consultation` | `completed` | Complete visit | `opd:consult` |
| `waiting`, `in_consultation` | `cancelled` | Cancel visit | `opd:update` |

### 5.2 Queue Status

```
waiting ──call──► called ──start visit──► in_consultation ──complete──► completed
   │                  │
   └──skip────────────┴──skip──► skipped
```

---

## 6. Endpoint Summary

| # | Method | Endpoint | Permission | FR |
|---|--------|----------|------------|-----|
| 1 | POST | `/opd/visits` | `opd:create` | FR-OPD-002 |
| 2 | GET | `/opd/visits` | `opd:read` | FR-OPD-013 |
| 3 | GET | `/opd/visits/{visit_id}` | `opd:read` | FR-OPD-006 |
| 4 | PATCH | `/opd/visits/{visit_id}` | `opd:update` | FR-OPD-002 |
| 5 | POST | `/opd/visits/{visit_id}/cancel` | `opd:update` | FR-OPD-013 |
| 6 | POST | `/opd/visits/{visit_id}/start` | `opd:consult` | FR-OPD-006 |
| 7 | POST | `/opd/visits/{visit_id}/complete` | `opd:consult` | FR-OPD-013 |
| 8 | GET | `/opd/queue` | `opd:queue` | FR-OPD-004 |
| 9 | POST | `/opd/queue` | `opd:queue` | FR-OPD-004 |
| 10 | PATCH | `/opd/queue/{queue_id}` | `opd:queue` | FR-OPD-005 |
| 11 | POST | `/opd/queue/{queue_id}/call` | `opd:queue` | FR-OPD-004 |
| 12 | POST | `/opd/queue/{queue_id}/complete` | `opd:queue` | FR-OPD-013 |
| 13 | POST | `/opd/queue/{queue_id}/skip` | `opd:queue` | FR-OPD-005 |
| 14 | POST | `/opd/visits/{visit_id}/vitals` | `opd:consult` | FR-OPD-009 |
| 15 | GET | `/opd/visits/{visit_id}/vitals` | `opd:read` | FR-OPD-009 |
| 16 | POST | `/opd/visits/{visit_id}/notes` | `opd:consult` | FR-OPD-007 |
| 17 | GET | `/opd/visits/{visit_id}/notes` | `opd:read` | FR-OPD-007 |
| 18 | POST | `/opd/visits/{visit_id}/prescriptions` | `opd:prescribe` | FR-OPD-010 |
| 19 | GET | `/opd/visits/{visit_id}/prescriptions` | `opd:read` | FR-OPD-010 |
| 20 | GET | `/opd/visits/{visit_id}/prescriptions/{prescription_id}` | `opd:read` | FR-OPD-010 |

**Total: 20 endpoints** (Sprint 5 DoD: ≥15 documented).

---

## 7. Visits API

### 7.1 POST `/opd/visits`

Create an OPD visit (walk-in or from confirmed appointment).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:create` |
| **Status** | `201 Created` |

**Request:**

```json
{
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
  "visit_date": "2026-06-20",
  "visit_type": "walk_in",
  "appointment_id": null,
  "chief_complaint": "Fever and cough for 3 days",
  "add_to_queue": true,
  "queue_priority": "normal"
}
```

**Response `201`:** `OpdVisit` object with auto-assigned `visit_number`, `token_number`, and `queue_id` when `add_to_queue` is true.

**Validation:**

| Field | Rules |
|-------|-------|
| `patient_id` | Required UUID; must exist in tenant |
| `doctor_id` | Required UUID; doctor must be active and `is_available` |
| `visit_date` | Required; defaults to today; cannot be >30 days in past |
| `visit_type` | `walk_in` or `appointment` |
| `appointment_id` | Required when `visit_type` is `appointment`; appointment must be `confirmed` and same doctor/date |
| `chief_complaint` | Optional; max 2000 chars |
| `add_to_queue` | Default `true` for walk-in |
| `queue_priority` | `normal` or `urgent`; default `normal` |

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | Patient, doctor, or appointment not found (cross-tenant → `404`) |
| `409` | Duplicate visit for same patient+doctor+date; appointment already has visit |
| `422` | Validation failure |

**Side effects:** Creates `clinical.opd_visits` row; optionally creates `clinical.opd_queue` with next token number.

---

### 7.2 GET `/opd/visits`

List OPD visits with filters.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `opd:read` |

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `doctor_id` | UUID | Filter by doctor |
| `patient_id` | UUID | Filter by patient |
| `visit_date` | date | Specific date |
| `from_date` | date | Range start |
| `to_date` | date | Range end |
| `status` | string | `waiting`, `in_consultation`, `completed`, `cancelled` |
| `visit_type` | string | `walk_in`, `appointment` |
| `location_id` | UUID | Branch filter |
| `page`, `page_size`, `sort` | — | Standard pagination (`API_DESIGN.md` §2.5) |

**Response `200`:** Paginated list of `OpdVisit` summaries.

---

### 7.3 GET `/opd/visits/{visit_id}`

Get visit detail including queue snapshot and prescription count.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `opd:read` |

**Response `200`:** Full `OpdVisit` plus embedded:

```json
{
  "vitals_count": 1,
  "notes_count": 3,
  "prescriptions_count": 1,
  "latest_vitals": { },
  "queue": { }
}
```

**Errors:** `404` if visit not in tenant.

**Audit:** PHI access logged to `audit.phi_access_logs` (Sprint 5+).

---

### 7.4 PATCH `/opd/visits/{visit_id}`

Update visit metadata before consultation starts.

| Attribute | Value |
|-----------|-------|
| **Method** | `PATCH` |
| **Authorization** | `opd:update` |

**Request (partial):**

```json
{
  "chief_complaint": "Updated complaint",
  "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123"
}
```

**Validation:** Only allowed when `status` is `waiting`. Cannot change `patient_id`.

**Errors:** `409` if visit not in `waiting` status.

---

### 7.5 POST `/opd/visits/{visit_id}/cancel`

Cancel a visit and remove from active queue.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:update` |

**Request:**

```json
{
  "reason": "Patient did not arrive"
}
```

**Response `200`:** Updated `OpdVisit` with `status: cancelled`.

**Validation:** Allowed from `waiting` or `in_consultation`. `reason` required, 1–500 chars.

**Errors:** `409` if already `completed` or `cancelled`.

---

### 7.6 POST `/opd/visits/{visit_id}/start`

Doctor starts consultation.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:consult` |

**Request:** Empty body `{}` or optional `{ "doctor_id": "..." }` when covering doctor.

**Response `200`:**

```json
{
  "data": {
    "id": "f6a7b8c9-d0e1-2345-f012-456789012345",
    "status": "in_consultation",
    "started_at": "2026-06-20T09:10:00Z"
  }
}
```

**Side effects:** Updates visit + queue status to `in_consultation`; sets `started_at`.

**Errors:** `409` if not in `waiting` status.

---

### 7.7 POST `/opd/visits/{visit_id}/complete`

Complete consultation and finalize visit.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:consult` |

**Request:**

```json
{
  "finalize_notes": true,
  "create_billing_draft": true,
  "follow_up_notes": "Review in 1 week if fever persists"
}
```

**Response `200`:**

```json
{
  "data": {
    "id": "f6a7b8c9-d0e1-2345-f012-456789012345",
    "status": "completed",
    "completed_at": "2026-06-20T09:30:00Z",
    "billing_invoice_id": "b8c9d0e1-f2a3-4567-1234-678901234567"
  }
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `finalize_notes` | Default `true`; sets `is_final` on all visit notes |
| `create_billing_draft` | Default per tenant setting; creates draft invoice with consultation fee |
| Visit must be `in_consultation` | |

**Errors:** `409` if not `in_consultation`; `422` if required clinical data missing (tenant-configurable).

**Side effects:** Queue → `completed`; appointment → `completed` if linked.

---

## 8. Queue API

### 8.1 GET `/opd/queue`

Poll doctor queue for a date (MVP: client polls every 5 seconds).

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `opd:queue` |

**Query parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `doctor_id` | UUID | Yes | Doctor whose queue to fetch |
| `date` | date | No | Defaults to today |
| `location_id` | UUID | No | Branch filter |
| `status` | string | No | Filter: `waiting`, `called`, `in_consultation` |

**Response `200`:**

```json
{
  "data": {
    "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
    "queue_date": "2026-06-20",
    "current_token": 11,
    "waiting_count": 8,
    "entries": [ ]
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Performance target:** <500ms p95 with seed data (Sprint 9).

---

### 8.2 POST `/opd/queue`

Add existing visit to queue (or re-queue after skip).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:queue` |

**Request:**

```json
{
  "opd_visit_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
  "priority": "urgent"
}
```

**Response `201`:** `OpdQueueEntry` with assigned `token_number`.

**Errors:** `409` if visit already in active queue for doctor/date.

---

### 8.3 PATCH `/opd/queue/{queue_id}`

Reorder queue or change priority (FR-OPD-005).

| Attribute | Value |
|-----------|-------|
| **Method** | `PATCH` |
| **Authorization** | `opd:queue` |

**Request:**

```json
{
  "priority": "urgent",
  "position": 3
}
```

**Validation:** `position` is 1-based target index among `waiting` entries. Only `waiting` entries can be reordered.

**Errors:** `409` if queue entry not in `waiting` status.

---

### 8.4 POST `/opd/queue/{queue_id}/call`

Call next patient (updates display token).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:queue` |

**Response `200`:** `OpdQueueEntry` with `status: called`, `called_at` set.

---

### 8.5 POST `/opd/queue/{queue_id}/complete`

Mark queue entry complete (usually via visit complete; explicit for edge cases).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:queue` |

**Response `200`:** Queue entry `status: completed`.

---

### 8.6 POST `/opd/queue/{queue_id}/skip`

Skip patient in queue (FR-OPD-005).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:queue` |

**Request:**

```json
{
  "reason": "Patient stepped out"
}
```

**Response `200`:** Queue entry `status: skipped`.

---

## 9. Vitals API

### 9.1 POST `/opd/visits/{visit_id}/vitals`

Record vitals during consultation.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:consult` |
| **Status** | `201 Created` |

**Request:**

```json
{
  "blood_pressure_systolic": 120,
  "blood_pressure_diastolic": 80,
  "pulse_rate": 78,
  "temperature": 37.2,
  "respiratory_rate": 16,
  "spo2": 98,
  "weight_kg": 62.5,
  "height_cm": 165.0,
  "notes": "Patient appears alert"
}
```

**Validation:**

| Field | Range |
|-------|-------|
| `blood_pressure_systolic` | 60–250 mmHg |
| `blood_pressure_diastolic` | 40–150 mmHg |
| `pulse_rate` | 30–220 bpm |
| `temperature` | 30.0–45.0 (unit from tenant `clinical.vitals_unit`) |
| `respiratory_rate` | 5–60 |
| `spo2` | 50–100 % |
| `weight_kg` | 0.5–500 |
| `height_cm` | 30–250 |

**Computed:** Server calculates `bmi` when weight and height provided.

**Errors:** `409` if visit `completed` or `cancelled`.

---

### 9.2 GET `/opd/visits/{visit_id}/vitals`

List all vitals recordings for a visit (typically one; multiple allowed for re-check).

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `opd:read` |

**Response `200`:** Array of `OpdVitals` ordered by `recorded_at` DESC.

---

## 10. Clinical Notes API

### 10.1 POST `/opd/visits/{visit_id}/notes`

Add clinical note.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:consult` |
| **Status** | `201 Created` |

**Request:**

```json
{
  "note_type": "examination",
  "content": "Chest clear on auscultation. No wheeze.",
  "icd_code": null,
  "icd_description": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `note_type` | Required enum |
| `content` | Required; 1–10000 chars |
| `icd_code` | Optional; max 10 chars (P1 ICD search) |

**Errors:** `409` if visit completed and tenant disallows append.

---

### 10.2 GET `/opd/visits/{visit_id}/notes`

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `opd:read` |

**Query:** `note_type` filter optional.

**Response `200`:** Array of `OpdClinicalNote`.

---

## 11. Prescriptions API

### 11.1 POST `/opd/visits/{visit_id}/prescriptions`

Create e-prescription with line items.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `opd:prescribe` |
| **Status** | `201 Created` |

**Request:**

```json
{
  "notes": "Take after meals",
  "items": [
    {
      "medicine_id": null,
      "medicine_name": "Paracetamol 500mg",
      "dosage": "500mg",
      "frequency": "twice daily",
      "duration": "5 days",
      "route": "oral",
      "instructions": "After food",
      "quantity": 10
    }
  ]
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `items` | Required; 1–30 items |
| `medicine_name` | Required per item; 1–255 chars |
| `dosage`, `frequency`, `duration` | Required per item |
| `quantity` | Optional; positive integer |
| Visit status | Must be `in_consultation` (not completed) |

**Response `201`:** `OpdPrescription` with auto `prescription_number`.

**Side effects:** Prescription visible in pharmacy queue (Sprint 8).

**Errors:** `409` if visit completed.

---

### 11.2 GET `/opd/visits/{visit_id}/prescriptions`

List prescriptions for visit.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `opd:read` |

**Response `200`:** Array of `OpdPrescription` (items included).

---

### 11.3 GET `/opd/visits/{visit_id}/prescriptions/{prescription_id}`

Get single prescription with items.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `opd:read` |

**Errors:** `404` cross-tenant or prescription not on visit.

---

## 12. OPD Error Catalog

| Code | HTTP | Message (example) |
|------|------|-------------------|
| `opd_visit_not_found` | 404 | OPD visit not found |
| `opd_invalid_status_transition` | 409 | Cannot start visit in status completed |
| `opd_visit_already_in_queue` | 409 | Visit already queued for this doctor today |
| `opd_queue_not_found` | 404 | Queue entry not found |
| `opd_queue_not_waiting` | 409 | Only waiting patients can be reordered |
| `opd_consultation_required` | 409 | Visit must be in consultation to add prescription |
| `opd_visit_completed` | 409 | Cannot modify completed visit |
| `opd_duplicate_appointment_visit` | 409 | Appointment already has an OPD visit |
| `opd_doctor_unavailable` | 422 | Doctor is not available for OPD |

All errors use standard envelope (`API_DESIGN.md` §2.3).

---

## 13. Multi-Tenant & RLS

| Table | RLS | Composite FK |
|-------|-----|--------------|
| `clinical.opd_visits` | `tenant_id = current_setting('app.tenant_id')` | `(tenant_id, patient_id)` → `core.patients` |
| `clinical.opd_queue` | ✅ | `(tenant_id, opd_visit_id)` → `opd_visits` |
| `clinical.opd_vitals` | ✅ | `(tenant_id, opd_visit_id)` → `opd_visits` |
| `clinical.opd_clinical_notes` | ✅ | `(tenant_id, opd_visit_id)` → `opd_visits` |
| `clinical.opd_prescriptions` | ✅ | `(tenant_id, opd_visit_id)` → `opd_visits` |
| `clinical.opd_prescription_items` | ✅ | `(tenant_id, prescription_id)` → `opd_prescriptions` |

**Repository pattern:** All writes via `TenantScopedRepository` with `SET app.tenant_id` before queries.

**IDOR:** `GET /opd/visits/{uuid}` returns `404` (not `403`) when UUID belongs to another tenant.

---

## 14. Database Mapping

| API Resource | Table(s) | Number generation |
|--------------|----------|-----------------|
| Visit | `clinical.opd_visits` | `generate_visit_number(tenant_id)` |
| Queue | `clinical.opd_queue` | Token: `MAX(token_number)+1` per doctor/date |
| Vitals | `clinical.opd_vitals` | — |
| Notes | `clinical.opd_clinical_notes` | — |
| Prescription | `clinical.opd_prescriptions`, `opd_prescription_items` | `generate_prescription_number(tenant_id)` |

Migration: `008_opd_tables` (Sprint 9).

---

## 15. Pydantic Schema Reference (MVP-052)

Planned module layout:

```
backend/app/domains/clinical/schemas/opd/
├── visit.py          # OpdVisitCreate, OpdVisitResponse, OpdVisitUpdate
├── queue.py          # OpdQueueCreate, OpdQueueResponse, OpdQueueReorder
├── vitals.py         # OpdVitalsCreate, OpdVitalsResponse
├── notes.py          # OpdNoteCreate, OpdNoteResponse
└── prescription.py   # OpdPrescriptionCreate, OpdPrescriptionItemCreate

backend/app/api/v1/opd/
├── router.py         # Aggregates sub-routers
├── visits.py
├── queue.py
├── vitals.py
├── notes.py
└── prescriptions.py
```

Sprint 5 stubs return `501 Not Implemented` with schemas registered in OpenAPI.

---

## 16. Integration Hooks

| Event | Downstream |
|-------|------------|
| Visit created from appointment | `appointments.status` → `confirmed` (unchanged until complete) |
| Visit completed | Optional `POST /billing/invoices` draft; `appointments.status` → `completed` |
| Prescription created | Pharmacy dispense queue entry (Sprint 8) |
| PHI read on visit detail | `audit.phi_access_logs` write |

---

## 17. Manual Testing Checklist (Sprint 9 implementation)

1. Register patient → create walk-in visit → verify token in queue.
2. Book appointment → create visit with `appointment_id` → verify link.
3. Receptionist calls patient → doctor starts → records vitals + notes + Rx → completes.
4. Verify receptionist gets `403` on `POST .../prescriptions`.
5. Verify tenant B cannot `GET` tenant A visit by UUID (`404`).
6. Complete visit → verify optional billing draft invoice.

---

## 18. Sprint Assignment

| Sprint | Deliverable |
|--------|-------------|
| **S5 (MVP-051)** | ✅ This document — complete spec |
| **S5 (MVP-052)** | OpenAPI router stubs (`501`) |
| **S9** | Alembic `008_opd_tables` + full implementation |
| **S10** | Billing auto-draft on visit complete |

---

## Document History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | Sprint 4 | Initial endpoint summary stub |
| 2.0 | Sprint 5 | Full schemas, validation, 20 endpoints, error catalog, RLS mapping |
