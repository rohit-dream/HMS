"""Seed a development tenant and admin user for auth testing."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from sqlalchemy import select  # noqa: E402

from app.core.database import session_scope  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.domains.identity.services.rbac_service import RbacProvisioner  # noqa: E402
from app.domains.platform.constants import DEFAULT_TENANT_SETTINGS, PRIMARY_LOCATION_CODE, PRIMARY_LOCATION_NAME  # noqa: E402
from app.domains.platform.repositories.location_repository import LocationRepository  # noqa: E402
from app.domains.platform.repositories.setting_repository import SettingRepository  # noqa: E402
from app.models.core.user import User  # noqa: E402
from app.models.platform.tenant import Tenant  # noqa: E402


def _provision_hospital_resources(db, tenant_id: uuid.UUID) -> None:
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


def seed() -> None:
    with session_scope() as db:
        provisioner = RbacProvisioner(db)
        provisioner.seed_system_rbac()

        existing = db.scalars(select(Tenant).where(Tenant.slug == "apollo-dev")).first()
        if existing:
            provisioner.provision_tenant_rbac(existing.id)
            _provision_hospital_resources(db, existing.id)
            user = db.scalars(
                select(User).where(
                    User.tenant_id == existing.id,
                    User.email == "admin@apollo-dev.com",
                    User.deleted_at.is_(None),
                )
            ).first()
            if user:
                provisioner.assign_role(existing.id, user.id, "hospital_admin")
            db.commit()
            print(f"Dev tenant already exists: {existing.slug} ({existing.id})")
            print("  RBAC provisioned and hospital_admin role assigned")
            return

        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            tenant_id=tenant_id,
            name="Apollo Dev Clinic",
            slug="apollo-dev",
            subdomain="apollo-dev",
            status="active",
            email="admin@apollo-dev.com",
        )
        db.add(tenant)
        db.flush()

        provisioner.provision_tenant_rbac(tenant_id)
        _provision_hospital_resources(db, tenant_id)

        user = User(
            tenant_id=tenant_id,
            email="admin@apollo-dev.com",
            password_hash=hash_password("SecurePass@123"),
            first_name="Dev",
            last_name="Admin",
            status="active",
        )
        db.add(user)
        db.flush()
        provisioner.assign_role(tenant_id, user.id, "hospital_admin")
        db.commit()
        print("Seeded dev tenant and user:")
        print("  Tenant slug: apollo-dev  (header: X-Tenant-Slug: apollo-dev)")
        print("  Email:       admin@apollo-dev.com")
        print("  Password:    SecurePass@123")
        print("  Role:        hospital_admin")


if __name__ == "__main__":
    seed()
