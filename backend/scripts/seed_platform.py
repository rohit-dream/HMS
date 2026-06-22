#!/usr/bin/env python3
"""Seed system tenant subscription plan catalog (idempotent)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import session_scope
from app.domains.platform.services.plan_provisioner import PlanProvisioner


def main() -> int:
    with session_scope() as db:
        provisioner = PlanProvisioner(db)
        tenant_id = provisioner.seed_platform_catalog()
        count = provisioner.count_active_plans(tenant_id)
    print(f"Platform catalog ready — system tenant {tenant_id}, {count} plan(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
