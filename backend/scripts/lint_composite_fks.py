#!/usr/bin/env python3
"""Lint Alembic migrations and baseline schema for composite FK compliance (MVP-055)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

sys.path.insert(0, str(BACKEND_ROOT))

from app.db.composite_fk_lint import default_lint_targets, format_violations, lint_paths


def main() -> int:
    violations = lint_paths(default_lint_targets(REPO_ROOT))
    print(format_violations(violations))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
