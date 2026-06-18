# Database Migrations

Runtime schema changes are managed by **Alembic** in `backend/alembic/versions/`.

The `database/` folder holds reference SQL: baseline DDL, RLS policies, seeds, and indexes. Update these when making major releases; day-to-day changes flow through Alembic migrations only.
