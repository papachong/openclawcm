"""
Dashboard API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.instance import Instance
from app.models.agent import Agent
from app.models.skill import Skill
from app.models.output import Output
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

    return success({
        "instance_count": instance_count,
        "agent_count": agent_count,
        "active_agent_count": active_agent_count,
        "skill_count": skill_count,
        "output_count": output_count,
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
