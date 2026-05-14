from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class FieldError(BaseModel):
    field: str
    message: str


class ErrorDetail(BaseModel):
    code: str
    status_code: int
    details: dict = Field(default_factory=dict)
    field_errors: list[FieldError] = Field(default_factory=list)
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T
    meta: dict = Field(default_factory=dict)


class PaginatedMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: list[T]
    meta: PaginatedMeta
