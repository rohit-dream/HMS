"""Integration tests — MVP-013 platform.create_tenant()."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.database import session_scope, set_rls_tenant_context


@pytest.mark.integration
def test_create_tenant_returns_id_equal_to_tenant_id() -> None:
    slug = f"ct-{uuid.uuid4().hex[:10]}"
    with session_scope() as db:
        tenant_id = db.execute(
            text(
                """
                SELECT platform.create_tenant(
                    :name, :slug, :email, :slug
                )
                """
            ),
            {
                "name": "Create Tenant Hospital",
                "slug": slug,
                "email": f"owner@{slug}.com",
            },
        ).scalar_one()

        set_rls_tenant_context(db, tenant_id)
        row = db.execute(
            text(
                """
                SELECT id, tenant_id, status
                FROM platform.tenants
                WHERE id = :id
                """
            ),
            {"id": tenant_id},
        ).one()
        assert row.id == row.tenant_id == tenant_id
        assert row.status == "trial"


@pytest.mark.integration
def test_create_tenant_normalizes_slug_and_email() -> None:
    raw_slug = f"CT-{uuid.uuid4().hex[:8]}"
    expected_slug = raw_slug.lower()
    with session_scope() as db:
        tenant_id = db.execute(
            text(
                """
                SELECT platform.create_tenant(
                    :name, :slug, :email, :slug
                )
                """
            ),
            {
                "name": "Normalize Test",
                "slug": raw_slug,
                "email": f"  OWNER@{expected_slug}.COM  ",
            },
        ).scalar_one()

        set_rls_tenant_context(db, tenant_id)
        row = db.execute(
            text("SELECT slug, email, subdomain FROM platform.tenants WHERE id = :id"),
            {"id": tenant_id},
        ).one()
        assert row.slug == expected_slug
        assert row.subdomain == expected_slug
        assert row.email == f"owner@{expected_slug}.com"


@pytest.mark.integration
def test_create_tenant_rejects_duplicate_slug() -> None:
    slug = f"dup-{uuid.uuid4().hex[:8]}"
    with session_scope() as db:
        db.execute(
            text(
                """
                SELECT platform.create_tenant(
                    :name, :slug, :email, :slug
                )
                """
            ),
            {"name": "First", "slug": slug, "email": f"a@{slug}.com"},
        )

        with pytest.raises(DBAPIError) as exc_info:
            db.execute(
                text(
                    """
                    SELECT platform.create_tenant(
                        :name, :slug, :email, :slug
                    )
                    """
                ),
                {"name": "Second", "slug": slug, "email": f"b@{slug}.com"},
            )
        assert "slug already exists" in str(exc_info.value).lower()


@pytest.mark.integration
def test_create_tenant_rejects_reserved_slug() -> None:
    with session_scope() as db:
        with pytest.raises(DBAPIError) as exc_info:
            db.execute(
                text(
                    """
                    SELECT platform.create_tenant(
                        'Reserved', 'admin', 'admin@example.com', 'admin'
                    )
                    """
                )
            )
        assert "reserved" in str(exc_info.value).lower()


@pytest.mark.integration
def test_create_tenant_rejects_invalid_slug() -> None:
    with session_scope() as db:
        with pytest.raises(DBAPIError) as exc_info:
            db.execute(
                text(
                    """
                    SELECT platform.create_tenant(
                        'Bad Slug', 'bad_slug!', 'bad@example.com', 'bad_slug!'
                    )
                    """
                )
            )
        assert "invalid tenant slug" in str(exc_info.value).lower()
