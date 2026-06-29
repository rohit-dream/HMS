# Composite FK Migration Checklist

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Active (MVP-055) |
| **Applies to** | All Alembic revisions in `backend/alembic/versions/` |
| **Source of truth** | `DATABASE_DESIGN.md` § composite FKs, `database/baseline/schema.sql` |

---

## Rule

Every child-to-parent link **within a tenant** must use a composite foreign key:

```sql
FOREIGN KEY (tenant_id, child_id)
    REFERENCES parent_schema.parent_table (tenant_id, id)
```

This prevents cross-tenant reference attacks (e.g. linking an Apollo user to a City Hospital role).

**Only exception:** the tenant root column:

```sql
tenant_id UUID NOT NULL REFERENCES platform.tenants(id)
```

---

## Pre-migration checklist

Before opening a PR with new tables or FKs:

- [ ] Parent table has `UNIQUE (tenant_id, id)` (or `uq_<table>_tenant_id_id` index)
- [ ] Child table includes `tenant_id UUID NOT NULL REFERENCES platform.tenants(id)`
- [ ] Cross-table FKs use `(tenant_id, <fk_column>)` on both sides
- [ ] RLS policies added for new tenant-scoped tables (`app/db/rls_policies.py`)
- [ ] `downgrade()` drops constraints/tables in reverse order
- [ ] Composite FK lint passes locally

---

## DDL order (per revision)

| Step | Action |
|------|--------|
| 1 | `CREATE TABLE` with `tenant_id` root FK only |
| 2 | `CREATE UNIQUE INDEX uq_<table>_tenant_id_id ON schema.table (tenant_id, id)` |
| 3 | `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY (tenant_id, fk_col) REFERENCES ...` |
| 4 | Enable RLS + tenant isolation policies |

**Do not** use inline `REFERENCES other_table(id)` for tenant-scoped parents. Declare the column without FK, then add the composite constraint via `ALTER TABLE`.

---

## Good vs bad examples

### Good — tenant root

```sql
tenant_id UUID NOT NULL REFERENCES platform.tenants(id)
```

### Good — composite user FK

```sql
ALTER TABLE core.user_sessions
    ADD CONSTRAINT fk_user_sessions_user
    FOREIGN KEY (tenant_id, user_id)
    REFERENCES core.users (tenant_id, id) ON DELETE CASCADE;
```

### Bad — single-column FK (cross-tenant risk)

```sql
plan_id UUID NOT NULL REFERENCES platform.subscription_plans(id)
```

### Good — composite plan FK

```sql
plan_id UUID NOT NULL,
-- ...
ALTER TABLE platform.tenant_subscriptions
    ADD CONSTRAINT fk_tsub_plan
    FOREIGN KEY (tenant_id, plan_id)
    REFERENCES platform.subscription_plans (tenant_id, id);
```

---

## Lint command

From `backend/`:

```bash
python scripts/lint_composite_fks.py
```

Scans:

- `database/baseline/schema.sql`
- `backend/alembic/versions/*.py`

CI runs this on every push/PR.

---

## Reviewer checklist

- [ ] No new `REFERENCES ... (id)` unless target is `platform.tenants`
- [ ] Parent `UNIQUE (tenant_id, id)` exists before composite FK
- [ ] Integration test covers tenant isolation for new table (when applicable)
- [ ] `lint_composite_fks.py` passes
