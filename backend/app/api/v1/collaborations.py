"""
Multi-agent collaboration API endpoints.
"""
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.collaboration import Collaboration
from app.schemas.collaboration import CollaborationCreate, CollaborationUpdate, CollaborationOut
from app.utils.response import success, error, page_response

router = APIRouter()


@router.get("")
async def list_collaborations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(select(func.count(Collaboration.id)).where(Collaboration.is_template == 0))
    total = count_result.scalar() or 0

    query = select(Collaboration).where(Collaboration.is_template == 0)\
        .order_by(Collaboration.id.desc())\
        .offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = []
    for item in items:
        d = CollaborationOut.model_validate(item).model_dump()
        try:
            agent_list = json.loads(item.agent_ids) if item.agent_ids else []
            d["agent_count"] = len(agent_list)
        except Exception:
            d["agent_count"] = 0
        data.append(d)

    return page_response(data, total, page, page_size)


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collaboration).where(Collaboration.is_template == 1))
    items = result.scalars().all()
    data = [CollaborationOut.model_validate(item).model_dump() for item in items]
    return success(data)


@router.get("/{collab_id}")
async def get_collaboration(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collaboration).where(Collaboration.id == collab_id))
    item = result.scalar_one_or_none()
    if not item:
        return error("协作配置不存在", 404)
    return success(CollaborationOut.model_validate(item).model_dump())


@router.post("")
async def create_collaboration(data: CollaborationCreate, db: AsyncSession = Depends(get_db)):
    collab = Collaboration(**data.model_dump())
    db.add(collab)
    await db.flush()
    await db.refresh(collab)
    return success(CollaborationOut.model_validate(collab).model_dump(), "创建成功")


@router.put("/{collab_id}")
async def update_collaboration(collab_id: int, data: CollaborationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collaboration).where(Collaboration.id == collab_id))
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(collab, key, value)

    await db.flush()
    await db.refresh(collab)
    return success(CollaborationOut.model_validate(collab).model_dump(), "更新成功")


@router.delete("/{collab_id}")
async def delete_collaboration(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collaboration).where(Collaboration.id == collab_id))
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)
    await db.delete(collab)
    return success(None, "删除成功")


@router.post("/{collab_id}/save-template")
async def save_as_template(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collaboration).where(Collaboration.id == collab_id))
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)

    template = Collaboration(
        name=collab.name,
        type=collab.type,
        agent_ids=collab.agent_ids,
        routing_rules=collab.routing_rules,
        description=collab.description,
        is_template=1,
        template_name=f"{collab.name}_模板",
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return success(CollaborationOut.model_validate(template).model_dump(), "已保存为模板")
