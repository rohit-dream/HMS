"""Shared RBAC test helpers."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.domains.identity.services.rbac_service import RbacProvisioner
from app.domains.platform.constants import DEFAULT_TENANT_SETTINGS, PRIMARY_LOCATION_CODE, PRIMARY_LOCATION_NAME
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.setting_repository import SettingRepository
from app.models.core.user import User
from app.models.platform.tenant import Tenant


def provision_tenant_with_role(
    db: Session,
    *,
    slug: str,
    email: str,
    password_hash: str,
    role_code: str = "hospital_admin",
) -> dict:
    """Create tenant, user, RBAC templates, and assign role."""
    provisioner = RbacProvisioner(db)
    provisioner.seed_system_rbac()

    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        tenant_id=tenant_id,
        name=f"Test {slug}",
        slug=slug,
        subdomain=slug,
        status="active",
        email=email,
    )
    db.add(tenant)
    db.flush()

    provisioner.provision_tenant_rbac(tenant_id)

    user = User(
        tenant_id=tenant_id,
        email=email,
        password_hash=password_hash,
        first_name="Test",
        last_name="User",
        status="active",
    )
    db.add(user)
    db.flush()
    provisioner.assign_role(tenant_id, user.id, role_code)

    location_repo = LocationRepository(db, tenant_id)
    if location_repo.get_primary() is None:
        location_repo.create(
            name=PRIMARY_LOCATION_NAME,
            code=PRIMARY_LOCATION_CODE,
            is_primary=True,
            is_active=True,
        )
    setting_repo = SettingRepository(db, tenant_id)
    setting_repo.seed_defaults(DEFAULT_TENANT_SETTINGS)

    db.commit()

    return {"slug": slug, "email": email, "tenant_id": tenant_id, "user_id": user.id, "role": role_code}
