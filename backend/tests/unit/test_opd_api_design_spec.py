"""MVP-051 — API_DESIGN_OPD.md completeness checks."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
OPD_SPEC_PATH = REPO_ROOT / "docs" / "API_DESIGN_OPD.md"

REQUIRED_SECTIONS = (
    "## 1. Introduction",
    "## 3. RBAC & Authorization",
    "## 5. Status Machines",
    "## 6. Endpoint Summary",
    "## 12. OPD Error Catalog",
    "## 13. Multi-Tenant & RLS",
    "## 15. Pydantic Schema Reference",
)

REQUIRED_PERMISSIONS = (
    "opd:read",
    "opd:create",
    "opd:update",
    "opd:queue",
    "opd:consult",
    "opd:prescribe",
)

ENDPOINT_ROW_PATTERN = re.compile(
    r"^\|\s*\d+\s*\|\s*(GET|POST|PATCH|PUT|DELETE)\s*\|\s*`(/opd/[^`]+)`\s*\|\s*`([^`]+)`",
    re.MULTILINE,
)


@pytest.fixture
def opd_spec_text() -> str:
    assert OPD_SPEC_PATH.is_file(), f"Missing spec: {OPD_SPEC_PATH}"
    return OPD_SPEC_PATH.read_text(encoding="utf-8")


def test_opd_spec_file_exists() -> None:
    assert OPD_SPEC_PATH.is_file()


def test_opd_spec_marked_complete(opd_spec_text: str) -> None:
    assert "Complete (Sprint 5 — MVP-051)" in opd_spec_text
    assert "To be completed in Sprint 5" not in opd_spec_text


def test_opd_spec_has_required_sections(opd_spec_text: str) -> None:
    for section in REQUIRED_SECTIONS:
        assert section in opd_spec_text, f"Missing section: {section}"


def test_opd_spec_documents_minimum_endpoints(opd_spec_text: str) -> None:
    """Sprint 5 DoD: ≥15 OPD endpoints documented."""
    endpoints = ENDPOINT_ROW_PATTERN.findall(opd_spec_text)
    assert len(endpoints) >= 15, f"Expected ≥15 endpoints, found {len(endpoints)}"


def test_opd_spec_endpoint_permissions_are_valid(opd_spec_text: str) -> None:
    endpoints = ENDPOINT_ROW_PATTERN.findall(opd_spec_text)
    permissions = {perm for _, _, perm in endpoints}
    for perm in REQUIRED_PERMISSIONS:
        assert perm in permissions, f"Permission not used in endpoint table: {perm}"


def test_opd_spec_covers_core_workflow_paths(opd_spec_text: str) -> None:
    required_paths = (
        "/opd/visits",
        "/opd/visits/{visit_id}/start",
        "/opd/visits/{visit_id}/complete",
        "/opd/queue",
        "/opd/visits/{visit_id}/vitals",
        "/opd/visits/{visit_id}/notes",
        "/opd/visits/{visit_id}/prescriptions",
    )
    for path in required_paths:
        assert path in opd_spec_text, f"Missing endpoint path: {path}"


def test_opd_spec_documents_visit_status_machine(opd_spec_text: str) -> None:
    for status in ("waiting", "in_consultation", "completed", "cancelled"):
        assert status in opd_spec_text


def test_opd_spec_documents_rls_and_composite_fk(opd_spec_text: str) -> None:
    assert "clinical.opd_visits" in opd_spec_text
    assert "tenant_id" in opd_spec_text
    assert "Composite FK" in opd_spec_text or "composite FK" in opd_spec_text.lower()
