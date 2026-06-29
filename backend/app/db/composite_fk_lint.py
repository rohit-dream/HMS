"""Lint composite foreign keys in Alembic migrations and baseline schema (MVP-055)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TENANTS_TABLE = "platform.tenants"

FK_PATTERN = re.compile(
    r"FOREIGN\s+KEY\s*\(\s*([^)]+?)\s*\)\s*REFERENCES\s+([\w.]+)\s*\(\s*([^)]+?)\s*\)",
    re.IGNORECASE | re.DOTALL,
)

INLINE_FK_PATTERN = re.compile(
    r"(\w+)\s+UUID(?:\s+NOT\s+NULL)?\s+REFERENCES\s+([\w.]+)\s*\(\s*([^)]+?)\s*\)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ForeignKeyRef:
    source: str
    line: int
    fk_columns: tuple[str, ...]
    ref_table: str
    ref_columns: tuple[str, ...]


@dataclass(frozen=True)
class LintViolation:
    source: str
    line: int
    message: str
    fk_columns: tuple[str, ...]
    ref_table: str
    ref_columns: tuple[str, ...]


def _split_columns(raw: str) -> tuple[str, ...]:
    return tuple(part.strip().lower() for part in raw.split(",") if part.strip())


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _normalize_table(table: str) -> str:
    return table.strip().lower()


def extract_foreign_keys(text: str, source: str) -> list[ForeignKeyRef]:
    refs: list[ForeignKeyRef] = []

    for match in FK_PATTERN.finditer(text):
        refs.append(
            ForeignKeyRef(
                source=source,
                line=_line_number(text, match.start()),
                fk_columns=_split_columns(match.group(1)),
                ref_table=_normalize_table(match.group(2)),
                ref_columns=_split_columns(match.group(3)),
            )
        )

    for match in INLINE_FK_PATTERN.finditer(text):
        refs.append(
            ForeignKeyRef(
                source=source,
                line=_line_number(text, match.start()),
                fk_columns=(match.group(1).strip().lower(),),
                ref_table=_normalize_table(match.group(2)),
                ref_columns=_split_columns(match.group(3)),
            )
        )

    return refs


def _is_tenant_root_fk(fk: ForeignKeyRef) -> bool:
    return (
        fk.fk_columns == ("tenant_id",)
        and fk.ref_table == TENANTS_TABLE
        and fk.ref_columns == ("id",)
    )


def validate_foreign_key(fk: ForeignKeyRef) -> list[str]:
    """Return human-readable violations for a single FK definition."""
    if _is_tenant_root_fk(fk):
        return []

    errors: list[str] = []

    if len(fk.fk_columns) != len(fk.ref_columns):
        errors.append("FK column count must match REFERENCES column count")

    if "tenant_id" not in fk.fk_columns:
        errors.append("FK must include tenant_id to prevent cross-tenant references")

    if fk.ref_table != TENANTS_TABLE:
        if "tenant_id" not in fk.ref_columns:
            errors.append("REFERENCES must use composite (tenant_id, <id>) on parent table")
        elif fk.ref_columns[0] != "tenant_id":
            errors.append("tenant_id must be the first referenced column")

    if len(fk.fk_columns) == 1 and fk.fk_columns[0] != "tenant_id":
        errors.append("Single-column FK is only allowed for tenant_id -> platform.tenants(id)")

    if fk.ref_table != TENANTS_TABLE and fk.ref_columns == ("id",):
        errors.append("REFERENCES (... id) without tenant_id is not allowed for tenant-scoped tables")

    return errors


def lint_sql_text(text: str, source: str) -> list[LintViolation]:
    violations: list[LintViolation] = []
    for fk in extract_foreign_keys(text, source):
        for message in validate_foreign_key(fk):
            violations.append(
                LintViolation(
                    source=fk.source,
                    line=fk.line,
                    message=message,
                    fk_columns=fk.fk_columns,
                    ref_table=fk.ref_table,
                    ref_columns=fk.ref_columns,
                )
            )
    return violations


def lint_paths(paths: list[Path]) -> list[LintViolation]:
    violations: list[LintViolation] = []
    for path in sorted(paths):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        violations.extend(lint_sql_text(text, str(path)))
    return violations


def default_lint_targets(repo_root: Path) -> list[Path]:
    backend = repo_root / "backend"
    migration_dir = backend / "alembic" / "versions"
    targets = [repo_root / "database" / "baseline" / "schema.sql"]
    targets.extend(sorted(migration_dir.glob("*.py")))
    return targets


def format_violations(violations: list[LintViolation]) -> str:
    if not violations:
        return "Composite FK lint PASSED"
    lines = ["Composite FK lint FAILED:"]
    for item in violations:
        cols = ", ".join(item.fk_columns)
        ref_cols = ", ".join(item.ref_columns)
        lines.append(
            f"  - {item.source}:{item.line} "
            f"({cols}) -> {item.ref_table}({ref_cols}): {item.message}"
        )
    return "\n".join(lines)
