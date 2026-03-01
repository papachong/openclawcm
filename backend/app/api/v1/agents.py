"""
Agent management API endpoints - full CRUD + memory config + skills binding.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models.agent import Agent, AgentSkill
from app.models.instance import Instance
from app.models.skill import Skill
from app.models.model_config import ModelConfig
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentOut,
    AgentSkillBind, AgentSkillOut,
)
from app.utils.response import success, error, page_response

router = APIRouter()


def _agent_to_dict(item) -> dict:
    """Build agent response dict, safely accessing relationships."""
    loaded = item.__dict__
    instance = loaded.get('instance')
    model_config = loaded.get('model_config')
    summary_model = loaded.get('summary_model')
    return {
        "id": item.id,
        "name": item.name,
        "instance_id": item.instance_id,
        "instance_name": instance.name if instance else None,
        "role": item.role,
        "model_config_id": item.model_config_id,
        "model_name": model_config.model_name if model_config else "默认模型",
        "system_prompt": item.system_prompt,
        "status": item.status,
        "description": item.description,
        "skills_count": item.skills_count,
        # Memory config
        "memory_type": item.memory_type or "buffer",
        "max_history_messages": item.max_history_messages or 20,
        "max_token_limit": item.max_token_limit or 4000,
        "summary_model_id": item.summary_model_id,
        "summary_model_name": summary_model.model_name if summary_model else None,
        "memory_persistence": item.memory_persistence if item.memory_persistence is not None else 1,
        "auto_cleanup_days": item.auto_cleanup_days or 0,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("")
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    instance_id: Optional[int] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Agent).options(
        selectinload(Agent.instance),
        selectinload(Agent.model_config),
        selectinload(Agent.summary_model),
    )
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

    data = [_agent_to_dict(item) for item in items]
    return page_response(data, total, page, page_size)


@router.get("/{agent_id}")
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Agent).options(
            selectinload(Agent.instance),
            selectinload(Agent.model_config),
            selectinload(Agent.summary_model),
        ).where(Agent.id == agent_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return error("Agent不存在", 404)
    return success(_agent_to_dict(item))


@router.post("")
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = Agent(**data.model_dump())
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return success(_agent_to_dict(agent), "创建成功")


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
    return success(_agent_to_dict(agent), "更新成功")


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
        memory_type=agent.memory_type,
        max_history_messages=agent.max_history_messages,
        max_token_limit=agent.max_token_limit,
        summary_model_id=agent.summary_model_id,
        memory_persistence=agent.memory_persistence,
        auto_cleanup_days=agent.auto_cleanup_days,
    )
    db.add(new_agent)
    await db.flush()
    await db.refresh(new_agent)
    return success(_agent_to_dict(new_agent), "复制成功")


# ==================== Skills Binding ====================
@router.get("/{agent_id}/skills")
async def list_agent_skills(agent_id: int, db: AsyncSession = Depends(get_db)):
    """List all skills bound to an agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    if not result.scalar_one_or_none():
        return error("Agent不存在", 404)

    result = await db.execute(
        select(AgentSkill).options(selectinload(AgentSkill.skill))
        .where(AgentSkill.agent_id == agent_id)
        .order_by(AgentSkill.id.desc())
    )
    items = result.scalars().all()
    data = []
    for item in items:
        data.append({
            "id": item.id,
            "agent_id": item.agent_id,
            "skill_id": item.skill_id,
            "skill_name": item.skill.name if item.skill else None,
            "skill_version": item.skill.version if item.skill else None,
            "skill_status": item.skill.status if item.skill else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })
    return success(data)


@router.post("/{agent_id}/skills")
async def bind_agent_skill(agent_id: int, data: AgentSkillBind, db: AsyncSession = Depends(get_db)):
    """Bind a skill to an agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return error("Agent不存在", 404)

    result = await db.execute(select(Skill).where(Skill.id == data.skill_id))
    if not result.scalar_one_or_none():
        return error("Skill不存在", 404)

    # Check duplicate
    existing = await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id, AgentSkill.skill_id == data.skill_id)
    )
    if existing.scalar_one_or_none():
        return error("该Skill已绑定", 400)

    binding = AgentSkill(agent_id=agent_id, skill_id=data.skill_id)
    db.add(binding)
    agent.skills_count = (agent.skills_count or 0) + 1
    await db.flush()
    await db.refresh(binding)
    return success({"id": binding.id, "agent_id": agent_id, "skill_id": data.skill_id}, "绑定成功")


@router.delete("/{agent_id}/skills/{skill_id}")
async def unbind_agent_skill(agent_id: int, skill_id: int, db: AsyncSession = Depends(get_db)):
    """Unbind a skill from an agent."""
    result = await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id, AgentSkill.skill_id == skill_id)
    )
    binding = result.scalar_one_or_none()
    if not binding:
        return error("绑定关系不存在", 404)

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent and agent.skills_count and agent.skills_count > 0:
        agent.skills_count -= 1

    await db.delete(binding)
    return success(None, "解绑成功")
