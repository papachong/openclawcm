"""
Agent management API endpoints - full CRUD.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models.agent import Agent
from app.models.instance import Instance
from app.models.model_config import ModelConfig
from app.schemas.agent import AgentCreate, AgentUpdate, AgentOut
from app.utils.response import success, error, page_response

router = APIRouter()


@router.get("")
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    instance_id: Optional[int] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Agent).options(selectinload(Agent.instance), selectinload(Agent.model_config))
    count_query = select(func.count(Agent.id))

    if instance_id:
        query = query.where(Agent.instance_id == instance_id)
        count_query = count_query.where(Agent.instance_id == instance_id)
    if name:
        query = query.where(Agent.name.contains(name))
        count_query = count_query.where(Agent.name.contains(name))
    if status:
        query = query.where(Agent.status == status)
        count_query = count_query.where(Agent.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Agent.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = []
    for item in items:
        d = AgentOut.model_validate(item).model_dump()
        d["instance_name"] = item.instance.name if item.instance else None
        d["model_name"] = item.model_config.model_name if item.model_config else "默认模型"
        data.append(d)

    return page_response(data, total, page, page_size)


@router.get("/{agent_id}")
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Agent).options(selectinload(Agent.instance), selectinload(Agent.model_config))
        .where(Agent.id == agent_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return error("Agent不存在", 404)
    d = AgentOut.model_validate(item).model_dump()
    d["instance_name"] = item.instance.name if item.instance else None
    d["model_name"] = item.model_config.model_name if item.model_config else "默认模型"
    return success(d)


@router.post("")
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = Agent(**data.model_dump())
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return success(AgentOut.model_validate(agent).model_dump(), "创建成功")


@router.put("/{agent_id}")
async def update_agent(agent_id: int, data: AgentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return error("Agent不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)

    await db.flush()
    await db.refresh(agent)
    return success(AgentOut.model_validate(agent).model_dump(), "更新成功")


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return error("Agent不存在", 404)
    await db.delete(agent)
    return success(None, "删除成功")


@router.post("/{agent_id}/start")
async def start_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return error("Agent不存在", 404)
    agent.status = "running"
    await db.flush()
    return success({"id": agent_id, "status": "running"}, "启动成功")


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return error("Agent不存在", 404)
    agent.status = "stopped"
    await db.flush()
    return success({"id": agent_id, "status": "stopped"}, "已停止")


@router.post("/{agent_id}/restart")
async def restart_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return error("Agent不存在", 404)
    agent.status = "running"
    await db.flush()
    return success({"id": agent_id, "status": "running"}, "重启成功")


@router.post("/{agent_id}/copy")
async def copy_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return error("Agent不存在", 404)

    new_agent = Agent(
        name=f"{agent.name} (副本)",
        instance_id=agent.instance_id,
        role=agent.role,
        model_config_id=agent.model_config_id,
        system_prompt=agent.system_prompt,
        description=agent.description,
        status="stopped",
    )
    db.add(new_agent)
    await db.flush()
    await db.refresh(new_agent)
    return success(AgentOut.model_validate(new_agent).model_dump(), "复制成功")
