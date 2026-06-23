#!/usr/bin/env python3
"""Run MVP-032 auth integration and API E2E verification."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

AUTH_E2E_CHECKS: tuple[tuple[str, list[str]], ...] = (
    (
        "Auth API E2E workflow (MVP-032)",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_auth_e2e.py",
            "-v",
            "--tb=short",
        ],
    ),
    (
        "Auth endpoint integration regression",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/api/v1/test_auth.py",
            "-q",
        ],
    ),
    (
        "Auth security + rate limit unit tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/test_security.py",
            "tests/unit/test_rate_limit.py",
            "tests/unit/test_captcha.py",
            "-q",
        ],
    ),
)


def _run_step(title: str, command: list[str]) -> bool:
    print(f"\n=== {title} ===")
    result = subprocess.run(command, cwd=BACKEND_ROOT, check=False)
    ok = result.returncode == 0
    print(f"{'PASS' if ok else 'FAIL'}: {title}")
    return ok


def main() -> int:
    print("MVP-032 — Auth Integration + E2E Verification")
    print(f"Repository: {REPO_ROOT}")

    results = [_run_step(title, command) for title, command in AUTH_E2E_CHECKS]
    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 50}")
    if all(results):
        print(f"MVP-032: PASSED ({passed}/{total} check groups)")
        return 0

    print(f"MVP-032: FAILED ({passed}/{total} check groups passed)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
