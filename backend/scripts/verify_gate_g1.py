#!/usr/bin/env python3
"""Run Gate G1 (Sprint 2 foundation) verification and print a pass/fail report."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

G1_CHECKS: tuple[tuple[str, list[str]], ...] = (
    (
        "Gate G1 automated checklist",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_gate_g1.py",
            "-v",
            "--tb=short",
        ],
    ),
    (
        "CF-01 cross-tenant isolation regression",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_tenant_isolation.py",
            "-q",
        ],
    ),
    (
        "Full backend test suite",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
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
    print("Gate G1 — Sprint 2 Foundation Verification")
    print(f"Repository: {REPO_ROOT}")
    print("Expected Alembic head: 013_email_verification_tokens")

    infra_ok = (REPO_ROOT / "docker-compose.yml").is_file() and (
        REPO_ROOT / ".github" / "workflows" / "ci.yml"
    ).is_file()
    print(f"\nDocker Compose present: {'yes' if (REPO_ROOT / 'docker-compose.yml').is_file() else 'no'}")
    print(f"CI workflow present: {'yes' if (REPO_ROOT / '.github/workflows/ci.yml').is_file() else 'no'}")

    results = [infra_ok]
    for title, command in G1_CHECKS:
        results.append(_run_step(title, command))

    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 50}")
    if all(results):
        print(f"GATE G1: PASSED ({passed}/{total} check groups)")
        print("Sprint 2 foundation is complete — safe to proceed to Sprint 3 feature work.")
        return 0

    print(f"GATE G1: FAILED ({passed}/{total} check groups passed)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
