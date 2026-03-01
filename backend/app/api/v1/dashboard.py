"""
Dashboard API endpoints - overview, trends, stats, alerts.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, case
from typing import Optional

from app.database import get_db
from app.models.instance import Instance
from app.models.agent import Agent
from app.models.skill import Skill
from app.models.output import Output
from app.models.collaboration import Collaboration
from app.utils.response import success

router = APIRouter()


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Get dashboard overview statistics."""
    instance_count = (await db.execute(select(func.count(Instance.id)))).scalar() or 0
    agent_count = (await db.execute(select(func.count(Agent.id)))).scalar() or 0
    active_agent_count = (await db.execute(
        select(func.count(Agent.id)).where(Agent.status == "running")
    )).scalar() or 0
    skill_count = (await db.execute(
        select(func.count(Skill.id)).where(Skill.status == "installed")
    )).scalar() or 0
    output_count = (await db.execute(select(func.count(Output.id)))).scalar() or 0
    collab_count = (await db.execute(
        select(func.count(Collaboration.id)).where(Collaboration.is_template == 0)
    )).scalar() or 0
    pool_count = 0
    try:
        from app.models.memory_pool import SharedMemoryPool
        pool_count = (await db.execute(select(func.count(SharedMemoryPool.id)))).scalar() or 0
    except Exception:
        pass

    return success({
        "instance_count": instance_count,
        "agent_count": agent_count,
        "active_agent_count": active_agent_count,
        "skill_count": skill_count,
        "output_count": output_count,
        "collab_count": collab_count,
        "pool_count": pool_count,
    })


@router.get("/output-trends")
async def get_output_trends(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Get daily output count for the last N days."""
    data = []
    today = datetime.utcnow().date()
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        count_result = await db.execute(
            select(func.count(Output.id)).where(
                Output.created_at >= day_start,
                Output.created_at < day_end,
            )
        )
        count = count_result.scalar() or 0
        data.append({"date": day.isoformat(), "count": count})
    return success(data)


@router.get("/agent-stats")
async def get_agent_stats(db: AsyncSession = Depends(get_db)):
    """Get agent status distribution."""
    result = await db.execute(
        select(Agent.status, func.count(Agent.id)).group_by(Agent.status)
    )
    stats = {row[0]: row[1] for row in result.fetchall()}
    return success({
        "running": stats.get("running", 0),
        "stopped": stats.get("stopped", 0),
        "error": stats.get("error", 0),
        "idle": stats.get("idle", 0),
    })


@router.get("/output-type-stats")
async def get_output_type_stats(db: AsyncSession = Depends(get_db)):
    """Get output type distribution."""
    result = await db.execute(
        select(Output.output_type, func.count(Output.id)).group_by(Output.output_type)
    )
    data = [{"type": row[0], "count": row[1]} for row in result.fetchall()]
    return success(data)


@router.get("/instance-health")
async def get_instance_health(db: AsyncSession = Depends(get_db)):
    """Get instance health summary."""
    result = await db.execute(
        select(Instance.status, func.count(Instance.id)).group_by(Instance.status)
    )
    stats = {row[0]: row[1] for row in result.fetchall()}
    return success({
        "online": stats.get("online", 0),
        "offline": stats.get("offline", 0),
        "unknown": stats.get("unknown", 0),
    })


@router.get("/recent-outputs")
async def get_recent_outputs(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get recent output activity."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Output).options(
            selectinload(Output.instance),
            selectinload(Output.agent),
        ).order_by(Output.id.desc()).limit(limit)
    )
    items = result.scalars().all()
    data = []
    for item in items:
        data.append({
            "id": item.id,
            "title": item.title,
            "output_type": item.output_type,
            "status": item.status,
            "instance_name": item.instance.name if item.instance else None,
            "agent_name": item.agent.name if item.agent else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })
    return success(data)


@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    """Get system alerts (offline instances, error agents)."""
    alerts = []

    # Offline instances
    result = await db.execute(select(Instance).where(Instance.status == "offline"))
    for inst in result.scalars().all():
        alerts.append({"type": "warning", "message": f"实例 '{inst.name}' 离线", "resource_type": "instance", "resource_id": inst.id})

    # Error agents
    result = await db.execute(select(Agent).where(Agent.status == "error"))
    for agent in result.scalars().all():
        alerts.append({"type": "error", "message": f"Agent '{agent.name}' 异常", "resource_type": "agent", "resource_id": agent.id})

    return success(alerts)
