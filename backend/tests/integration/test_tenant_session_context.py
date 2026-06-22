"""Integration tests — MVP-014 TenantScopedRepository + session RLS binding."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.core.database import (
    get_session_factory,
    session_scope,
    set_rls_tenant_context,
    use_rls_enforced_role,
)
from app.core.tenant.context import (
    get_effective_tenant_id,
    set_request_tenant_id,
    tenant_db_session,
)
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.tenant_repository import TenantRepository
from app.repositories.base import TenantScopedRepository


@pytest.mark.integration
def test_tenant_scoped_repository_sets_rls_on_init() -> None:
    """Constructing a repository must bind app.tenant_id on the session."""
    slug = f"repo-rls-{uuid.uuid4().hex[:8]}"

    with session_scope() as db:
        tenant_id = TenantRepository(db).create_via_db_function(
            slug=slug,
            name="RLS Repo Test",
            email=f"{slug}@example.com",
        )
        db.commit()

        use_rls_enforced_role(db)
        LocationRepository(db, tenant_id)
        setting = db.execute(
            text("SELECT current_setting('app.tenant_id', true)")
        ).scalar_one()
        assert setting == str(tenant_id)


@pytest.mark.integration
def test_get_db_applies_request_tenant_context() -> None:
    """get_effective_tenant_id drives RLS when opening a session via get_db pattern."""
    from app.core.tenant.context import clear_auth_context

    tenant_id = uuid.uuid4()
    set_request_tenant_id(tenant_id)

    session_factory = get_session_factory()
    db = session_factory()
    try:
        effective = get_effective_tenant_id()
        assert effective == tenant_id
        set_rls_tenant_context(db, effective)
        use_rls_enforced_role(db)
        setting = db.execute(
            text("SELECT current_setting('app.tenant_id', true)")
        ).scalar_one()
        assert setting == str(tenant_id)
    finally:
        db.close()
        clear_auth_context()


@pytest.mark.integration
def test_tenant_db_session_context_manager() -> None:
    """tenant_db_session scopes RLS for the block and clears afterward."""
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    with session_scope() as db:
        use_rls_enforced_role(db)
        with tenant_db_session(db, tenant_a):
            assert (
                db.execute(text("SELECT current_setting('app.tenant_id', true)")).scalar_one()
                == str(tenant_a)
            )
        with tenant_db_session(db, tenant_b):
            assert (
                db.execute(text("SELECT current_setting('app.tenant_id', true)")).scalar_one()
                == str(tenant_b)
            )
        cleared = db.execute(text("SELECT current_setting('app.tenant_id', true)")).scalar_one()
        assert cleared in ("", None)


@pytest.mark.integration
def test_location_repository_rls_isolation() -> None:
    """Repository queries under hms_app must not return other tenants' locations."""
    slug_a = f"loc-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"loc-b-{uuid.uuid4().hex[:8]}"
    location_a_id = uuid.uuid4()

    with session_scope() as db:
        tenant_repo = TenantRepository(db)
        tenant_a_id = tenant_repo.create_via_db_function(
            slug=slug_a,
            name="Hospital A",
            email=f"{slug_a}@example.com",
        )
        tenant_b_id = tenant_repo.create_via_db_function(
            slug=slug_b,
            name="Hospital B",
            email=f"{slug_b}@example.com",
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, tenant_a_id)
        db.execute(
            text(
                """
                INSERT INTO platform.tenant_locations (
                    id, tenant_id, name, code, is_primary, is_active
                ) VALUES (
                    :id, :tenant_id, 'Branch A', 'A1', TRUE, TRUE
                )
                """
            ),
            {"id": location_a_id, "tenant_id": tenant_a_id},
        )
        db.commit()

        repo_a = LocationRepository(db, tenant_a_id)
        locations = repo_a.list_active()
        assert len(locations) == 1
        assert locations[0].id == location_a_id

        repo_b = LocationRepository(db, tenant_b_id)
        assert repo_b.get_by_id(location_a_id) is None


@pytest.mark.integration
def test_repository_assert_tenant_blocks_cross_tenant_entity() -> None:
    """add() must reject entities stamped with a different tenant_id."""
    from app.core.exceptions import ForbiddenError
    from app.models.platform.tenant_location import TenantLocation

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    with session_scope() as db:
        repo = TenantScopedRepository(db, tenant_a)
        foreign = TenantLocation(
            tenant_id=tenant_b,
            name="Foreign",
            code="FOR",
            is_primary=False,
        )
        with pytest.raises(ForbiddenError):
            repo.add(foreign)
