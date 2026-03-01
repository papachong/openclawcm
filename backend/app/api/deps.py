"""
API dependencies: DB session, auth, pagination, etc.
"""
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db


async def get_pagination(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    """Common pagination parameters."""
    return {"page": page, "page_size": page_size, "offset": (page - 1) * page_size}
