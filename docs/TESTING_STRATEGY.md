# Testing Strategy

## Multi-Tenant Hospital Management SaaS — MVP

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Active |
| **Companion** | `SDLC Planning/09_MVP_SPRINT_PLAN_V2.md`, `10_MVP_TASK_BACKLOG.md` |
| **Last Updated** | June 2026 |
| **Owner** | Engineering |

---

## 1. Purpose

This document defines how the Hospital Management SaaS MVP is tested at every layer. Every sprint closes only when its test deliverables pass locally and in CI. Tenant isolation tests are **mandatory on every CI run** once RLS is introduced in Sprint 2.

### 1.1 Goals

| Goal | Rationale |
|------|-----------|
| Prevent cross-tenant data leaks | Multi-tenant SaaS failure mode is catastrophic |
| Catch regressions before merge | Solo developer cannot afford production firefighting |
| Enforce API contract stability | Frontend and integrations depend on envelope + status codes |
| Measure coverage on business logic | Billing, auth, and patient flows carry legal and financial risk |
| Gate production launch | Sprint 12 security and load tests block Gate G5 |

### 1.2 Scope

| In scope (MVP) | Out of scope (post-MVP) |
|----------------|-------------------------|
| Unit, integration, API, E2E tests | Mobile app testing |
| Tenant isolation + RLS verification | HL7/FHIR interoperability tests |
| CI on every push/PR | Third-party penetration test firm engagement |
| Load test on staging (S12) | Chaos engineering |
| Bandit SAST + OWASP ZAP (S12) | Continuous performance benchmarking |

---

## 2. Testing Pyramid

The pyramid balances speed (bottom) with confidence (top). Most tests are fast unit and integration tests; fewer E2E tests cover critical hospital workflows.

```mermaid
flowchart TB
    subgraph Pyramid["Test Pyramid"]
        E2E["End-to-End Tests<br/>5–7 critical journeys<br/>Playwright / API workflows"]
        API["API Tests<br/>Every shipped endpoint<br/>FastAPI TestClient"]
        INT["Integration Tests<br/>DB + Redis + migrations<br/>Tenant isolation"]
        UNIT["Unit Tests<br/>Services, validators, RBAC<br/>Fastest feedback"]
    end

    UNIT --> INT
    INT --> API
    API --> E2E
```

### 2.1 Layer Summary

| Layer | What it validates | Tooling | When it runs |
|-------|-------------------|---------|--------------|
| **Unit Tests** | Pure logic: validators, MRN generation, billing math, permission helpers, envelope builders | pytest | Every commit; CI |
| **Integration Tests** | Database queries, Alembic migrations, repository + RLS, Redis rate limiting | pytest + PostgreSQL + Redis | Every commit; CI |
| **API Tests** | HTTP status codes, request/response schemas, auth guards, standard envelope `{ data, meta, errors }` | pytest + FastAPI `TestClient` | Every commit; CI |
| **End-to-End Tests** | Full user journeys across frontend + API (register → OPD → bill) | Playwright (S4+) or API-only workflow scripts | Gates G2, G3, G4, G5 |

### 2.2 Test Count Targets (MVP)

| Sprint | New test focus | Minimum new tests |
|--------|----------------|-------------------|
| S1 | Health, envelope, logging | 5+ |
| S2 | Platform register, RLS isolation | 10+ |
| S3 | Auth flow, lockout, cross-tenant login | 15+ |
| S4 | RBAC 403, user CRUD, register E2E | 20+ |
| S5 | OpenAPI contract snapshot | 5+ |
| S6 | Org CRUD + isolation | 15+ |
| S7 | Patient CRUD, MRN, duplicate, search | 20+ |
| S8 | Appointments, 409 conflict | 15+ |
| S9 | OPD full workflow | 25+ |
| S10 | Invoice, payment, void audit | 20+ |
| S11 | Reports, file upload, notifications | 15+ |
| S12 | Razorpay webhook, 2FA, regression, load | 30+ |

---

## 3. Backend Testing

### 3.1 Pytest Setup

Backend tests live under `backend/tests/`. Configuration is in `backend/pyproject.toml`.

| Setting | Value |
|---------|-------|
| Test runner | pytest ≥ 8.3 |
| Coverage plugin | pytest-cov ≥ 6.0 |
| Linter | ruff ≥ 0.8 |
| Python | 3.11+ |
| Config file | `backend/pyproject.toml` → `[tool.pytest.ini_options]` |

