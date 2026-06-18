# Backend

FastAPI modular monolith + SQS worker.

## Layout

- `app/api/v1/` — HTTP routers (thin layer)
- `app/core/` — Config, security, middleware, shared infrastructure
- `app/core/tenant/` — Multi-tenant context and plan limits
- `app/domains/` — Business logic by domain module
- `app/models/` — SQLAlchemy ORM (by PostgreSQL schema)
- `app/adapters/` — External integrations (S3, SQS, SES, Razorpay)
- `worker/` — Async job handlers and schedulers
- `alembic/` — Database migrations
- `tests/` — Unit and integration tests

See [docs/PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) §3.
