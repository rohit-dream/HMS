# Database Migrations

Runtime schema changes are managed by **Alembic** in `backend/alembic/versions/`.

## Strategy

| Layer | Purpose |
|-------|---------|
| `backend/alembic/versions/` | **Authoritative** runtime migrations (append-only) |
| `database/baseline/schema.sql` | Reference DDL snapshot (61 tables) — not applied directly |
| `database/rls/`, `database/seeds/` | Reference policies and seed data |

## Rules

1. **Never edit** a migration that has been applied in any shared environment.
2. **Append** new revisions for every schema change.
3. **001_database_foundation** — extensions (`pgcrypto`), 8 schemas, shared functions only.
4. **002+** — business tables per `DATABASE_IMPLEMENTATION_PLAN.md`.
5. ORM models in `app/models/` must be imported in `app/models/__init__.py` for Alembic autogenerate.

## Commands

```bash
cd backend
alembic upgrade head
alembic current
alembic revision -m "description"   # manual or autogenerate
alembic downgrade -1
```

## Foundation revision (001)

Creates:

- `CREATE EXTENSION pgcrypto`
- Schemas: `platform`, `core`, `clinical`, `billing`, `pharmacy`, `laboratory`, `comms`, `audit`
- `public.set_updated_at()` — trigger function for `updated_at`
- `platform.enforce_tenant_self_reference()` — tenants self-reference guard

No business tables in foundation revision.
