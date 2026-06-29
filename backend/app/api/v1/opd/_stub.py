"""Raise 501 for OPD endpoints pending Sprint 9 implementation."""

from app.core.exceptions import FeatureNotImplementedError


def opd_not_implemented(feature: str) -> None:
    raise FeatureNotImplementedError(f"{feature} is planned for Sprint 9 (OPD vertical slice)")
