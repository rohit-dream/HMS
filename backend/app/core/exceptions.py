"""Domain exceptions — mapped to HTTP responses in exception_handlers."""


class AppError(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "app_error",
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.field = field


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", field: str | None = None) -> None:
        super().__init__(message, code="not_found", field=field)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", field: str | None = None) -> None:
        super().__init__(message, code="forbidden", field=field)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", field: str | None = None) -> None:
        super().__init__(message, code="unauthorized", field=field)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", field: str | None = None) -> None:
        super().__init__(message, code="conflict", field=field)


class ValidationError(AppError):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message, code="validation_error", field=field)


class PlanLimitError(AppError):
    def __init__(
        self,
        message: str = "Plan limit exceeded",
        *,
        resource: str | None = None,
        field: str | None = None,
    ) -> None:
        code = f"plan_limit_{resource}" if resource else "plan_limit_exceeded"
        super().__init__(message, code=code, field=field or resource)


class AccountLockedError(AppError):
    def __init__(self, message: str = "Account is locked", field: str | None = None) -> None:
        super().__init__(message, code="account_locked", field=field)


class TenantSuspendedError(AppError):
    def __init__(self, message: str = "Tenant is suspended", field: str | None = None) -> None:
        super().__init__(message, code="tenant_suspended", field=field)


class RateLimitExceededError(AppError):
    def __init__(self, message: str = "Too many requests", field: str | None = None) -> None:
        super().__init__(message, code="rate_limit_exceeded", field=field)


class FeatureNotImplementedError(AppError):
    def __init__(self, message: str = "Not implemented", field: str | None = None) -> None:
        super().__init__(message, code="not_implemented", field=field)
