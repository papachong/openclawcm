"""
Instance management API endpoints - full CRUD + config sync.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.instance import Instance
from app.models.agent import Agent
from app.models.skill import Skill
from app.models.model_config import ModelProvider, ModelConfig
from app.schemas.instance import InstanceCreate, InstanceUpdate, InstanceOut
from app.services.openclaw_gateway import sync_instance_config
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
        headers = {}
        if instance.api_key:
            headers["Authorization"] = f"Bearer {instance.api_key}"
            headers["X-API-Key"] = instance.api_key
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{instance.url}/health", headers=headers)
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


@router.post("/{instance_id}/sync")
async def sync_config(instance_id: int, db: AsyncSession = Depends(get_db)):
    """Sync configuration from a remote OpenClaw instance.

    Fetches agents, models (from config.get), and plugins from the remote gateway,
    then upserts them into the local database.
    """
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        return error("实例不存在", 404)
    if not instance.api_key:
        return error("实例未配置 API Key，无法同步配置", 400)

    # First do health check
    import httpx
    try:
        headers = {}
        if instance.api_key:
            headers["Authorization"] = f"Bearer {instance.api_key}"
            headers["X-API-Key"] = instance.api_key
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{instance.url}/health", headers=headers)
            if resp.status_code == 200:
                instance.status = "online"
                instance.last_heartbeat = datetime.now().isoformat()
            else:
                instance.status = "offline"
                await db.flush()
                return error(f"实例不可达 (HTTP {resp.status_code})")
    except Exception as e:
        instance.status = "offline"
        await db.flush()
        return error(f"实例连通失败: {str(e)}")

    # Sync via WebSocket gateway
    try:
        sync_data = await sync_instance_config(instance.url, instance.api_key)
    except Exception as e:
        await db.flush()
        return error(f"网关同步失败: {str(e)}")

    synced = {"agents": 0, "models": 0, "plugins": 0, "errors": sync_data.get("errors", [])}

    # ---- Sync Agents ----
    for remote_agent in sync_data.get("agents", []):
        rname = remote_agent.get("name")
        if not rname:
            continue
        existing_res = await db.execute(
            select(Agent).where(Agent.instance_id == instance_id, Agent.name == rname)
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            if remote_agent.get("role"):
                existing.role = remote_agent["role"]
            if remote_agent.get("description"):
                existing.description = remote_agent["description"]
        else:
            db.add(Agent(
                name=rname,
                instance_id=instance_id,
                role=remote_agent.get("role"),
                description=remote_agent.get("description"),
                status="stopped",
            ))
        synced["agents"] += 1

    # Flush agents first so count is accurate
    await db.flush()

    # ---- Sync Models (from remote config) ----
    for remote_model in sync_data.get("models", []):
        mname = remote_model.get("name")
        model_name = remote_model.get("model_name", "unknown")
        if not mname:
            continue
        # Find or create provider
        provider_name = remote_model.get("provider", "unknown")
        provider_res = await db.execute(
            select(ModelProvider).where(ModelProvider.name == provider_name)
        )
        provider = provider_res.scalar_one_or_none()
        if not provider:
            provider = ModelProvider(
                name=provider_name,
                api_type="openai",
                base_url=remote_model.get("base_url"),
                status="active",
                description=f"从实例 {instance.name} 同步",
            )
            db.add(provider)
            await db.flush()

        # Find or create model config
        existing_res = await db.execute(
            select(ModelConfig).where(
                ModelConfig.instance_id == instance_id,
                ModelConfig.name == mname,
            )
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            existing.model_name = model_name
            existing.provider_id = provider.id
            if remote_model.get("description"):
                existing.description = remote_model["description"]
        else:
            db.add(ModelConfig(
                name=mname,
                model_name=model_name,
                provider_id=provider.id,
                scope="instance",
                instance_id=instance_id,
                description=remote_model.get("description") or f"从实例 {instance.name} 同步",
            ))
        synced["models"] += 1

    # ---- Sync Plugins -> Skills ----
    for remote_plugin in sync_data.get("plugins", []):
        pname = remote_plugin.get("name")
        if not pname:
            continue
        existing_res = await db.execute(
            select(Skill).where(Skill.name == pname)
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            if remote_plugin.get("version"):
                existing.version = remote_plugin["version"]
            if remote_plugin.get("description"):
                existing.description = remote_plugin["description"]
            if remote_plugin.get("status"):
                existing.status = remote_plugin["status"]
        else:
            db.add(Skill(
                name=pname,
                version=remote_plugin.get("version", "1.0.0"),
                description=remote_plugin.get("description"),
                status=remote_plugin.get("status", "available"),
            ))
        synced["plugins"] += 1

    # Recalculate agent count after inserts
    await db.flush()
    cnt_res2 = await db.execute(
        select(func.count(Agent.id)).where(Agent.instance_id == instance_id)
    )
    instance.agent_count = cnt_res2.scalar() or 0
    await db.flush()

    return success({
        "instance_id": instance_id,
        "synced_agents": synced["agents"],
        "synced_models": synced["models"],
        "synced_plugins": synced["plugins"],
        "errors": synced["errors"],
        "gateway_version": sync_data.get("gateway_version"),
    }, "同步完成")


@router.post("/sync-all")
async def sync_all_instances(db: AsyncSession = Depends(get_db)):
    """Sync configuration from ALL online instances that have an API key."""
    result = await db.execute(
        select(Instance).where(Instance.api_key.isnot(None), Instance.api_key != "")
    )
    instances = result.scalars().all()

    if not instances:
        return success({"total": 0, "results": []}, "没有可同步的实例")

    import httpx
    results = []
    for inst in instances:
        entry = {"instance_id": inst.id, "name": inst.name, "status": "skipped"}
        # Health check first
        try:
            headers = {}
            if inst.api_key:
                headers["Authorization"] = f"Bearer {inst.api_key}"
                headers["X-API-Key"] = inst.api_key
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{inst.url}/health", headers=headers)
                if resp.status_code == 200:
                    inst.status = "online"
                    inst.last_heartbeat = datetime.now().isoformat()
                else:
                    inst.status = "offline"
                    entry["status"] = "offline"
                    results.append(entry)
                    continue
        except Exception as e:
            inst.status = "offline"
            entry["status"] = f"连通失败: {str(e)}"
            results.append(entry)
            continue

        # Sync via gateway
        try:
            sync_data = await sync_instance_config(inst.url, inst.api_key)
            synced_agents = 0
            for remote_agent in sync_data.get("agents", []):
                rname = remote_agent.get("name")
                if not rname:
                    continue
                existing_res = await db.execute(
                    select(Agent).where(Agent.instance_id == inst.id, Agent.name == rname)
                )
                existing = existing_res.scalar_one_or_none()
                if existing:
                    if remote_agent.get("role"):
                        existing.role = remote_agent["role"]
                    if remote_agent.get("description"):
                        existing.description = remote_agent["description"]
                else:
                    db.add(Agent(
                        name=rname,
                        instance_id=inst.id,
                        role=remote_agent.get("role"),
                        description=remote_agent.get("description"),
                        status="stopped",
                    ))
                synced_agents += 1

            await db.flush()
            cnt_res = await db.execute(
                select(func.count(Agent.id)).where(Agent.instance_id == inst.id)
            )
            inst.agent_count = cnt_res.scalar() or 0

            entry["status"] = "synced"
            entry["agents"] = synced_agents
            entry["models"] = len(sync_data.get("models", []))
            entry["plugins"] = len(sync_data.get("plugins", []))
            entry["errors"] = sync_data.get("errors", [])
        except Exception as e:
            entry["status"] = f"同步失败: {str(e)}"

        results.append(entry)

    await db.flush()
    return success({"total": len(results), "results": results}, "批量同步完成")
