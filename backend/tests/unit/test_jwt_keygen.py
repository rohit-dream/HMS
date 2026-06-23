"""Unit tests for JWT key generation utilities (MVP-035)."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import Settings
from app.core.jwt_keygen import ensure_jwt_keys, verify_jwt_key_pair, write_jwt_key_pair
from app.core.security import clear_key_cache, create_access_token, decode_access_token


def test_write_jwt_key_pair_creates_pem_files(tmp_path: Path) -> None:
    private_path, public_path, created = write_jwt_key_pair(tmp_path)
    assert created is True
    assert private_path.exists()
    assert public_path.exists()
    assert b"BEGIN PRIVATE KEY" in private_path.read_bytes()
    assert b"BEGIN PUBLIC KEY" in public_path.read_bytes()


def test_write_jwt_key_pair_skips_existing_without_force(tmp_path: Path) -> None:
    first_private, first_public, created = write_jwt_key_pair(tmp_path)
    assert created is True

    second_private, second_public, created_again = write_jwt_key_pair(tmp_path)
    assert created_again is False
    assert second_private == first_private
    assert second_public == first_public
    assert first_private.read_bytes() == second_private.read_bytes()


def test_write_jwt_key_pair_force_regenerates(tmp_path: Path) -> None:
    first_private, _, _ = write_jwt_key_pair(tmp_path)
    first_bytes = first_private.read_bytes()

    second_private, _, created = write_jwt_key_pair(tmp_path, force=True)
    assert created is True
    assert second_private.read_bytes() != first_bytes


def test_verify_jwt_key_pair_accepts_generated_keys(tmp_path: Path) -> None:
    private_path, public_path, _ = write_jwt_key_pair(tmp_path)
    verify_jwt_key_pair(private_path, public_path, issuer="https://auth.test.local")


def test_generated_keys_work_with_security_module(tmp_path: Path) -> None:
    private_path, public_path, _ = write_jwt_key_pair(tmp_path)
    clear_key_cache()
    settings = Settings(
        environment="test",
        database_url="postgresql://hms:hms@localhost:5432/hms_test",
        jwt_private_key_path=str(private_path),
        jwt_public_key_path=str(public_path),
        jwt_issuer="https://auth.test.local",
    )

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    token, jti, _expires_in = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=["hospital_admin"],
        settings=settings,
    )
    claims = decode_access_token(token, settings)
    assert claims.sub == user_id
    assert claims.tenant_id == tenant_id
    assert claims.jti == jti


def test_ensure_jwt_keys_is_idempotent(tmp_path: Path) -> None:
    first = ensure_jwt_keys(tmp_path)
    second = ensure_jwt_keys(tmp_path)
    assert first == second
