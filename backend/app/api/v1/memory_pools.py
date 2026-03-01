"""
Shared memory pool management API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models.agent import SharedMemoryPool, AgentMemoryPoolBinding, Agent
from app.schemas.agent import (
    SharedMemoryPoolCreate, SharedMemoryPoolUpdate, SharedMemoryPoolOut,
    PoolAgentBind, PoolAgentBindingOut,
)
from app.utils.response import success, error, page_response

router = APIRouter()


def _pool_to_dict(item) -> dict:
    loaded = item.__dict__
    bindings = loaded.get('agent_bindings')
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "memory_type": item.memory_type or "buffer",
        "max_history_messages": item.max_history_messages or 50,
        "max_token_limit": item.max_token_limit or 8000,
        "status": item.status or "active",
        "collaboration_id": item.collaboration_id,
        "message_count": item.message_count or 0,
        "total_tokens": item.total_tokens or 0,
        "agent_count": len(bindings) if bindings else 0,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("")
async def list_memory_pools(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(SharedMemoryPool).options(selectinload(SharedMemoryPool.agent_bindings))
    count_query = select(func.count(SharedMemoryPool.id))

    if status:
        query = query.where(SharedMemoryPool.status == status)
        count_query = count_query.where(SharedMemoryPool.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(SharedMemoryPool.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = [_pool_to_dict(item) for item in items]
    return page_response(data, total, page, page_size)


@router.get("/{pool_id}")
async def get_memory_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SharedMemoryPool).options(selectinload(SharedMemoryPool.agent_bindings))
        .where(SharedMemoryPool.id == pool_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return error("记忆池不存在", 404)
    return success(_pool_to_dict(item))


@router.post("")
async def create_memory_pool(data: SharedMemoryPoolCreate, db: AsyncSession = Depends(get_db)):
    pool = SharedMemoryPool(**data.model_dump())
    db.add(pool)
    await db.flush()
    await db.refresh(pool)
    return success(_pool_to_dict(pool), "创建成功")


@router.put("/{pool_id}")
async def update_memory_pool(pool_id: int, data: SharedMemoryPoolUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SharedMemoryPool).where(SharedMemoryPool.id == pool_id))
    pool = result.scalar_one_or_none()
    if not pool:
        return error("记忆池不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(pool, key, value)

    await db.flush()
    await db.refresh(pool)
    return success(_pool_to_dict(pool), "更新成功")


@router.delete("/{pool_id}")
async def delete_memory_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SharedMemoryPool).where(SharedMemoryPool.id == pool_id))
    pool = result.scalar_one_or_none()
    if not pool:
        return error("记忆池不存在", 404)
    await db.delete(pool)
    return success(None, "删除成功")


# ==================== Agent Bindings ====================
@router.get("/{pool_id}/agents")
async def list_pool_agents(pool_id: int, db: AsyncSession = Depends(get_db)):
    """List agents bound to a memory pool."""
    result = await db.execute(select(SharedMemoryPool).where(SharedMemoryPool.id == pool_id))
    if not result.scalar_one_or_none():
        return error("记忆池不存在", 404)

    result = await db.execute(
        select(AgentMemoryPoolBinding).options(selectinload(AgentMemoryPoolBinding.agent))
        .where(AgentMemoryPoolBinding.pool_id == pool_id)
        .order_by(AgentMemoryPoolBinding.id.desc())
    )
    items = result.scalars().all()
    data = []
    for item in items:
        data.append({
            "id": item.id,
            "agent_id": item.agent_id,
            "pool_id": item.pool_id,
            "agent_name": item.agent.name if item.agent else None,
            "permission": item.permission,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })
    return success(data)


@router.post("/{pool_id}/agents")
async def bind_agent_to_pool(pool_id: int, data: PoolAgentBind, db: AsyncSession = Depends(get_db)):
    """Bind an agent to a memory pool."""
    result = await db.execute(select(SharedMemoryPool).where(SharedMemoryPool.id == pool_id))
    if not result.scalar_one_or_none():
        return error("记忆池不存在", 404)

    result = await db.execute(select(Agent).where(Agent.id == data.agent_id))
    if not result.scalar_one_or_none():
        return error("Agent不存在", 404)

    # Check duplicate
    existing = await db.execute(
        select(AgentMemoryPoolBinding).where(
            AgentMemoryPoolBinding.pool_id == pool_id,
            AgentMemoryPoolBinding.agent_id == data.agent_id,
        )
    )
    if existing.scalar_one_or_none():
        return error("该Agent已绑定到此记忆池", 400)

    binding = AgentMemoryPoolBinding(
        pool_id=pool_id,
        agent_id=data.agent_id,
        permission=data.permission,
    )
    db.add(binding)
    await db.flush()
    await db.refresh(binding)
    return success({
        "id": binding.id,
        "pool_id": pool_id,
        "agent_id": data.agent_id,
        "permission": binding.permission,
    }, "绑定成功")


@router.delete("/{pool_id}/agents/{agent_id}")
async def unbind_agent_from_pool(pool_id: int, agent_id: int, db: AsyncSession = Depends(get_db)):
    """Unbind an agent from a memory pool."""
    result = await db.execute(
        select(AgentMemoryPoolBinding).where(
            AgentMemoryPoolBinding.pool_id == pool_id,
            AgentMemoryPoolBinding.agent_id == agent_id,
        )
    )
    binding = result.scalar_one_or_none()
    if not binding:
        return error("绑定关系不存在", 404)
    await db.delete(binding)
    return success(None, "解绑成功")
