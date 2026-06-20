"""Generate RS256 JWT key pair for local development."""

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main() -> None:
    keys_dir = Path(__file__).resolve().parents[1] / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)

    private_path = keys_dir / "private.pem"
    public_path = keys_dir / "public.pem"

    if private_path.exists() and public_path.exists():
        print("JWT keys already exist — skipping.")
        return

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

    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    print(f"Generated {private_path}")
    print(f"Generated {public_path}")


if __name__ == "__main__":
    main()
