# OPD API Design (MVP)

## Outpatient Module — REST Contract

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | **To be completed in Sprint 5** |
| **Base Path** | `/api/v1/opd` |
| **Implements** | FR-OPD-001 through FR-OPD-013 (P0 subset) |
| **Related** | `API_DESIGN.md` §6 Appointments, `DATABASE_DESIGN.md` §3.4 |

---

## 1. Scope (MVP)

| In Scope | Out of Scope (Post-MVP) |
|----------|-------------------------|
| OPD visits (walk-in + appointment) | IPD admissions |
| Token queue per doctor | WebSocket real-time queue |
| Vitals recording | ICD-10 coded diagnosis |
| Clinical notes | Lab orders from consult |
| E-prescription | Referral notifications |
| Visit complete → billing hook | Printable visit summary PDF |

---

## 2. Endpoint Summary

| # | Method | Endpoint | Permission |
|---|--------|----------|------------|
| 1 | POST | `/opd/visits` | `opd:create` |
| 2 | GET | `/opd/visits` | `opd:read` |
| 3 | GET | `/opd/visits/{visit_id}` | `opd:read` |
| 4 | PATCH | `/opd/visits/{visit_id}` | `opd:update` |
| 5 | POST | `/opd/visits/{visit_id}/start` | `opd:consult` |
| 6 | POST | `/opd/visits/{visit_id}/complete` | `opd:consult` |
| 7 | GET | `/opd/queue` | `opd:queue` |
| 8 | POST | `/opd/queue` | `opd:queue` |
| 9 | POST | `/opd/queue/{queue_id}/call` | `opd:queue` |
| 10 | POST | `/opd/queue/{queue_id}/complete` | `opd:queue` |
| 11 | POST | `/opd/visits/{visit_id}/vitals` | `opd:consult` |
| 12 | GET | `/opd/visits/{visit_id}/vitals` | `opd:read` |
| 13 | POST | `/opd/visits/{visit_id}/notes` | `opd:consult` |
| 14 | GET | `/opd/visits/{visit_id}/notes` | `opd:read` |
| 15 | POST | `/opd/visits/{visit_id}/prescriptions` | `opd:prescribe` |
| 16 | GET | `/opd/visits/{visit_id}/prescriptions` | `opd:read` |

---

## 3. Visit Status Machine

```
scheduled → waiting → in_consultation → completed
                    → cancelled
```

---

## 4. Queue Polling (MVP)

`GET /opd/queue?doctor_id={uuid}&date={date}` — clients poll every 5 seconds.

Post-MVP: WebSocket channel `opd:queue:{doctor_id}:{date}`.

---

## 5. Sprint Assignment

| Sprint | Action |
|--------|--------|
| **S5** | Complete request/response schemas, error codes, OpenAPI stubs |
| **S9** | Full implementation |

---

> **Sprint 5 deliverable:** Expand each endpoint with full JSON schemas, validation rules, and examples matching `API_DESIGN.md` conventions.
