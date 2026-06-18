# Folder Structure Freeze — Enforcement Rules

| Field | Value |
|-------|-------|
| **Version** | 1.1 |
| **Status** | **Frozen** |
| **Effective Date** | 2026-06-18 |
| **Canonical Structure** | [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) v2.0 |

---

## Purpose

This document is the **short, enforceable checklist** for all code generation and refactors. The full tree, naming conventions, and folder explanations live in **PROJECT_STRUCTURE.md**. When in doubt, read PROJECT_STRUCTURE.md first.

---

## Mandatory Rules (Before Generating Code)

1. **Follow PROJECT_STRUCTURE.md** — Place every file in the path defined there. Do not invent parallel layouts.
2. **Follow this document** — Structural changes require the approvals listed below.
3. **No new top-level folders** — Allowed roots only: `backend/`, `frontend/`, `database/`, `infrastructure/`, `docs/`, `.github/`, plus root config files (`docker-compose.yml`, `README.md`, etc.).
4. **No moving files between modules** — A file stays in its domain/module. Cross-domain logic uses services, adapters, or shared `core/` — not folder moves.
5. **Module-based architecture** — Backend: `api/v1/` (thin) → `domains/<domain>/` (logic). Frontend: `features/<domain>/` mirrors backend domains. One feature spans both sides in the same domain name.
6. **Multi-tenant design** — Every tenant-scoped table and query includes `tenant_id`. Use `core/tenant/`, RLS (`database/rls/`), and `TenantScopedRepository`. See [MULTI_TENANT_DESIGN.md](./MULTI_TENANT_DESIGN.md) and [SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md).
7. **RBAC design** — Permissions and roles from [RBAC_DESIGN.md](./RBAC_DESIGN.md). Enforce at API (`dependencies.py`), service layer, and UI route guards. Do not invent ad-hoc role names.

---

## Structural Change Policy

| Action | Allowed? |
|--------|----------|
| Add files inside existing folders | Yes — match naming in PROJECT_STRUCTURE.md |
| Add a new domain (backend + frontend mirror) | Yes — copy existing domain pattern |
| Rename, move, or delete top-level folders | **No** — Principal Architect approval + doc update |
| Move a file to a different domain/module | **No** — refactor in place or extract shared code to `core/` |
| New top-level directory | **No** — architecture review + update PROJECT_STRUCTURE.md and this file |

---

## Domain Modules (Fixed Set)

Backend `domains/` and frontend `features/` use the same domain names:

| Domain | Scope |
|--------|--------|
| `platform` | SaaS operator: tenants, subscriptions, onboarding |
| `identity` | Auth, users, RBAC, sessions |
| `patients` | Patient registry, demographics |
| `staff` | Staff profiles, departments |
| `clinical` | OPD, IPD, appointments |
| `billing` | Hospital billing (invoices, payments) |
| `laboratory` | Lab orders, results |
| `pharmacy` | Prescriptions, inventory |
| `communications` | SMS, email, notifications |
| `reporting` | Dashboards, exports |
| `audit` | Audit logs, compliance |

New business areas must map to an existing domain or follow the “add new domain” pattern in PROJECT_STRUCTURE.md §1.1.

---

## Related Documents (Precedence)

| Topic | Document |
|-------|----------|
| Folder tree & conventions | PROJECT_STRUCTURE.md |
| Tenant isolation | MULTI_TENANT_DESIGN.md |
| Roles & permissions | RBAC_DESIGN.md |
| Security controls | SECURITY_ARCHITECTURE.md |
| Implementation order | IMPLEMENTATION_PLAN.md |

**Conflict resolution:** SECURITY_ARCHITECTURE.md → RBAC_DESIGN.md → DATABASE_DESIGN.md → API_DESIGN.md

---

## AI / Developer Checklist

Before opening a PR or generating code, confirm:

- [ ] File path exists in PROJECT_STRUCTURE.md (or is a new file inside an allowed folder)
- [ ] No new top-level folder created
- [ ] Feature code lives in the correct `domains/` / `features/` module
- [ ] `tenant_id` handled for all tenant-scoped data
- [ ] RBAC checks use roles/permissions from RBAC_DESIGN.md
- [ ] Tests mirror domain structure under `backend/tests/`

---

*End of FOLDER_STRUCTURE_FREEZE.md*
