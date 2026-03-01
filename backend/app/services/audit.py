"""
Audit log service - records user operations for traceability.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    detail: Optional[str] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """Record an audit log entry."""
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    await db.flush()
