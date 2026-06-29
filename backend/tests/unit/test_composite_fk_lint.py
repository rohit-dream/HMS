"""Unit tests — composite FK lint (MVP-055)."""

from __future__ import annotations

from pathlib import Path

from app.db.composite_fk_lint import (
    default_lint_targets,
    extract_foreign_keys,
    lint_paths,
    lint_sql_text,
    validate_foreign_key,
)


def test_validate_tenant_root_fk_is_allowed() -> None:
    fk = extract_foreign_keys(
        "tenant_id UUID NOT NULL REFERENCES platform.tenants(id)",
        "example.sql",
    )[0]
    assert validate_foreign_key(fk) == []


def test_validate_composite_user_fk_is_allowed() -> None:
    sql = """
    ALTER TABLE core.user_roles
        ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (tenant_id, user_id)
        REFERENCES core.users (tenant_id, id) ON DELETE CASCADE
    """
    fk = extract_foreign_keys(sql, "example.sql")[0]
    assert validate_foreign_key(fk) == []


def test_validate_single_column_plan_fk_is_rejected() -> None:
    sql = "plan_id UUID NOT NULL REFERENCES platform.subscription_plans(id)"
    fk = extract_foreign_keys(sql, "bad.sql")[0]
    errors = validate_foreign_key(fk)
    assert any("tenant_id" in err for err in errors)


def test_validate_user_id_only_fk_is_rejected() -> None:
    sql = """
    ALTER TABLE audit.audit_logs
        ADD CONSTRAINT fk_bad FOREIGN KEY (user_id)
        REFERENCES core.users (id)
    """
    fk = extract_foreign_keys(sql, "bad.sql")[0]
    errors = validate_foreign_key(fk)
    assert len(errors) >= 2


def test_lint_repo_defaults_pass() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    violations = lint_paths(default_lint_targets(repo_root))
    assert violations == [], violations


def test_lint_sql_text_reports_violation_line() -> None:
    violations = lint_sql_text(
        "plan_id UUID NOT NULL REFERENCES platform.subscription_plans(id)",
        "snippet.sql",
    )
    assert len(violations) >= 1
    assert violations[0].line == 1
