#!/usr/bin/env python3
"""Generate RS256 JWT key pair for local development (MVP-035)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.jwt_keygen import (  # noqa: E402
    DEFAULT_KEYS_DIR,
    verify_jwt_key_pair,
    write_jwt_key_pair,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate RS256 JWT key pair PEM files for local HMS development.",
    )
    parser.add_argument(
        "--keys-dir",
        type=Path,
        default=DEFAULT_KEYS_DIR,
        help=f"Output directory (default: {DEFAULT_KEYS_DIR})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing private.pem and public.pem",
    )
    parser.add_argument(
        "--key-size",
        type=int,
        default=2048,
        help="RSA key size in bits (default: 2048)",
    )
    parser.add_argument(
        "--issuer",
        default="https://auth.platform.com",
        help="Issuer used for post-generation sign/verify smoke check",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.key_size < 2048:
        print("ERROR: --key-size must be at least 2048 bits.", file=sys.stderr)
        return 1

    private_path, public_path, created = write_jwt_key_pair(
        args.keys_dir,
        force=args.force,
        key_size=args.key_size,
    )

    try:
        verify_jwt_key_pair(private_path, public_path, issuer=args.issuer)
    except Exception as exc:  # noqa: BLE001 — CLI smoke check
        print(f"ERROR: generated keys failed verification: {exc}", file=sys.stderr)
        return 1

    if created:
        print(f"Generated {private_path}")
        print(f"Generated {public_path}")
    else:
        print("JWT keys already exist — skipping (use --force to regenerate).")
        print(f"Private key: {private_path}")
        print(f"Public key:  {public_path}")

    print("\nAdd to backend/.env (if not already set):")
    print(f"JWT_PRIVATE_KEY_PATH={private_path.resolve().as_posix()}")
    print(f"JWT_PUBLIC_KEY_PATH={public_path.resolve().as_posix()}")
    print("\nProduction: store keys in AWS Secrets Manager — never commit *.pem files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
