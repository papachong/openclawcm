"""
Model management API endpoints - full CRUD for providers & configs.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models.model_config import ModelProvider, ModelConfig
from app.schemas.model_config import (
    ProviderCreate, ProviderUpdate, ProviderOut,
    ModelConfigCreate, ModelConfigUpdate, ModelConfigOut,
)
from app.utils.response import success, error, page_response

router = APIRouter()


# ==================== Providers (MUST be before /{config_id} to avoid route collision) ====================
@router.get("/providers")
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelProvider).order_by(ModelProvider.id.desc()))
    items = result.scalars().all()
    data = [ProviderOut.model_validate(item).model_dump() for item in items]
    return success(data)


@router.post("/providers")
async def create_provider(data: ProviderCreate, db: AsyncSession = Depends(get_db)):
    provider = ModelProvider(**data.model_dump())
    db.add(provider)
    await db.flush()
    await db.refresh(provider)
    return success(ProviderOut.model_validate(provider).model_dump(), "供应商创建成功")


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: int, data: ProviderUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelProvider).where(ModelProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        return error("供应商不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(provider, key, value)

    await db.flush()
    await db.refresh(provider)
    return success(ProviderOut.model_validate(provider).model_dump(), "更新成功")


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelProvider).where(ModelProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        return error("供应商不存在", 404)
    await db.delete(provider)
    return success(None, "删除成功")


# ==================== Model Configs ====================
@router.get("")
async def list_model_configs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scope: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ModelConfig).options(selectinload(ModelConfig.provider))
    count_query = select(func.count(ModelConfig.id))

    if scope:
        query = query.where(ModelConfig.scope == scope)
        count_query = count_query.where(ModelConfig.scope == scope)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(ModelConfig.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = []
    for item in items:
        d = ModelConfigOut.model_validate(item).model_dump()
        d["provider_name"] = item.provider.name if item.provider else None
        data.append(d)

    return page_response(data, total, page, page_size)


@router.get("/{config_id}")
async def get_model_config(config_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelConfig).options(selectinload(ModelConfig.provider)).where(ModelConfig.id == config_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return error("模型配置不存在", 404)
    d = ModelConfigOut.model_validate(item).model_dump()
    d["provider_name"] = item.provider.name if item.provider else None
    return success(d)


@router.post("")
async def create_model_config(data: ModelConfigCreate, db: AsyncSession = Depends(get_db)):
    config = ModelConfig(**data.model_dump())
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return success(ModelConfigOut.model_validate(config).model_dump(), "创建成功")


@router.put("/{config_id}")
async def update_model_config(config_id: int, data: ModelConfigUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        return error("模型配置不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(config, key, value)

    await db.flush()
    await db.refresh(config)
    return success(ModelConfigOut.model_validate(config).model_dump(), "更新成功")


@router.delete("/{config_id}")
async def delete_model_config(config_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        return error("模型配置不存在", 404)
    await db.delete(config)
    return success(None, "删除成功")
