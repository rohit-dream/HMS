"""Unit tests for password hashing and JWT utilities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest

from app.core.config import Settings
from app.core.constants import BCRYPT_ROUNDS, JWT_ALGORITHM
from app.core.security import (
    clear_key_cache,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


@pytest.fixture
def jwt_settings(tmp_path: Path) -> Settings:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_path = tmp_path / "private.pem"
    public_path = tmp_path / "public.pem"
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)

    clear_key_cache()
    return Settings(
        environment="test",
        database_url="postgresql://hms:hms@localhost:5432/hms_test",
        jwt_private_key_path=str(private_path),
        jwt_public_key_path=str(public_path),
        jwt_issuer="https://auth.test.local",
        jwt_access_token_expire_minutes=30,
    )


def test_hash_and_verify_password() -> None:
    hashed = hash_password("SecurePass@123")
    assert hashed != "SecurePass@123"
    assert hashed.startswith(f"$2b${BCRYPT_ROUNDS:02d}$")
    assert verify_password("SecurePass@123", hashed)
    assert not verify_password("wrong", hashed)


def test_generate_refresh_token_is_opaque_and_unique() -> None:
    a = generate_refresh_token()
    b = generate_refresh_token()
    assert len(a) >= 48
    assert a != b


def test_refresh_token_hash_is_deterministic() -> None:
    assert hash_refresh_token("abc") == hash_refresh_token("abc")
    assert hash_refresh_token("abc") != hash_refresh_token("def")


def test_create_and_decode_access_token(jwt_settings: Settings) -> None:
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    token, jti, expires_in = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=["doctor"],
        settings=jwt_settings,
    )
    assert expires_in == 1800
    header = jwt.get_unverified_header(token)
    assert header["alg"] == JWT_ALGORITHM

    claims = decode_access_token(token, jwt_settings)
    assert claims.sub == user_id
    assert claims.tenant_id == tenant_id
    assert claims.roles == ("doctor",)
    assert claims.jti == jti

    payload = jwt.decode(token, options={"verify_signature": False})
    assert "permissions" not in payload
    assert set(payload.keys()) >= {"iss", "sub", "tenant_id", "roles", "iat", "exp", "jti"}


def test_decode_rejects_tampered_token(jwt_settings: Settings) -> None:
    token, _, _ = create_access_token(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        settings=jwt_settings,
    )
    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}.invalid"
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered, jwt_settings)


def test_decode_rejects_wrong_issuer(jwt_settings: Settings) -> None:
    token, _, _ = create_access_token(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        settings=jwt_settings,
    )
    wrong_issuer = jwt_settings.model_copy(update={"jwt_issuer": "https://evil.example"})
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token, wrong_issuer)


def test_decode_rejects_expired_token(jwt_settings: Settings) -> None:
    private_key = Path(jwt_settings.jwt_private_key_path).read_text(encoding="utf-8")
    past = datetime.now(UTC) - timedelta(minutes=5)
    payload = {
        "iss": jwt_settings.jwt_issuer,
        "sub": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "roles": [],
        "iat": int(past.timestamp()),
        "exp": int((past + timedelta(seconds=1)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, private_key, algorithm=JWT_ALGORITHM)
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token, jwt_settings)
