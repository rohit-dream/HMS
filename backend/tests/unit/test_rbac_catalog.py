"""Unit tests — MVP-037 permission catalog definitions."""

from __future__ import annotations

from app.core.rbac.catalog import (
    PERMISSION_CATALOG,
    ROLE_CATALOG,
    ROLE_PERMISSION_MAP,
    TENANT_ROLE_CODES,
)


def _catalog_codes() -> set[str]:
    return {code for code, _name, _module in PERMISSION_CATALOG}


def test_catalog_includes_sprint4_permissions() -> None:
    codes = _catalog_codes()
    assert "opd:queue" in codes
    assert "admin:staff" in codes


def test_catalog_codes_are_unique() -> None:
    codes = [code for code, _name, _module in PERMISSION_CATALOG]
    assert len(codes) == len(set(codes))


def test_role_permission_map_references_known_permissions() -> None:
    catalog = _catalog_codes()
    for role_code, perm_codes in ROLE_PERMISSION_MAP.items():
        assert role_code in {code for code, _, _ in ROLE_CATALOG}, role_code
        for perm in perm_codes:
            assert perm in catalog, f"{role_code} references unknown permission {perm}"


def test_receptionist_has_opd_queue() -> None:
    assert "opd:queue" in ROLE_PERMISSION_MAP["receptionist"]


def test_hospital_admin_has_admin_staff_and_opd_queue() -> None:
    perms = ROLE_PERMISSION_MAP["hospital_admin"]
    assert "admin:staff" in perms
    assert "opd:queue" in perms


def test_tenant_roles_exclude_platform_admin() -> None:
    assert "platform_admin" not in TENANT_ROLE_CODES
    assert "hospital_admin" in TENANT_ROLE_CODES
