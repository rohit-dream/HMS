"""Seed system tenant RBAC catalog and provision tenant templates."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.database import session_scope  # noqa: E402
from app.domains.identity.services.rbac_service import RbacProvisioner  # noqa: E402


def seed() -> None:
    with session_scope() as db:
        provisioner = RbacProvisioner(db)
        provisioner.seed_system_rbac()
        db.commit()
        print("Seeded system tenant RBAC:")
        print("  Permissions: full catalog")
        print("  Roles: platform_admin + all tenant roles")


if __name__ == "__main__":
    seed()
