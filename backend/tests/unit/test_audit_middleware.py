"""Unit tests — mutation audit middleware helpers (MVP-054)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.core.audit_middleware import (
    extract_entity_id_from_response,
    method_to_audit_action,
    resolve_audit_resource,
    should_record_mutation_audit,
    should_skip_audit_path,
)
from app.domains.audit.constants import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE


def test_method_to_audit_action_maps_http_verbs() -> None:
    assert method_to_audit_action("POST") == ACTION_CREATE
    assert method_to_audit_action("patch") == ACTION_UPDATE
    assert method_to_audit_action("DELETE") == ACTION_DELETE


def test_should_skip_audit_path_for_auth_and_health() -> None:
    prefix = "/api/v1"
    assert should_skip_audit_path("/api/v1/auth/login", prefix) is True
    assert should_skip_audit_path("/api/v1/auth/logout", prefix) is True
    assert should_skip_audit_path("/api/v1/health", prefix) is True
    assert should_skip_audit_path("/api/v1/hospital/profile", prefix) is False


def test_resolve_audit_resource_extracts_entity_type_and_id() -> None:
    entity_id = uuid.uuid4()
    entity_type, parsed_id = resolve_audit_resource(
        f"/api/v1/hospital/locations/{entity_id}",
        "/api/v1",
    )
    assert entity_type == "locations"
    assert parsed_id == entity_id

    profile_type, profile_id = resolve_audit_resource("/api/v1/hospital/profile", "/api/v1")
    assert profile_type == "profile"
    assert profile_id is None


def test_extract_entity_id_from_response_reads_envelope_data_id() -> None:
    entity_id = uuid.uuid4()
    body = f'{{"data": {{"id": "{entity_id}"}}, "meta": {{}}}}'.encode()
    assert extract_entity_id_from_response(body) == entity_id
    assert extract_entity_id_from_response(b"not-json") is None


def test_should_record_mutation_audit_requires_success_and_tenant() -> None:
    request = MagicMock()
    request.method = "PATCH"
    request.url.path = "/api/v1/hospital/profile"
    request.state.tenant_id = str(uuid.uuid4())

    assert (
        should_record_mutation_audit(
            request=request,
            status_code=200,
            api_prefix="/api/v1",
        )
        is True
    )

    assert (
        should_record_mutation_audit(
            request=request,
            status_code=403,
            api_prefix="/api/v1",
        )
        is False
    )

    request.state.tenant_id = None
    assert (
        should_record_mutation_audit(
            request=request,
            status_code=200,
            api_prefix="/api/v1",
        )
        is False
    )


def test_method_to_audit_action_rejects_get() -> None:
    with pytest.raises(ValueError, match="Unsupported mutation method"):
        method_to_audit_action("GET")
