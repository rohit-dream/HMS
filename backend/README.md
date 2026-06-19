# Backend

FastAPI modular monolith + SQS worker.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env.local
uvicorn app.main:app --reload --port 8000
```

## Validate structure

```bash
python -m scripts.validate_structure
python -m scripts.scaffold_dirs   # create missing domain folders if needed
```

## Layout

- `app/api/v1/` — HTTP routers (thin layer)
- `app/core/` — Config, logging, middleware, response envelope
- `app/core/tenant/` — Multi-tenant context (stubs until Sprint 2)
- `app/domains/` — Business logic by domain module (folders only)
- `app/models/` — SQLAlchemy ORM (database setup phase)
- `app/adapters/` — External integrations
- `worker/` — Async job handlers (Sprint 4+)
- `alembic/` — Database migrations (database setup phase)
- `tests/` — Unit and integration tests

See [docs/PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) §3.
