"""
Skills management API endpoints - full CRUD.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate, SkillOut
from app.utils.response import success, error, page_response

router = APIRouter()


@router.get("")
async def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    name: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Skill)
    count_query = select(func.count(Skill.id))

    if name:
        query = query.where(Skill.name.contains(name))
        count_query = count_query.where(Skill.name.contains(name))
    if status:
        query = query.where(Skill.status == status)
        count_query = count_query.where(Skill.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Skill.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = [SkillOut.model_validate(item).model_dump() for item in items]
    return page_response(data, total, page, page_size)


@router.get("/{skill_id}")
async def get_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    item = result.scalar_one_or_none()
    if not item:
        return error("Skill不存在", 404)
    return success(SkillOut.model_validate(item).model_dump())


@router.post("")
async def create_skill(data: SkillCreate, db: AsyncSession = Depends(get_db)):
    skill = Skill(**data.model_dump())
    db.add(skill)
    await db.flush()
    await db.refresh(skill)
    return success(SkillOut.model_validate(skill).model_dump(), "创建成功")


@router.put("/{skill_id}")
async def update_skill(skill_id: int, data: SkillUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        return error("Skill不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(skill, key, value)

    await db.flush()
    await db.refresh(skill)
    return success(SkillOut.model_validate(skill).model_dump(), "更新成功")


@router.delete("/{skill_id}")
async def delete_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        return error("Skill不存在", 404)
    await db.delete(skill)
    return success(None, "删除成功")


@router.post("/{skill_id}/install")
async def install_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        return error("Skill不存在", 404)
    skill.status = "installed"
    await db.flush()
    return success({"id": skill_id, "status": "installed"}, "安装成功")


@router.post("/{skill_id}/uninstall")
async def uninstall_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        return error("Skill不存在", 404)
    skill.status = "available"
    await db.flush()
    return success({"id": skill_id, "status": "available"}, "卸载成功")
