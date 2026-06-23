#!/usr/bin/env python3
"""Run Gate G2 (Sprint 4 platform admin) verification and print a pass/fail report."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

G2_CHECKS: tuple[tuple[str, list[str]], ...] = (
    (
        "Gate G2 platform E2E workflow (MVP-050)",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_gate_g2_e2e.py",
            "-v",
            "--tb=short",
        ],
    ),
    (
        "Hospital profile, branches, and settings API",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/api/v1/test_platform_hospital.py",
            "-q",
        ],
    ),
    (
        "User management + accept-invite API",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/api/v1/test_user_management.py",
            "tests/integration/api/v1/test_accept_invite.py",
            "-q",
        ],
    ),
    (
        "RBAC enforcement regression",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/api/v1/test_rbac.py",
            "-q",
        ],
    ),
    (
        "Registration legal acceptance + auth E2E smoke",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_register_legal_acceptance.py",
            "tests/integration/test_auth_e2e.py::test_e2e_register_login_me_logout",
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
    print("Gate G2 — Sprint 4 Platform Admin Verification (MVP-050)")
    print(f"Repository: {REPO_ROOT}")
    print("Expected scope: register → hospital admin → users → RBAC")

    results = [_run_step(title, command) for title, command in G2_CHECKS]
    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 50}")
    if all(results):
        print(f"GATE G2: PASSED ({passed}/{total} check groups)")
        print("Sprint 4 platform vertical slice is complete — safe to proceed to Sprint 5.")
        return 0

    print(f"GATE G2: FAILED ({passed}/{total} check groups passed)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
