"""Unit tests for permission resolution and wildcard matching."""

from __future__ import annotations

from app.core.permissions import has_all_permissions, has_any_permission, has_permission


def test_has_permission_exact_match() -> None:
    assert has_permission(["patient:read", "billing:create"], "patient:read")


def test_has_permission_module_wildcard() -> None:
    assert has_permission(["billing:*"], "billing:void")
    assert not has_permission(["billing:*"], "patient:read")


def test_has_permission_global_wildcard() -> None:
    assert has_permission(["*:*"], "admin:users")
    assert has_permission(["*:*"], "anything:action")


def test_has_any_permission() -> None:
    perms = ["patient:read"]
    assert has_any_permission(perms, ["billing:void", "patient:read"])
    assert not has_any_permission(perms, ["billing:void", "admin:users"])


def test_has_all_permissions() -> None:
    perms = ["patient:read", "patient:create", "billing:*"]
    assert has_all_permissions(perms, ["patient:read", "billing:void"])
    assert not has_all_permissions(perms, ["patient:read", "admin:users"])