**Install test dependencies:**

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

**Run all tests:**

```bash
cd backend
pytest tests/ -v
```

**Run with coverage report:**

```bash
cd backend
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

Coverage HTML output is written to `backend/htmlcov/index.html`.

**Run a single file or test:**

```bash
pytest tests/unit/test_security.py -v
pytest tests/integration/api/v1/test_health.py::test_liveness -v
```

### 3.2 Shared Fixtures (`conftest.py`)

`backend/tests/conftest.py` provides:

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `settings` | session | Loads `Settings` with test JWT RS256 keys generated under `backend/keys/` |
| `client` | module | FastAPI `TestClient` wrapping `create_app()` with `SKIP_STARTUP_CHECKS=true` |

Environment defaults set before app import:

```python
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SKIP_STARTUP_CHECKS", "true")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
```

For database-backed integration tests, set `DATABASE_URL` to a dedicated test database before running pytest. CI uses `postgresql://hms:hms@localhost:5432/hms_test`.

### 3.3 Async Testing

FastAPI route handlers and services use `async def`. Testing patterns:

| Pattern | Use when |
|---------|----------|
| `TestClient` (sync) | HTTP-level API tests — preferred for most integration tests |
| `pytest-asyncio` + `AsyncClient` | Direct async service/repository calls without HTTP |
| `anyio` backend | Already supported by Starlette test utilities |

**Example — async service test (Sprint 3+):**

```python
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_auth_service_refresh_rotates_token(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/refresh")
    assert response.status_code in (200, 401)
```

Add `pytest-asyncio` to `requirements-dev.txt` when the first pure-async service tests are introduced.

### 3.4 Database Testing

| Concern | Approach |
|---------|----------|
| Test database | Separate DB (`hms_test` in CI; `hms_dev` locally with caution) |
| Schema state | `alembic upgrade head` before integration suite |
| Transaction rollback | Use per-test transactions or truncate tenant-scoped tables in fixtures |
| Migrations | `tests/integration/test_alembic_foundation.py` verifies 001+ apply cleanly |
| RLS verification | `SET LOCAL app.tenant_id = '<uuid>'` in raw SQL tests; API tests use two tenant tokens |
| Seeds | Dev seeds (`scripts/seed_auth_dev.py`) for manual QA; tests create own fixtures |

**Pre-test migration (local):**

```bash
cd backend
export DATABASE_URL=postgresql://hms:hms@localhost:5432/hms_test   # bash
# PowerShell: $env:DATABASE_URL="postgresql://hms:hms@localhost:5432/hms_test"
alembic upgrade head
pytest tests/integration/ -v
```

**Tenant isolation pattern (mandatory from S2):**

```python
def test_tenant_b_cannot_read_tenant_a_patient(client, token_a, token_b, patient_a):
    response = client.get(
        f"/api/v1/patients/{patient_a.id}",
        headers={"Authorization": f"Bearer {token_b['access']}"},
    )
    assert response.status_code == 404  # not 403 — no resource enumeration
```

Plus a direct SQL test confirming RLS blocks `SELECT` when `app.tenant_id` differs.

### 3.5 Mocking External Services

External dependencies must never be called from CI. Mock or stub at the adapter boundary.

| Service | Adapter location | Mock strategy |
|---------|------------------|---------------|
| Email (SES) | `app/adapters/email/` | In-memory outbox; assert message queued |
| SMS | `app/adapters/sms/` | Stub returns success |
| S3 file storage | `app/adapters/storage/` | Local filesystem or `moto` (S12) |
| Razorpay | `app/adapters/payments/` | Webhook signature fixture + test payloads |
| Redis | Built-in | Real Redis in CI service container; `fakeredis` for pure unit tests |
| CAPTCHA | `app/adapters/captcha/` | `CAPTCHA_BYPASS=true` in test env only |

**Example — email adapter mock:**

```python
from unittest.mock import AsyncMock, patch

@patch("app.adapters.email.ses.send_email", new_callable=AsyncMock)
async def test_password_reset_sends_email(mock_send, client):
    mock_send.return_value = {"MessageId": "test-123"}
    response = client.post("/api/v1/auth/forgot-password", json={"email": "a@hospital.com"})
    assert response.status_code == 200
    mock_send.assert_called_once()
```

---

## 4. Frontend Testing

Frontend test tooling is introduced incrementally starting Sprint 3 (auth UI). Sprint 1 establishes the strategy and folder layout.

