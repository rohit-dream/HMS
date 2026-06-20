# Database

PostgreSQL SQL artifacts for the Hospital Management SaaS platform.

## Layout

| Folder | Purpose |
|--------|---------|
| `baseline/` | Full bootstrap DDL (`schema.sql`) |
| `schemas/` | Per-schema SQL extracts |
| `rls/` | Row-Level Security policies |
| `functions/` | Stored procedures and triggers |
| `indexes/` | Performance index definitions |
| `seeds/` | Ordered seed scripts for dev/staging |
| `partitions/` | Table partitioning (scale) |

Runtime schema changes go through **Alembic** in `backend/alembic/`. See `migrations-readme.md`.

See [docs/PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) §5.
