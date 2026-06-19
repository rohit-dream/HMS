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
    def __init__(self, message: str = "Plan limit exceeded", field: str | None = None) -> None:
        super().__init__(message, code="plan_limit_exceeded", field=field)
