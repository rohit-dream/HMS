# API Design Document

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Last Updated** | June 2026 |
| **Author** | Senior API Architecture |
| **Base URL** | `https://{subdomain}.platform.com/api/v1` |
| **Framework** | FastAPI (Python 3.11+) |
| **Related Documents** | RBAC_DESIGN.md, SYSTEM_ARCHITECTURE.md, DATABASE_DESIGN.md, MULTI_TENANT_DESIGN.md |

---

## 1. Introduction

This document defines the **REST API** contract for the Hospital Management SaaS Platform. All endpoints are versioned, tenant-scoped, JWT-authenticated (unless public), and validated using **Pydantic v2** models compatible with **FastAPI** auto-generated OpenAPI documentation.

### 1.1 Design Principles

| Principle | Implementation |
|-----------|----------------|
| RESTful resources | Nouns for resources; HTTP verbs for actions |
| Versioning | URL prefix `/api/v1` |
| Tenant isolation | `tenant_id` from JWT — never from client body |
| Consistent envelope | `{ data, meta, errors }` on all responses |
| Idempotency | `X-Idempotency-Key` header on POST (billing, payments) |
| Pagination | Cursor or offset via query params |
| Filtering & sorting | Query parameters on list endpoints |
| OpenAPI | Auto-generated at `/api/v1/docs` (Swagger UI) |

---

## 2. Global Conventions

### 2.1 Base URL

```
Production:  https://{subdomain}.platform.com/api/v1
Staging:     https://{subdomain}.staging.platform.com/api/v1
Local:       http://localhost:8000/api/v1
```

### 2.2 Required Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes (authenticated) | `Bearer {access_token}` |
| `Content-Type` | Yes (JSON body) | `application/json` |
| `Accept` | Recommended | `application/json` |
| `X-Request-ID` | Optional | Client correlation ID; server generates if absent |
| `X-Idempotency-Key` | Conditional | UUID for idempotent POST (payments, invoices) |

### 2.3 Response Envelope

**Success:**

```json
{
  "data": { },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-06-17T10:30:00.123Z",
    "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
  },
  "errors": null
}
```

**Paginated list:**

```json
{
  "data": [ ],
  "meta": {
    "request_id": "...",
    "timestamp": "...",
    "tenant_id": "...",
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 150,
      "total_pages": 8
    }
  },
  "errors": null
}
```

**Validation error (422):**

```json
{
  "data": null,
  "meta": { "request_id": "...", "timestamp": "..." },
  "errors": [
    {
      "code": "validation_error",
      "field": "phone",
      "message": "Phone number must be 10 digits"
    }
  ]
}
```

### 2.4 HTTP Status Codes

| Code | Usage |
|------|-------|
| `200` | Successful GET, PUT, PATCH |
| `201` | Successful POST (resource created) |
| `204` | Successful DELETE (no body) |
| `400` | Malformed request |
| `401` | Missing or invalid authentication |
| `402` | Plan limit exceeded |
| `403` | Insufficient permissions or tenant suspended |
| `404` | Resource not found (includes cross-tenant IDOR) |
| `409` | Conflict (duplicate MRN, double-booked slot) |
| `422` | Pydantic validation failure |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

### 2.5 Common Query Parameters (List Endpoints)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number (1-based) |
| `page_size` | integer | `20` | Items per page (max 100) |
| `sort` | string | `-created_at` | Sort field; prefix `-` for DESC |
| `search` | string | — | Full-text / field search |
| `status` | string | — | Filter by status enum |
| `from_date` | date | — | Filter start date (ISO 8601) |
| `to_date` | date | — | Filter end date (ISO 8601) |

### 2.6 FastAPI Router Structure

```
app/
├── api/
│   └── v1/
│       ├── router.py              # Aggregates all module routers
│       ├── auth.py
│       ├── patients.py
│       ├── doctors.py
│       ├── appointments.py
│       ├── billing.py
│       ├── pharmacy.py
│       ├── inventory.py
│       ├── laboratory.py
│       └── staff.py
├── schemas/                       # Pydantic models (request/response)
├── services/                      # Business logic
├── repositories/                  # Data access
└── core/
    ├── security.py                # JWT, @requires decorator
    └── dependencies.py            # get_db, get_current_user
```

### 2.7 Pydantic Base Pattern

```python
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime

class APIResponse(BaseModel, Generic[T]):
    data: T | None = None
    meta: ResponseMeta
    errors: list[ErrorDetail] | None = None

class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    date_of_birth: date
    gender: Literal["male", "female", "other"]
    phone: str = Field(..., pattern=r"^[0-9]{10}$")
    email: EmailStr | None = None

    model_config = ConfigDict(str_strip_whitespace=True)
```

---

## 3. Module: Authentication

**Base path:** `/api/v1/auth`  
**Tag:** `Authentication`  
Most endpoints are **public** or **authenticated** without module-specific RBAC.

### 3.1 Endpoint Summary

| # | Method | Endpoint | Auth | Permission |
|---|--------|----------|------|------------|
| 1 | POST | `/auth/register` | Public | — |
| 2 | POST | `/auth/login` | Public | — |
| 3 | POST | `/auth/refresh` | Cookie | — |
| 4 | POST | `/auth/logout` | Bearer | — |
| 5 | POST | `/auth/forgot-password` | Public | — |
| 6 | POST | `/auth/reset-password` | Public | — |
| 7 | POST | `/auth/accept-invite` | Public | — |
| 8 | GET | `/auth/me` | Bearer | — |

---

### 3.2 POST `/auth/register`

Register a new tenant and admin user (self-service signup).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | Public |

**Request:**

