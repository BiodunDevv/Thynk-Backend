from fastapi import HTTPException, status

from app.core.error_codes import ErrorCodes


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = ErrorCodes.INTERNAL_SERVER_ERROR,
        details: dict | None = None,
        field_errors: list[dict] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.field_errors = field_errors or []


class NotFoundException(AppException):
    def __init__(self, message: str, error_code: str = ErrorCodes.RESOURCE_NOT_FOUND) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, message, error_code)
