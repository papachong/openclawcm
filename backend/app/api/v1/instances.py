"""
Instance management API endpoints - full CRUD.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.instance import Instance
from app.schemas.instance import InstanceCreate, InstanceUpdate, InstanceOut
from app.utils.response import success, error, page_response

router = APIRouter()


@router.get("")
async def list_instances(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all OpenClaw instances with pagination and filters."""
    query = select(Instance)
    count_query = select(func.count(Instance.id))

    if name:
        query = query.where(Instance.name.contains(name))
        count_query = count_query.where(Instance.name.contains(name))
    if status:
        query = query.where(Instance.status == status)
        count_query = count_query.where(Instance.status == status)

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginated results
    query = query.order_by(Instance.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = [InstanceOut.model_validate(item).model_dump() for item in items]
    return page_response(data, total, page, page_size)


@router.get("/{instance_id}")
async def get_instance(instance_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single instance by ID."""
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    item = result.scalar_one_or_none()
    if not item:
        return error("实例不存在", 404)
    return success(InstanceOut.model_validate(item).model_dump())


@router.post("")
async def create_instance(data: InstanceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new OpenClaw instance."""
    instance = Instance(**data.model_dump())
    db.add(instance)
    await db.flush()
    await db.refresh(instance)
    return success(InstanceOut.model_validate(instance).model_dump(), "创建成功")


@router.put("/{instance_id}")
async def update_instance(instance_id: int, data: InstanceUpdate, db: AsyncSession = Depends(get_db)):
    """Update an instance."""
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        return error("实例不存在", 404)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(instance, key, value)

    await db.flush()
    await db.refresh(instance)
    return success(InstanceOut.model_validate(instance).model_dump(), "更新成功")


@router.delete("/{instance_id}")
async def delete_instance(instance_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an instance."""
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        return error("实例不存在", 404)
    await db.delete(instance)
    return success(None, "删除成功")


@router.post("/{instance_id}/health-check")
async def health_check(instance_id: int, db: AsyncSession = Depends(get_db)):
    """Check instance connectivity."""
    import httpx
    from datetime import datetime

    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        return error("实例不存在", 404)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{instance.url}/health")
            if resp.status_code == 200:
                instance.status = "online"
                instance.last_heartbeat = datetime.now().isoformat()
                await db.flush()
                return success({"status": "online"}, "连通性检测成功")
            else:
                instance.status = "offline"
                await db.flush()
                return error(f"实例返回状态码 {resp.status_code}")
    except Exception as e:
        instance.status = "offline"
        await db.flush()
        return error(f"连通失败: {str(e)}")