```json
{
  "organization_name": "Apollo Clinic",
  "slug": "apollo-clinic",
  "admin_first_name": "Rajesh",
  "admin_last_name": "Kumar",
  "email": "admin@apollo.com",
  "phone": "9876543210",
  "password": "SecurePass@123",
  "plan_code": "starter",
  "country": "IN",
  "timezone": "Asia/Kolkata"
}
```

**Response `201`:**

```json
{
  "data": {
    "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "slug": "apollo-clinic",
    "subdomain": "apollo-clinic",
    "status": "trial",
    "trial_ends_at": "2026-07-01T00:00:00Z",
    "verification_email_sent": true
  },
  "meta": { "request_id": "...", "timestamp": "..." },
  "errors": null
}
```

**Validation (Pydantic):**

| Field | Rules |
|-------|-------|
| `organization_name` | Required, 2–255 chars |
| `slug` | Required, `^[a-z0-9-]+$`, 3–100 chars, unique platform-wide |
| `email` | Valid email format |
| `phone` | 10-digit numeric |
| `password` | Min 8 chars, 1 uppercase, 1 number, 1 special char |
| `plan_code` | Enum: `starter`, `professional`, `enterprise` |

**FastAPI:**

```python
@router.post("/register", status_code=201, response_model=APIResponse[TenantRegisterResponse])
async def register(payload: TenantRegisterRequest, idempotency_key: str = Header(..., alias="X-Idempotency-Key")):
    ...
```

---

### 3.3 POST `/auth/login`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | Public |

**Request:**

```json
{
  "email": "doctor@apollo.com",
  "password": "SecurePass@123"
}
```

**Response `200`:**

```json
{
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "email": "doctor@apollo.com",
      "first_name": "Vikram",
      "last_name": "Patel",
      "roles": ["doctor"],
      "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    }
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Response headers:** `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict`

**Validation:**

| Field | Rules |
|-------|-------|
| `email` | Required, valid email |
| `password` | Required, non-empty |

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` | Invalid credentials |
| `423` | Account locked (5 failed attempts) |
| `403` | Tenant suspended/cancelled |

**Authorization:** Resolved via subdomain + email lookup; `tenant_id` embedded in JWT.

---

### 3.4 POST `/auth/refresh`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | HttpOnly `refresh_token` cookie |

**Request:** No body (cookie-based).

**Response `200`:**

```json
{
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "meta": { "request_id": "...", "timestamp": "..." },
  "errors": null
}
```

**Validation:** Refresh token hash must exist in `user_sessions` and not be revoked/expired.

---

### 3.5 POST `/auth/logout`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | Bearer token required |

**Request:** Empty body.

**Response `204`:** No content. Clears refresh token cookie.

---

### 3.6 POST `/auth/forgot-password`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | Public |

**Request:**

```json
{
  "email": "doctor@apollo.com"
}
```

**Response `200`:** Always returns success (prevents email enumeration).

```json
{
  "data": { "message": "If the email exists, a reset link has been sent." },
  "meta": { "request_id": "...", "timestamp": "..." },
  "errors": null
}
```

---

### 3.7 POST `/auth/reset-password`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | Public (token in body) |

**Request:**

```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecure@456"
}
```

**Response `200`:**

```json
{
  "data": { "message": "Password updated successfully." },
  "meta": { "request_id": "...", "timestamp": "..." },
  "errors": null
}
```

**Validation:** Token single-use, 1-hour expiry; password policy enforced.

---

### 3.8 POST `/auth/accept-invite`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | Public (invite token) |

**Request:**

```json
{
  "invite_token": "invite-token-from-email",
  "password": "SecurePass@123"
}
```

**Response `200`:** Same structure as login (access token + user).

---

### 3.9 GET `/auth/me`

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | Bearer token |

**Response `200`:**

