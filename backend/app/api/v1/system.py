"""
System settings API endpoints - system info, audit logs, settings.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.user import AuditLog, SystemSetting, User
from app.utils.auth import require_auth, require_admin
from app.utils.response import success, error, page_response

router = APIRouter()


@router.get("/info")
async def get_system_info():
    """Get system information."""
    from app.config import settings
    return {"code": 200, "message": "success", "data": {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }}


# ==================== Audit Logs ====================
@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if username:
        query = query.where(AuditLog.username.contains(username))
        count_query = count_query.where(AuditLog.username.contains(username))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = [{
        "id": item.id,
        "user_id": item.user_id,
        "username": item.username,
        "action": item.action,
        "resource_type": item.resource_type,
        "resource_id": item.resource_id,
        "detail": item.detail,
        "ip_address": item.ip_address,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    } for item in items]

    return page_response(data, total, page, page_size)


# ==================== System Settings ====================
@router.get("/settings")
async def list_settings(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SystemSetting).order_by(SystemSetting.key))
    items = result.scalars().all()
    data = [{
        "id": item.id,
        "key": item.key,
        "value": item.value,
        "description": item.description,
    } for item in items]
    return success(data)


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    value: str = Query(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        setting = SystemSetting(key=key, value=value)
        db.add(setting)
    else:
        setting.value = value
    await db.flush()
    return success({"key": key, "value": value}, "设置已更新")