### 4.1 Vitest + React Testing Library

| Package | Version target | Purpose |
|---------|----------------|---------|
| `vitest` | 2.x | Test runner (Vite-native) |
| `@testing-library/react` | 16.x | Component rendering and queries |
| `@testing-library/user-event` | 14.x | Realistic user interactions |
| `@testing-library/jest-dom` | 6.x | DOM matchers (`toBeInTheDocument`) |
| `jsdom` | 25.x | Browser environment |
| `msw` | 2.x | Mock API responses for integration tests |

**Planned `frontend/package.json` scripts (Sprint 3):**

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

**Planned `frontend/vitest.config.ts`:**

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx", "src/test/**"],
    },
  },
});
```

### 4.2 Component Testing

Test components in isolation with providers wrapped as needed.

| Component type | Test focus |
|----------------|------------|
| Form inputs | Validation messages, disabled states, submit handlers |
| `PermissionGuard` | Renders children only when permission present |
| `AuthProvider` | Login/logout state transitions |
| Data tables | Empty state, loading skeleton, pagination |
| API hooks | Loading/error/success states with MSW |

**Example — login form (Sprint 3):**

```typescript
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "@/features/identity/components/LoginForm";

it("shows error when email is empty", async () => {
  render(<LoginForm onSubmit={vi.fn()} />);
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
  expect(screen.getByText(/email is required/i)).toBeInTheDocument();
});
```

### 4.3 Frontend Integration Testing

Integration tests verify feature modules with mocked API layer (MSW) or a running local backend.

| Scope | Tool | Location |
|-------|------|----------|
| Feature flow (login → dashboard) | Vitest + MSW | `frontend/src/features/identity/__tests__/` |
| Route guards | Vitest + MemoryRouter | `frontend/src/app/__tests__/` |
| React Query cache | Vitest + MSW | Per-feature `__tests__/` |

### 4.4 E2E Testing (Sprint 4+)

| Tool | Use |
|------|-----|
| Playwright | Browser E2E for Gates G2–G5 |
| Location | `frontend/e2e/` |

Critical journeys are listed in Section 8.

---

## 5. Coverage Requirements

Coverage is enforced per layer. Sprint 1 baseline is recorded; gates tighten through MVP.

### 5.1 Targets by Layer

| Layer | Coverage target | Measured on |
|-------|-----------------|-------------|
| **Services** (domain logic) | ≥ 90% | `backend/app/domains/**/services/` |
| **API routes** (integration) | ≥ 85% | All shipped endpoints exercised |
| **Critical business flows** | 100% | Auth, tenant isolation, billing payment, OPD consult close |
| **Repositories** | ≥ 80% | `backend/app/domains/**/repositories/` |
| **Frontend components** (Sprint 4+) | ≥ 70% | `frontend/src/features/**` |
| **Overall backend (MVP launch)** | ≥ 75% | `backend/app/` |

### 5.2 Critical Flows Requiring 100% Test Coverage

| Flow ID | Description | Gate |
|---------|-------------|------|
| CF-01 | Tenant A cannot read/write Tenant B data (API + RLS) | G1 |
| CF-02 | Login → refresh → logout → session invalidated | G2 |
| CF-03 | Permission denied returns 403 with envelope | G2 |
| CF-04 | Patient register → appointment → OPD visit → close | G3 |
| CF-05 | Invoice create → payment → receipt PDF | G4 |
| CF-06 | Razorpay webhook activates subscription | G5 |
| CF-07 | Owner 2FA required on production login | G5 |

### 5.3 Coverage Exclusions

| Path | Reason |
|------|--------|
| `app/main.py` bootstrap | Covered by integration smoke |
| Alembic migration files | Tested via `test_alembic_foundation` |
| Generated OpenAPI stubs | Replaced in implementation sprints |
| `scripts/` CLI utilities | Manual verification acceptable |

### 5.4 Recording Baseline (Sprint 1)

```bash
cd backend
pytest tests/ --cov=app --cov-report=term-missing
```

Record the overall percentage in the sprint retrospective. Each subsequent sprint must not decrease coverage on `app/`.

---

## 6. Test Folder Structure

### 6.1 Backend

```
backend/tests/
├── __init__.py
├── conftest.py                 # Shared fixtures: settings, client, DB, tokens
├── helpers/
│   ├── __init__.py
│   ├── factories.py            # Patient, tenant, user factories (S2+)
│   └── rbac.py                 # Permission test helpers
├── unit/
│   ├── test_security.py
│   ├── test_permissions.py
│   ├── test_models_base.py
│   ├── test_repository_base.py
│   ├── test_startup.py
│   └── test_tenant_schemas.py
├── integration/
│   ├── test_alembic_foundation.py
│   ├── test_tenant_isolation.py    # S2 — mandatory CI
│   └── api/
│       └── v1/
│           ├── test_health.py
│           ├── test_auth.py
│           ├── test_platform_hospital.py
│           ├── test_rbac.py
│           └── test_user_management.py
└── e2e/                            # S4+ API workflow scripts
    ├── test_register_to_dashboard.py
    └── test_opd_billing_flow.py
```

### 6.2 Frontend (from Sprint 3)

```
frontend/
├── src/
│   ├── test/
│   │   ├── setup.ts              # jest-dom, MSW server
│   │   └── utils.tsx             # renderWithProviders()
│   └── features/
│       └── identity/
│           ├── components/
│           └── __tests__/
│               └── LoginForm.test.tsx
└── e2e/                          # Playwright (S4+)
    ├── playwright.config.ts
    └── specs/
        └── auth.spec.ts
```

### 6.3 Naming Conventions

| Rule | Example |
|------|---------|
| Backend test files | `test_<subject>.py` |
| Frontend test files | `<Component>.test.tsx` |
| E2E specs | `<journey>.spec.ts` or `test_<journey>.py` |
| One assertion theme per test | `test_login_returns_401_for_wrong_password` |
| Fixtures in `conftest.py` | `token_hospital_a`, `db_session` |

---

## 7. CI Testing Workflow

CI is defined in `.github/workflows/ci.yml`. It runs on push to `main`, `dev`, `rohit/dev` and on pull requests to `main` and `dev`.

```mermaid
flowchart LR
    subgraph Trigger["Trigger"]
        PUSH["Push / PR"]
    end

    subgraph BackendJob["Job: backend"]
        B1["Checkout"]
        B2["Setup Python 3.11"]
        B3["pip install"]
        B4["ruff check"]
        B5["pytest tests/ -v"]
        B1 --> B2 --> B3 --> B4 --> B5
    end

    subgraph FrontendJob["Job: frontend"]
        F1["Checkout"]
        F2["Setup Node 20"]
        F3["npm ci"]
        F4["npm run lint"]
        F5["npm run typecheck"]
        F6["npm run build"]
        F1 --> F2 --> F3 --> F4 --> F5 --> F6
    end

    PUSH --> BackendJob
    PUSH --> FrontendJob
```

### 7.1 CI Steps — Backend

| Step | Command | Pass criteria |
|------|---------|---------------|
| Lint | `ruff check .` | Zero errors |
| Unit + integration tests | `pytest tests/ -v` | All pass |
| Services | PostgreSQL 14 + Redis 7 (GitHub Actions service containers) | Healthy before tests |

**CI environment variables:**

```yaml
ENVIRONMENT: test
DATABASE_URL: postgresql://hms:hms@localhost:5432/hms_test
REDIS_URL: redis://localhost:6379/0
```

### 7.2 CI Steps — Frontend

| Step | Command | Pass criteria |
|------|---------|---------------|
| Lint | `npm run lint` | Zero errors |
| Type check | `npm run typecheck` | Zero TS errors |
| Build | `npm run build` | Production bundle succeeds |

### 7.3 Planned CI Additions by Sprint

| Sprint | Addition |
|--------|----------|
| S2 | `tests/integration/test_tenant_isolation.py` required |
| S3 | `pytest --cov=app --cov-fail-under=70` |
| S4 | `npm run test` (Vitest) |
| S5 | OpenAPI schema diff check |
| S11 | `bandit -r app -ll` |
| S12 | OWASP ZAP baseline scan on staging; k6 load test (manual gate) |

### 7.4 Coverage Reports in CI (Sprint 3+)

```yaml
- name: Test with coverage
  run: pytest tests/ --cov=app --cov-report=xml --cov-fail-under=70

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: backend/coverage.xml
```

### 7.5 PR Merge Policy

| Rule | Enforcement |
|------|-------------|
| CI must be green | Branch protection on `main` |
| No open P0 bugs | Manual sprint gate |
| Tenant isolation test passes | Required from S2 |
| Coverage must not drop | `--cov-fail-under` from S3 |

---

## 8. E2E Critical Journeys

| ID | Journey | Gate | Primary tool |
|----|---------|------|--------------|
| E2E-01 | Register → verify email → login → dashboard | G2 | Playwright |
| E2E-02 | Invite user → accept invite → login as invited | G2 | Playwright |
| E2E-03 | Register patient → book appointment | G3 | API workflow |
| E2E-04 | Appointment → OPD queue → consult → e-Rx | G3 | API workflow |
| E2E-05 | Complete visit → invoice → pay → receipt PDF | G4 | API workflow |
| E2E-06 | Full hospital day workflow under 5 minutes | G5 | Playwright |
| E2E-07 | Trial → add payment method → Razorpay webhook → active | G5 | API + webhook fixture |

---

## 9. Test Environments

| Environment | Database | Redis | When used |
|-------------|----------|-------|-----------|
| **Local** | `hms_dev` via Docker Compose | Local container | Developer daily work |
| **CI** | `hms_test` ephemeral (GitHub Actions) | Service container | Every push/PR |
| **Staging** | RDS staging instance | ElastiCache | S12 UAT, load test |
| **Production** | RDS Multi-AZ | ElastiCache | Smoke test post-deploy only |

---

## 10. Bug Severity & Sprint Rules

| Severity | Definition | Sprint rule |
|----------|------------|-------------|
| **P0** | Data leak, auth bypass, payment miscalculation | Fix immediately; blocks sprint close |
| **P1** | Core workflow broken (cannot register patient, cannot bill) | Fix before sprint close |
| **P2** | UI defect, non-critical edge case | Backlog if not blocking |
| **P3** | Cosmetic | Backlog |

**A sprint cannot close with open P0 bugs.**

---

## 11. Definition of Test Done (Per Sprint)

- [ ] Every new API endpoint has at least one integration test (happy path + auth failure)
- [ ] Every new tenant-scoped resource has a cross-tenant isolation test
- [ ] New Alembic migrations verified by integration test
- [ ] No regression in existing test suite
- [ ] New service code meets layer coverage target (Section 5)
- [ ] Frontend components for the sprint have Vitest tests (from S4)
- [ ] CI pipeline green on the sprint branch

---

## 12. Future Testing Roadmap

These activities are scheduled in later MVP sprints. They are not optional for production launch.

### 12.1 Load Testing (Sprint 12)

| Tool | Scenario | Target |
|------|----------|--------|
| k6 or Locust | 50 concurrent users on staging | API P95 < 500ms |
| k6 | Patient search under 100k records | < 1s (NFR-PERF-006) |
| k6 | Morning OPD rush simulation | 200 concurrent platform users |

**Location:** `infrastructure/scripts/load-test/`  
**Gate:** G5 — load test report attached to release notes.

### 12.2 Security Testing (Sprint 11–12)

| Tool | Scope | Frequency |
|------|-------|-----------|
| Bandit | Python SAST — no high severity | Every PR (from S11) |
| OWASP ZAP | Baseline scan on staging | Pre-production (S12) |
| Manual OWASP Top 10 checklist | Auth, injection, IDOR, tenant isolation | S12 gate |
| Dependency audit | `pip-audit`, `npm audit` | Weekly CI job (S12) |

### 12.3 Performance Testing (Sprint 12)

| Test | Target | Tool |
|------|--------|------|
| API P50 latency | < 200ms | k6 + CloudWatch |
| API P95 latency | < 500ms | k6 + CloudWatch |
| PDF generation | < 5s | Integration timing assertion |
| Report generation | < 10s | Integration timing assertion |

### 12.4 Contract Testing (Sprint 5)

- OpenAPI schema snapshot in `backend/tests/snapshots/openapi.json`
- CI fails if undocumented breaking change detected

---

## 13. Running Tests — Quick Reference

```bash
# Start local infrastructure
docker compose up -d postgres redis

# Backend — full suite
cd backend && pytest tests/ -v

# Backend — with coverage
cd backend && pytest tests/ --cov=app --cov-report=term-missing

# Backend — lint
cd backend && ruff check .

# Frontend — typecheck + build (Sprint 1)
cd frontend && npm run typecheck && npm run build

# Frontend — unit tests (Sprint 3+)
cd frontend && npm run test

# E2E (Sprint 4+)
cd frontend && npx playwright test
```

---

## 14. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 2026 | Initial production strategy — MVP-010 Sprint 1 deliverable |