```json
{
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "doctor@apollo.com",
    "first_name": "Vikram",
    "last_name": "Patel",
    "roles": ["doctor"],
    "permissions": ["patient:read", "opd:consult", "opd:prescribe"],
    "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "staff_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "location_id": null
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

---

## 4. Module: Patients

**Base path:** `/api/v1/patients`  
**Tag:** `Patients`

### 4.1 Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | GET | `/patients` | `patient:read` |
| 2 | POST | `/patients` | `patient:create` |
| 3 | GET | `/patients/{patient_id}` | `patient:read` |
| 4 | PUT | `/patients/{patient_id}` | `patient:update` |
| 5 | DELETE | `/patients/{patient_id}` | `patient:delete` |
| 6 | GET | `/patients/{patient_id}/allergies` | `patient:read` |
| 7 | POST | `/patients/{patient_id}/allergies` | `patient:update` |
| 8 | DELETE | `/patients/{patient_id}/allergies/{allergy_id}` | `patient:update` |
| 9 | POST | `/patients/{patient_id}/documents` | `patient:create` |
| 10 | POST | `/patients/import` | `patient:export` |

---

### 4.2 GET `/patients`

List and search patients.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `patient:read` |

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Name, phone, MRN, email |
| `page` | integer | Page number |
| `page_size` | integer | Items per page |
| `location_id` | UUID | Filter by branch |

**Response `200`:**

```json
{
  "data": [
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "mrn": "MRN-2026-00042",
      "first_name": "Anita",
      "last_name": "Sharma",
      "date_of_birth": "1985-03-15",
      "gender": "female",
      "phone": "9876543210",
      "email": "anita@email.com",
      "blood_group": "B+",
      "last_visit_date": "2026-06-10",
      "created_at": "2026-01-20T08:00:00Z"
    }
  ],
  "meta": {
    "request_id": "...",
    "timestamp": "...",
    "tenant_id": "...",
    "pagination": { "page": 1, "page_size": 20, "total_items": 1, "total_pages": 1 }
  },
  "errors": null
}
```

**Validation:** `page_size` max 100; `search` min 2 chars if provided.

**Authorization roles:** All tenant roles.

---

### 4.3 POST `/patients`

Register a new patient.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `patient:create` |

**Request:**

```json
{
  "first_name": "Anita",
  "last_name": "Sharma",
  "date_of_birth": "1985-03-15",
  "gender": "female",
  "phone": "9876543210",
  "email": "anita@email.com",
  "blood_group": "B+",
  "address_line1": "123 MG Road",
  "city": "Mumbai",
  "state": "Maharashtra",
  "postal_code": "400001",
  "emergency_contact": {
    "name": "Ravi Sharma",
    "relationship": "spouse",
    "phone": "9876543211"
  },
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123"
}
```

**Response `201`:**

```json
{
  "data": {
    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "mrn": "MRN-2026-00042",
    "first_name": "Anita",
    "last_name": "Sharma",
    "date_of_birth": "1985-03-15",
    "gender": "female",
    "phone": "9876543210",
    "created_at": "2026-06-17T10:30:00Z"
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `first_name` | Required, 1–100 chars |
| `date_of_birth` | Required, valid date, not in future |
| `gender` | Enum: `male`, `female`, `other` |
| `phone` | Required, 10 digits; duplicate warning returned in meta if exists |
| `blood_group` | Optional, enum: `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-` |
| `email` | Optional, valid email |

**Authorization roles:** Receptionist, Hospital Admin, Hospital Owner.

**Errors:** `409` if trial patient limit exceeded.

---

### 4.4 GET `/patients/{patient_id}`

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `patient:read` |

**Path parameters:** `patient_id` — UUID

**Response `200`:** Full patient profile including allergies, contacts, recent visits summary.

**Errors:** `404` if not found or belongs to another tenant.

---

### 4.5 PUT `/patients/{patient_id}`

| Attribute | Value |
|-----------|-------|
| **Method** | `PUT` |
| **Authorization** | `patient:update` |

**Request:** Same fields as POST (partial update via PATCH also supported in implementation).

**Response `200`:** Updated patient object.

**Validation:** `phone` uniqueness check per tenant; optimistic lock via `version` field (optional header `If-Match`).

---

### 4.6 DELETE `/patients/{patient_id}`

| Attribute | Value |
|-----------|-------|
| **Method** | `DELETE` |
| **Authorization** | `patient:delete` |

**Response `204`:** Soft delete (`deleted_at` set).

**Authorization roles:** Hospital Admin, Hospital Owner only.

---

### 4.7 POST `/patients/{patient_id}/allergies`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `patient:update` |

**Request:**

```json
{
  "allergen": "Penicillin",
  "severity": "severe",
  "reaction": "Anaphylaxis",
  "onset_date": "2010-05-01"
}
```

**Response `201`:** Allergy record with `id`.

**Validation:** `severity` enum: `mild`, `moderate`, `severe`; `allergen` required.

---

### 4.8 POST `/patients/import`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Content-Type** | `multipart/form-data` |
| **Authorization** | `patient:export` |

**Request:** `file` — CSV (max 5MB, max 5000 rows).

**Response `202`:**

```json
{
  "data": {
    "job_id": "import-job-uuid",
    "status": "processing",
    "message": "Import queued. Check status at /patients/import/{job_id}"
  },
  "meta": { "request_id": "...", "timestamp": "..." },
  "errors": null
}
```

---

## 5. Module: Doctors

**Base path:** `/api/v1/doctors`  
**Tag:** `Doctors`

### 5.1 Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | GET | `/doctors` | `patient:read` |
| 2 | POST | `/doctors` | `admin:users` |
| 3 | GET | `/doctors/{doctor_id}` | `patient:read` |
| 4 | PUT | `/doctors/{doctor_id}` | `admin:users` |
| 5 | GET | `/doctors/{doctor_id}/schedule` | `appointment:read` |
| 6 | PUT | `/doctors/{doctor_id}/schedule` | `admin:settings` |
| 7 | GET | `/doctors/{doctor_id}/availability` | `appointment:read` |

---

### 5.2 GET `/doctors`

List doctors (for appointment booking, referrals).

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `patient:read` |

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `department_id` | UUID | Filter by department |
| `specialization` | string | Filter by specialization |
| `is_available` | boolean | Only accepting patients |
| `location_id` | UUID | Filter by branch |

**Response `200`:**

```json
{
  "data": [
    {
      "id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
      "staff_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "first_name": "Vikram",
      "last_name": "Patel",
      "specialization": "General Medicine",
      "qualification": "MBBS, MD",
      "consultation_fee": 500.00,
      "follow_up_fee": 300.00,
      "department_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "department_name": "General Medicine",
      "is_available": true
    }
  ],
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

---

### 5.3 POST `/doctors`

Create doctor profile (links to existing staff record).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `admin:users` |

**Request:**

```json
{
  "staff_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "registration_number": "MH-12345",
  "specialization": "General Medicine",
  "qualification": "MBBS, MD",
  "consultation_fee": 500.00,
  "follow_up_fee": 300.00,
  "department_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "bio": "15 years experience in internal medicine"
}
```

**Response `201`:** Doctor object with `id`.

**Validation:**

| Field | Rules |
|-------|-------|
| `staff_id` | Required, must exist in tenant, not already a doctor |
| `specialization` | Required, 1–150 chars |
| `consultation_fee` | Required, >= 0 |
| `registration_number` | Optional, max 50 chars |

**Authorization roles:** Hospital Admin, Hospital Owner.

---

### 5.4 GET `/doctors/{doctor_id}/availability`

Get available slots for appointment booking.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `appointment:read` |

**Query parameters:**

| Param | Type | Required |
|-------|------|----------|
| `date` | date (ISO) | Yes |
| `location_id` | UUID | No |

**Response `200`:**

```json
{
  "data": {
    "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
    "date": "2026-06-20",
    "slots": [
      { "start_time": "09:00", "end_time": "09:20", "available": true },
      { "start_time": "09:20", "end_time": "09:40", "available": false },
      { "start_time": "09:40", "end_time": "10:00", "available": true }
    ]
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

---

### 5.5 PUT `/doctors/{doctor_id}/schedule`

Update weekly schedule template.

| Attribute | Value |
|-----------|-------|
| **Method** | `PUT` |
| **Authorization** | `admin:settings` |

**Request:**

```json
{
  "schedules": [
    {
      "day_of_week": 1,
      "start_time": "09:00",
      "end_time": "13:00",
      "slot_duration_minutes": 20,
      "max_patients_per_slot": 1,
      "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
      "is_active": true
    }
  ]
}
```

**Validation:** `day_of_week` 0–6; `end_time` > `start_time`; `slot_duration_minutes` in [10, 15, 20, 30, 60].

---

## 6. Module: Appointments

**Base path:** `/api/v1/appointments`  
**Tag:** `Appointments`

### 6.1 Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | GET | `/appointments` | `appointment:read` |
| 2 | POST | `/appointments` | `appointment:create` |
| 3 | GET | `/appointments/{appointment_id}` | `appointment:read` |
| 4 | PATCH | `/appointments/{appointment_id}` | `appointment:update` |
| 5 | DELETE | `/appointments/{appointment_id}` | `appointment:update` |
| 6 | POST | `/appointments/{appointment_id}/confirm` | `appointment:update` |
| 7 | POST | `/appointments/{appointment_id}/cancel` | `appointment:update` |

---

### 6.2 GET `/appointments`

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `appointment:read` |

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `doctor_id` | UUID | Filter by doctor |
| `patient_id` | UUID | Filter by patient |
| `appointment_date` | date | Specific date |
| `from_date` | date | Date range start |
| `to_date` | date | Date range end |
| `status` | string | `scheduled`, `confirmed`, `completed`, `cancelled`, `no_show` |

**Response `200`:** Paginated list of appointment objects.

---

### 6.3 POST `/appointments`

Book a new appointment.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `appointment:create` |

**Request:**

```json
{
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
  "appointment_date": "2026-06-20",
  "start_time": "09:00",
  "end_time": "09:20",
  "appointment_type": "new",
  "notes": "Follow-up for blood pressure"
}
```

**Response `201`:**

```json
{
  "data": {
    "id": "f6a7b8c9-d0e1-2345-f012-456789012345",
    "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "patient_name": "Anita Sharma",
    "doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
    "doctor_name": "Dr. Vikram Patel",
    "appointment_date": "2026-06-20",
    "start_time": "09:00",
    "end_time": "09:20",
    "appointment_type": "new",
    "status": "scheduled",
    "created_at": "2026-06-17T10:30:00Z"
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `patient_id` | Required, UUID, exists in tenant |
| `doctor_id` | Required, UUID, doctor `is_available` |
| `appointment_date` | Required, not in past |
| `start_time` / `end_time` | Required, slot must be available |
| `appointment_type` | Enum: `new`, `follow_up`, `emergency` |

**Errors:** `409` if slot already booked.

**Authorization roles:** Receptionist.

---

### 6.4 PATCH `/appointments/{appointment_id}`

Reschedule or update appointment.

| Attribute | Value |
|-----------|-------|
| **Method** | `PATCH` |
| **Authorization** | `appointment:update` |

**Request (partial):**

```json
{
  "appointment_date": "2026-06-21",
  "start_time": "10:00",
  "end_time": "10:20",
  "notes": "Rescheduled by patient request"
}
```

**Validation:** Cannot reschedule `completed` or `cancelled` appointments.

---

### 6.5 POST `/appointments/{appointment_id}/cancel`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `appointment:update` |

**Request:**

```json
{
  "cancelled_reason": "Patient requested cancellation"
}
```

**Response `200`:** Appointment with `status: cancelled`.

**Validation:** `cancelled_reason` required, 1–500 chars.

---

## 7. Module: Billing

**Base path:** `/api/v1/billing`  
**Tag:** `Billing`

### 7.1 Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | GET | `/billing/services` | `billing:read` |
| 2 | POST | `/billing/services` | `billing:update` |
| 3 | PUT | `/billing/services/{service_id}` | `billing:update` |
| 4 | GET | `/billing/invoices` | `billing:read` |
| 5 | POST | `/billing/invoices` | `billing:create` |
| 6 | GET | `/billing/invoices/{invoice_id}` | `billing:read` |
| 7 | POST | `/billing/invoices/{invoice_id}/line-items` | `billing:create` |
| 8 | POST | `/billing/invoices/{invoice_id}/finalize` | `billing:update` |
| 9 | POST | `/billing/invoices/{invoice_id}/void` | `billing:void` |
| 10 | POST | `/billing/payments` | `billing:collect` |
| 11 | GET | `/billing/payments/{payment_id}` | `billing:read` |
| 12 | GET | `/billing/reports/daily-collection` | `reports:financial` |

---

### 7.2 GET `/billing/services`

Service / charge master list.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `billing:read` |

**Query:** `category`, `is_active`, `search`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "a7b8c9d0-e1f2-3456-0123-567890123456",
      "code": "CONS-GEN",
      "name": "General Consultation",
      "category": "consultation",
      "price": 500.00,
      "tax_rate": 0.00,
      "is_tax_inclusive": false,
      "is_active": true
    }
  ],
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

---

### 7.3 POST `/billing/invoices`

Create a draft invoice.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `billing:create` |

**Request:**

```json
{
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "opd_visit_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
  "invoice_date": "2026-06-17",
  "due_date": "2026-06-17",
  "line_items": [
    {
      "billing_service_id": "a7b8c9d0-e1f2-3456-0123-567890123456",
      "description": "General Consultation",
      "quantity": 1,
      "unit_price": 500.00,
      "tax_rate": 0.00,
      "discount_amount": 0.00
    }
  ],
  "notes": "OPD visit billing"
}
```

**Response `201`:**

```json
{
  "data": {
    "id": "b8c9d0e1-f2a3-4567-1234-678901234567",
    "invoice_number": "INV-2026-00128",
    "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "status": "draft",
    "subtotal": 500.00,
    "tax_amount": 0.00,
    "discount_amount": 0.00,
    "total_amount": 500.00,
    "paid_amount": 0.00,
    "balance_amount": 500.00,
    "line_items": [ ],
    "created_at": "2026-06-17T10:30:00Z"
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `patient_id` | Required, exists in tenant |
| `line_items` | Min 1 item; `quantity` > 0; `unit_price` >= 0 |
| `invoice_date` | Required, valid date |

**Authorization roles:** Accountant, Receptionist.

---

### 7.4 POST `/billing/invoices/{invoice_id}/finalize`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `billing:update` |

**Request:** Empty body.

**Response `200`:** Invoice with `status: finalized`; `finalized_at` set. Invoice becomes immutable (void only).

**Errors:** `409` if already finalized or no line items.

---

### 7.5 POST `/billing/invoices/{invoice_id}/void`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `billing:void` |

**Request:**

```json
{
  "void_reason": "Duplicate invoice created in error"
}
```

**Response `200`:** Invoice with `status: voided`.

**Validation:** `void_reason` required; only today's invoices voidable by Accountant (older requires Hospital Owner).

**Authorization roles:** Accountant, Hospital Owner.

---

### 7.6 POST `/billing/payments`

Record payment against invoice(s).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `billing:collect` |
| **Headers** | `X-Idempotency-Key` required |

**Request:**

```json
{
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "amount": 500.00,
  "payment_mode": "upi",
  "reference_number": "UPI123456789",
  "allocations": [
    {
      "invoice_id": "b8c9d0e1-f2a3-4567-1234-678901234567",
      "allocated_amount": 500.00
    }
  ],
  "notes": "Full payment via PhonePe"
}
```

**Response `201`:**

```json
{
  "data": {
    "id": "c9d0e1f2-a3b4-5678-2345-789012345678",
    "receipt_number": "RCP-2026-00089",
    "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "amount": 500.00,
    "payment_mode": "upi",
    "status": "completed",
    "payment_date": "2026-06-17T10:35:00Z",
    "allocations": [
      {
        "invoice_id": "b8c9d0e1-f2a3-4567-1234-678901234567",
        "allocated_amount": 500.00
      }
    ]
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `amount` | Required, > 0 |
| `payment_mode` | Enum: `cash`, `card`, `upi`, `bank_transfer`, `insurance` |
| `allocations` | Sum of `allocated_amount` must equal `amount` |
| `invoice_id` | Must be finalized, not voided |

**Authorization roles:** Accountant, Receptionist.

---

### 7.7 GET `/billing/reports/daily-collection`

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `reports:financial` |

**Query:** `date` (default today), `location_id`

**Response `200`:**

```json
{
  "data": {
    "date": "2026-06-17",
    "total_collected": 45000.00,
    "total_billed": 52000.00,
    "outstanding": 7000.00,
    "invoice_count": 42,
    "by_payment_mode": {
      "cash": 15000.00,
      "upi": 20000.00,
      "card": 10000.00
    }
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

---

## 8. Module: Pharmacy

**Base path:** `/api/v1/pharmacy`  
**Tag:** `Pharmacy`

### 8.1 Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | GET | `/pharmacy/medicines` | `pharmacy:read` |
| 2 | POST | `/pharmacy/medicines` | `pharmacy:create` |
| 3 | PUT | `/pharmacy/medicines/{medicine_id}` | `pharmacy:update` |
| 4 | GET | `/pharmacy/prescriptions/pending` | `pharmacy:read` |
| 5 | GET | `/pharmacy/prescriptions/{prescription_id}` | `pharmacy:read` |
| 6 | POST | `/pharmacy/dispense` | `pharmacy:dispense` |
| 7 | GET | `/pharmacy/dispense` | `pharmacy:read` |
| 8 | GET | `/pharmacy/dispense/{dispense_id}` | `pharmacy:read` |

---

### 8.2 GET `/pharmacy/medicines`

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `pharmacy:read` |

**Query:** `search`, `category`, `is_active`, `page`, `page_size`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "d0e1f2a3-b4c5-6789-3456-890123456789",
      "code": "MED-PARA500",
      "name": "Paracetamol 500mg",
      "generic_name": "Paracetamol",
      "category": "tablet",
      "unit": "tablet",
      "strength": "500mg",
      "unit_price": 2.50,
      "reorder_level": 100,
      "is_active": true
    }
  ],
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

---

### 8.3 POST `/pharmacy/medicines`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `pharmacy:create` |

**Request:**

```json
{
  "code": "MED-PARA500",
  "name": "Paracetamol 500mg",
  "generic_name": "Paracetamol",
  "category": "tablet",
  "unit": "tablet",
  "strength": "500mg",
  "manufacturer": "PharmaCo Ltd",
  "unit_price": 2.50,
  "reorder_level": 100
}
```

**Validation:** `code` unique per tenant; `unit_price` >= 0; `category` enum.

**Authorization roles:** Pharmacist, Hospital Admin.

---

### 8.4 GET `/pharmacy/prescriptions/pending`

List prescriptions awaiting dispense.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `pharmacy:read` |

**Response `200`:** List with patient name, doctor, prescribed items, prescription date.

---

### 8.5 POST `/pharmacy/dispense`

Fulfill prescription.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `pharmacy:dispense` |

**Request:**

```json
{
  "prescription_id": "e1f2a3b4-c5d6-7890-4567-901234567890",
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "items": [
    {
      "prescription_item_id": "f2a3b4c5-d6e7-8901-5678-012345678901",
      "medicine_id": "d0e1f2a3-b4c5-6789-3456-890123456789",
      "inventory_id": "a3b4c5d6-e7f8-9012-6789-123456789012",
      "quantity_dispensed": 20
    }
  ]
}
```

**Response `201`:**

```json
{
  "data": {
    "id": "b4c5d6e7-f8a9-0123-7890-234567890123",
    "dispense_number": "DSP-2026-00045",
    "prescription_id": "e1f2a3b4-c5d6-7890-4567-901234567890",
    "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "status": "completed",
    "total_amount": 50.00,
    "dispensed_at": "2026-06-17T11:00:00Z",
    "items": [ ]
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `prescription_id` | Required, status `active` or `partially_dispensed` |
| `items` | Min 1; `quantity_dispensed` <= stock on hand |
| Stock check | Sufficient `pharmacy_inventory.quantity_on_hand` |

**Errors:** `409` if insufficient stock.

**Authorization roles:** Pharmacist only.

---

## 9. Module: Inventory

**Base path:** `/api/v1/inventory`  
**Tag:** `Inventory`  
Manages pharmacy stock levels, movements, and purchase orders.

### 9.1 Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | GET | `/inventory` | `pharmacy:read` |
| 2 | GET | `/inventory/{inventory_id}` | `pharmacy:read` |
| 3 | POST | `/inventory/stock-in` | `pharmacy:create` |
| 4 | POST | `/inventory/adjust` | `pharmacy:update` |
| 5 | GET | `/inventory/movements` | `pharmacy:read` |
| 6 | GET | `/inventory/low-stock` | `pharmacy:read` |
| 7 | GET | `/inventory/expiring` | `pharmacy:read` |
| 8 | POST | `/inventory/purchase-orders` | `pharmacy:create` |
| 9 | GET | `/inventory/purchase-orders` | `pharmacy:read` |

---

### 9.2 GET `/inventory`

List stock by medicine and batch.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `pharmacy:read` |

**Query:**

| Param | Description |
|-------|-------------|
| `medicine_id` | Filter by medicine |
| `location_id` | Filter by branch |
| `in_stock_only` | boolean, default true |

**Response `200`:**

```json
{
  "data": [
    {
      "id": "a3b4c5d6-e7f8-9012-6789-123456789012",
      "medicine_id": "d0e1f2a3-b4c5-6789-3456-890123456789",
      "medicine_name": "Paracetamol 500mg",
      "batch_number": "BATCH-2026-001",
      "quantity_on_hand": 500,
      "unit_cost": 1.80,
      "expiry_date": "2027-06-30",
      "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
      "supplier_name": "MedSupply Co"
    }
  ],
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

---

### 9.3 POST `/inventory/stock-in`

Record goods receipt / stock purchase.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `pharmacy:create` |

**Request:**

```json
{
  "medicine_id": "d0e1f2a3-b4c5-6789-3456-890123456789",
  "batch_number": "BATCH-2026-002",
  "quantity": 1000,
  "unit_cost": 1.75,
  "expiry_date": "2027-12-31",
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
  "supplier_name": "MedSupply Co",
  "purchase_order_id": null,
  "notes": "Monthly restock"
}
```

**Response `201`:**

```json
{
  "data": {
    "inventory_id": "a3b4c5d6-e7f8-9012-6789-123456789012",
    "movement_id": "c5d6e7f8-a9b0-1234-8901-345678901234",
    "medicine_id": "d0e1f2a3-b4c5-6789-3456-890123456789",
    "quantity_on_hand": 1000,
    "movement_type": "purchase"
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `medicine_id` | Required, exists, active |
| `batch_number` | Required, unique per medicine per tenant |
| `quantity` | Required, integer > 0 |
| `expiry_date` | Required, must be future date |
| `unit_cost` | Required, >= 0 |

**Authorization roles:** Pharmacist, Hospital Admin.

---

### 9.4 POST `/inventory/adjust`

Manual stock adjustment (damage, expiry, correction).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `pharmacy:update` |

**Request:**

```json
{
  "inventory_id": "a3b4c5d6-e7f8-9012-6789-123456789012",
  "quantity": -10,
  "reason": "expired",
  "notes": "10 tablets expired and disposed"
}
```

**Validation:** `quantity` non-zero integer; `reason` enum: `damage`, `expired`, `correction`, `theft`; resulting stock >= 0.

**Authorization roles:** Pharmacist, Hospital Admin.

---

### 9.5 GET `/inventory/low-stock`

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `pharmacy:read` |

**Response `200`:** Medicines where total `quantity_on_hand` < `reorder_level`.

---

### 9.6 GET `/inventory/movements`

Immutable stock ledger.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `pharmacy:read` |

**Query:** `medicine_id`, `movement_type`, `from_date`, `to_date`, `page`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "c5d6e7f8-a9b0-1234-8901-345678901234",
      "medicine_id": "d0e1f2a3-b4c5-6789-3456-890123456789",
      "movement_type": "dispense",
      "quantity": -20,
      "reference_type": "dispense",
      "reference_id": "b4c5d6e7-f8a9-0123-7890-234567890123",
      "created_at": "2026-06-17T11:00:00Z",
      "created_by": "pharmacist-user-uuid"
    }
  ],
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "...", "pagination": { } },
  "errors": null
}
```

---

## 10. Module: Laboratory

**Base path:** `/api/v1/laboratory`  
**Tag:** `Laboratory`

### 10.1 Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | GET | `/laboratory/tests` | `laboratory:read` |
| 2 | POST | `/laboratory/tests` | `laboratory:update` |
| 3 | PUT | `/laboratory/tests/{test_id}` | `laboratory:update` |
| 4 | GET | `/laboratory/orders` | `laboratory:read` |
| 5 | POST | `/laboratory/orders` | `laboratory:create` |
| 6 | GET | `/laboratory/orders/{order_id}` | `laboratory:read` |
| 7 | POST | `/laboratory/orders/{order_id}/cancel` | `laboratory:update` |
| 8 | POST | `/laboratory/samples/{sample_id}/collect` | `laboratory:update` |
| 9 | POST | `/laboratory/results` | `laboratory:update` |
| 10 | POST | `/laboratory/results/{result_id}/verify` | `lab:verify` |
| 11 | POST | `/laboratory/reports/{order_id}/generate` | `lab:report` |
| 12 | GET | `/laboratory/reports/{report_id}` | `laboratory:read` |

---

### 10.2 GET `/laboratory/tests`

Lab test catalog.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `laboratory:read` |

**Query:** `category`, `search`, `is_active`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "e7f8a9b0-c1d2-3456-9012-678901234567",
      "code": "CBC",
      "name": "Complete Blood Count",
      "category": "hematology",
      "sample_type": "blood",
      "price": 350.00,
      "tat_hours": 4,
      "normal_range": "See report",
      "is_active": true
    }
  ],
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

---

### 10.3 POST `/laboratory/orders`

Create lab order (from consultation or standalone).

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `laboratory:create` |

**Request:**

```json
{
  "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "ordering_doctor_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "opd_visit_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
  "priority": "routine",
  "clinical_notes": "Routine health checkup",
  "test_ids": [
    "e7f8a9b0-c1d2-3456-9012-678901234567",
    "f8a9b0c1-d2e3-4567-0123-890123456789"
  ]
}
```

**Response `201`:**

```json
{
  "data": {
    "id": "a9b0c1d2-e3f4-5678-1234-901234567890",
    "order_number": "LAB-2026-00056",
    "patient_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "status": "ordered",
    "priority": "routine",
    "order_date": "2026-06-17T10:30:00Z",
    "items": [
      {
        "id": "b0c1d2e3-f4a5-6789-2345-012345678901",
        "test_id": "e7f8a9b0-c1d2-3456-9012-678901234567",
        "test_name": "Complete Blood Count",
        "price": 350.00,
        "status": "ordered"
      }
    ]
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `patient_id` | Required |
| `test_ids` | Min 1; all tests must be active |
| `priority` | Enum: `routine`, `urgent`, `stat` |

**Authorization roles:** Doctor, Hospital Admin.

---

### 10.4 POST `/laboratory/samples/{sample_id}/collect`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `laboratory:update` |

**Request:**

```json
{
  "collected_at": "2026-06-17T11:00:00Z",
  "notes": "Sample collected from left arm"
}
```

**Response `200`:** Sample with `status: collected`, `sample_id` barcode generated.

**Authorization roles:** Lab Technician.

---

### 10.5 POST `/laboratory/results`

Enter test results.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `laboratory:update` |

**Request:**

```json
{
  "lab_order_item_id": "b0c1d2e3-f4a5-6789-2345-012345678901",
  "sample_id": "c1d2e3f4-a5b6-7890-3456-123456789012",
  "results": [
    {
      "parameter_name": "Hemoglobin",
      "result_value": "14.2",
      "unit": "g/dL",
      "reference_range": "12.0-16.0",
      "is_abnormal": false,
      "is_critical": false
    },
    {
      "parameter_name": "WBC",
      "result_value": "18.5",
      "unit": "10³/µL",
      "reference_range": "4.0-11.0",
      "is_abnormal": true,
      "is_critical": true
    }
  ]
}
```

**Response `201`:** Result records; critical values trigger doctor notification.

**Validation:** `lab_order_item_id` must be in `sample_collected` or `processing` status.

**Authorization roles:** Lab Technician.

---

### 10.6 POST `/laboratory/reports/{order_id}/generate`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `lab:report` |

**Request:**

```json
{
  "finalize": true,
  "signatories": [
    {
      "staff_id": "lab-tech-staff-uuid",
      "designation": "Lab Technician"
    }
  ]
}
```

**Response `201`:**

```json
{
  "data": {
    "id": "d2e3f4a5-b6c7-8901-4567-234567890123",
    "report_number": "RPT-2026-00034",
    "order_id": "a9b0c1d2-e3f4-5678-1234-901234567890",
    "status": "finalized",
    "file_url": "https://signed-url-to-pdf...",
    "finalized_at": "2026-06-17T12:00:00Z"
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Authorization roles:** Lab Technician.

---

## 11. Module: Staff

**Base path:** `/api/v1/staff`  
**Tag:** `Staff`

### 11.1 Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | GET | `/staff` | `admin:users` |
| 2 | POST | `/staff` | `admin:users` |
| 3 | GET | `/staff/{staff_id}` | `admin:users` |
| 4 | PUT | `/staff/{staff_id}` | `admin:users` |
| 5 | DELETE | `/staff/{staff_id}` | `admin:users` |
| 6 | GET | `/staff/departments` | `admin:users` |
| 7 | POST | `/staff/departments` | `admin:settings` |
| 8 | POST | `/staff/users/invite` | `admin:users` |
| 9 | GET | `/staff/users` | `admin:users` |
| 10 | PATCH | `/staff/users/{user_id}` | `admin:users` |
| 11 | POST | `/staff/users/{user_id}/deactivate` | `admin:users` |

---

### 11.2 GET `/staff`

List employees.

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **Authorization** | `admin:users` |

**Query:** `department_id`, `status`, `search`, `location_id`, `page`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "employee_code": "EMP-0042",
      "first_name": "Vikram",
      "last_name": "Patel",
      "email": "vikram@apollo.com",
      "phone": "9876543210",
      "department_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "department_name": "General Medicine",
      "designation": "Senior Consultant",
      "status": "active",
      "joining_date": "2020-01-15",
      "is_doctor": true,
      "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  ],
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "...", "pagination": { } },
  "errors": null
}
```

---

### 11.3 POST `/staff`

Create employee record.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `admin:users` |

**Request:**

```json
{
  "employee_code": "EMP-0043",
  "first_name": "Sunita",
  "last_name": "Nair",
  "email": "sunita@apollo.com",
  "phone": "9876543220",
  "department_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "designation": "Billing Executive",
  "joining_date": "2026-06-01",
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123"
}
```

**Response `201`:** Staff object with `id`.

**Validation:**

| Field | Rules |
|-------|-------|
| `employee_code` | Required, unique per tenant |
| `first_name`, `last_name` | Required |
| `joining_date` | Required, valid date |
| `email` | Optional, valid format |

**Authorization roles:** Hospital Admin, Hospital Owner.

---

### 11.4 POST `/staff/users/invite`

Invite user account linked to staff.

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `admin:users` |

**Request:**

```json
{
  "email": "sunita@apollo.com",
  "first_name": "Sunita",
  "last_name": "Nair",
  "role_codes": ["accountant"],
  "staff_id": "new-staff-uuid",
  "department_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response `201`:**

```json
{
  "data": {
    "user_id": "new-user-uuid",
    "email": "sunita@apollo.com",
    "status": "inactive",
    "invite_sent": true,
    "roles": ["accountant"]
  },
  "meta": { "request_id": "...", "timestamp": "...", "tenant_id": "..." },
  "errors": null
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| `email` | Required, unique per tenant |
| `role_codes` | Min 1; valid role codes |
| Plan limit | Max users per subscription enforced |

**Errors:** `402` if user seat limit exceeded.

**Authorization roles:** Hospital Admin, Hospital Owner.

---

### 11.5 PATCH `/staff/users/{user_id}`

Update user roles or status.

| Attribute | Value |
|-----------|-------|
| **Method** | `PATCH` |
| **Authorization** | `admin:users` |

**Request:**

```json
{
  "role_codes": ["accountant", "receptionist"],
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123"
}
```

**Validation:** Cannot remove last `hospital_owner`; cannot deactivate self.

**Side effect:** Permission cache invalidated for user.

---

### 11.6 POST `/staff/users/{user_id}/deactivate`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `admin:users` |

**Request:**

```json
{
  "reason": "Employee resigned"
}
```

**Response `200`:** User `status: inactive`; all sessions revoked.

---

### 11.7 POST `/staff/departments`

| Attribute | Value |
|-----------|-------|
| **Method** | `POST` |
| **Authorization** | `admin:settings` |

**Request:**

```json
{
  "name": "Radiology",
  "code": "RAD",
  "head_staff_id": null,
  "location_id": "d4e5f6a7-b8c9-0123-def0-234567890123"
}
```

**Validation:** `code` unique per tenant; 2–20 chars uppercase alphanumeric.

---

## 12. FastAPI Implementation Reference

### 12.1 Router Registration

```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1 import auth, patients, doctors, appointments, billing, pharmacy, inventory, laboratory, staff

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(pharmacy.router, prefix="/pharmacy", tags=["Pharmacy"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(laboratory.router, prefix="/laboratory", tags=["Laboratory"])
api_router.include_router(staff.router, prefix="/staff", tags=["Staff"])
```

### 12.2 Dependency Injection

```python
from fastapi import Depends, HTTPException
from app.core.security import get_current_user, requires

@router.get("", response_model=APIResponse[list[PatientListItem]])
@requires("patient:read")
async def list_patients(
    request: Request,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    patients, total = await patient_service.list(
        tenant_id=current_user.tenant_id,
        search=search,
        page=page,
        page_size=page_size,
        db=db,
    )
    return paginated_response(patients, page, page_size, total, current_user.tenant_id)
```

### 12.3 OpenAPI Documentation

| URL | Description |
|-----|-------------|
| `/api/v1/docs` | Swagger UI (staging/dev only) |
| `/api/v1/redoc` | ReDoc (staging/dev only) |
| `/api/v1/openapi.json` | OpenAPI 3.1 schema |

Production: API docs disabled; schema available to internal CI for contract testing.

---

## 13. API Endpoint Index

| Module | Endpoints | Base Path |
|--------|-----------|-----------|
| Authentication | 8 | `/api/v1/auth` |
| Patients | 10 | `/api/v1/patients` |
| Doctors | 7 | `/api/v1/doctors` |
| Appointments | 7 | `/api/v1/appointments` |
| Billing | 12 | `/api/v1/billing` |
| Pharmacy | 8 | `/api/v1/pharmacy` |
| Inventory | 9 | `/api/v1/inventory` |
| Laboratory | 12 | `/api/v1/laboratory` |
| Staff | 11 | `/api/v1/staff` |
| **Total** | **84** | — |

---

## 14. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Senior API Architecture | Initial API design document |
