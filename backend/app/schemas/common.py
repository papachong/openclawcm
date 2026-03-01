"""
Common schemas: pagination, response wrapper.
"""
from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class PagedResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[List[Any]] = None
    total: int = 0
    page: int = 1
    page_size: int = 20
