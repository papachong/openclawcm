"""
Unified API response format.
"""
from typing import Any, Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class PageResponse(BaseModel):
    """Paginated response wrapper."""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None
    total: int = 0
    page: int = 1
    page_size: int = 20


def success(data: Any = None, message: str = "success") -> dict:
    """Return a success response."""
    return {"code": 200, "message": message, "data": data}


def error(message: str = "error", code: int = 400, data: Any = None) -> dict:
    """Return an error response."""
    return {"code": code, "message": message, "data": data}


def page_response(data: list, total: int, page: int = 1, page_size: int = 20) -> dict:
    """Return a paginated response."""
    return {
        "code": 200,
        "message": "success",
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
