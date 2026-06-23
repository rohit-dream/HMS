"""RS256 JWT key pair generation utilities (MVP-035)."""

from __future__ import annotations

import os
import stat
import uuid
from pathlib import Path

import jwt

from app.core.constants import JWT_ALGORITHM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

DEFAULT_KEY_SIZE = 2048
DEFAULT_KEYS_DIR = Path(__file__).resolve().parents[2] / "keys"
PRIVATE_KEY_NAME = "private.pem"
PUBLIC_KEY_NAME = "public.pem"


def generate_rsa_key_pair(*, key_size: int = DEFAULT_KEY_SIZE) -> tuple[bytes, bytes]:
    """Return (private_pem, public_pem) for a new RSA key pair."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def _restrict_private_key_permissions(path: Path) -> None:
    if os.name != "posix":
        return
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def write_jwt_key_pair(
    keys_dir: Path | None = None,
    *,
    force: bool = False,
    key_size: int = DEFAULT_KEY_SIZE,
) -> tuple[Path, Path, bool]:
    """
    Write JWT PEM files when missing, or when force=True.

    Returns (private_path, public_path, created).
    """
    target_dir = keys_dir or DEFAULT_KEYS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    private_path = target_dir / PRIVATE_KEY_NAME
    public_path = target_dir / PUBLIC_KEY_NAME

    if private_path.exists() and public_path.exists() and not force:
        return private_path, public_path, False

    private_pem, public_pem = generate_rsa_key_pair(key_size=key_size)
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    _restrict_private_key_permissions(private_path)
    return private_path, public_path, True


def verify_jwt_key_pair(private_path: Path, public_path: Path, *, issuer: str) -> None:
    """Raise jwt.PyJWTError if the key pair cannot sign and verify RS256 tokens."""
    private_key = private_path.read_text(encoding="utf-8")
    public_key = public_path.read_text(encoding="utf-8")
    payload = {
        "iss": issuer,
        "sub": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "roles": [],
        "iat": 1,
        "exp": 9_999_999_999,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, private_key, algorithm=JWT_ALGORITHM)
    jwt.decode(token, public_key, algorithms=[JWT_ALGORITHM], issuer=issuer)


def ensure_jwt_keys(keys_dir: Path | None = None) -> tuple[Path, Path]:
    """Create keys when absent; used by local dev bootstrap and tests."""
    private_path, public_path, _created = write_jwt_key_pair(keys_dir, force=False)
    return private_path, public_path
