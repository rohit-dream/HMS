"""Validate monorepo folder structure against PROJECT_STRUCTURE.md."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    # Monorepo root
    "backend",
    "frontend",
    "database",
    "database/baseline",
    "docs",
    "infrastructure",
    ".github/workflows",
    "docker-compose.yml",
    ".gitignore",
    ".editorconfig",
    # Backend app
    "backend/app",
    "backend/app/api/v1",
    "backend/app/core",
    "backend/app/core/tenant",
    "backend/app/domains",
    "backend/app/models",
    "backend/app/repositories",
    "backend/app/adapters",
    "backend/app/main.py",
    "backend/requirements.txt",
    "backend/pyproject.toml",
    "backend/.env.example",
    "backend/keys",
    "backend/tests",
    "backend/scripts",
    # Domain modules (folders only at foundation)
    "backend/app/domains/platform",
    "backend/app/domains/platform/services",
    "backend/app/domains/platform/repositories",
    "backend/app/domains/platform/schemas",
    "backend/app/domains/identity",
    "backend/app/domains/identity/services",
    "backend/app/domains/identity/repositories",
    "backend/app/domains/identity/schemas",
    "backend/app/domains/patients",
    "backend/app/domains/clinical",
    "backend/app/domains/billing",
    "backend/app/domains/staff",
    "backend/app/domains/laboratory",
    "backend/app/domains/pharmacy",
    "backend/app/domains/communications",
    "backend/app/domains/reporting",
    "backend/app/domains/audit",
    # Frontend foundation
    "frontend/src",
    "frontend/src/api",
    "frontend/src/components/layout",
    "frontend/src/providers",
    "frontend/src/routes",
    "frontend/src/lib",
    "frontend/src/styles",
    "frontend/package.json",
    "frontend/.env.example",
]


def validate() -> list[str]:
    """Return list of missing required paths."""
    missing: list[str] = []
    for relative in REQUIRED_PATHS:
        path = REPO_ROOT / relative
        if not path.exists():
            missing.append(relative)
    return missing


def main() -> int:
    missing = validate()
    if missing:
        print("PROJECT_STRUCTURE validation FAILED — missing paths:")
        for item in missing:
            print(f"  - {item}")
        return 1
    print("PROJECT_STRUCTURE validation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
