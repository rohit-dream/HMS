"""Tenant data access — re-exports platform repository for identity domain."""

from app.domains.platform.repositories.tenant_repository import TenantRepository

__all__ = ["TenantRepository"]
