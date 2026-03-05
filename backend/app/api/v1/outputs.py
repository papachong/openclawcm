"""
Output management API endpoints - full CRUD + search + tags + export + batch ops.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.output import Output, OutputTag
from app.models.instance import Instance
from app.models.agent import Agent
from app.schemas.output import OutputCreate, OutputOut, TagCreate
from app.utils.response import success, error, page_response

router = APIRouter()


class BatchIds(BaseModel):
    ids: List[int]


def _output_to_dict(item) -> dict:
    """Build output response dict manually to avoid lazy-loading relationships."""
    # Check __dict__ to avoid triggering SQLAlchemy lazy loading
    loaded = item.__dict__
    instance = loaded.get('instance')
    agent = loaded.get('agent')
    tags = loaded.get('tags')
    return {
        "id": item.id,
        "instance_id": item.instance_id,
        "agent_id": item.agent_id,
        "task_id": item.task_id,
        "output_type": item.output_type,
        "content_type": item.content_type,
        "title": item.title,
        "summary": item.summary,
        "content": item.content,
        "raw_content": item.raw_content,
        "metadata_json": item.metadata_json,
        "status": item.status,
        "is_favorite": item.is_favorite,
        "token_usage": item.token_usage,
        "instance_name": instance.name if instance else None,
        "agent_name": agent.name if agent else None,
        "tags": [t.tag_name for t in tags] if tags else [],
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/search")
async def search_outputs(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    instance_id: Optional[int] = None,
    output_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Full-text search outputs using SQLite FTS5."""
    # Count matching results
    count_sql = "SELECT COUNT(*) FROM outputs_fts WHERE outputs_fts MATCH :q"
    count_result = await db.execute(text(count_sql), {"q": q})
    total = count_result.scalar() or 0

    # Get matching output IDs with ranking
    fts_sql = """
        SELECT rowid, rank FROM outputs_fts
        WHERE outputs_fts MATCH :q
        ORDER BY rank
        LIMIT :limit OFFSET :offset
    """
    fts_result = await db.execute(text(fts_sql), {
        "q": q,
        "limit": page_size,
        "offset": (page - 1) * page_size,
    })
    rows = fts_result.fetchall()
    row_ids = [row[0] for row in rows]

    if not row_ids:
        return page_response([], total, page, page_size)

    # Fetch full output records
    query = select(Output).options(
        selectinload(Output.instance),
        selectinload(Output.agent),
        selectinload(Output.tags),
    ).where(Output.id.in_(row_ids))

    if instance_id:
        query = query.where(Output.instance_id == instance_id)
    if output_type:
        query = query.where(Output.output_type == output_type)

    result = await db.execute(query)
    items = result.scalars().all()

    # Preserve FTS ranking order
    item_map = {item.id: item for item in items}
    data = []
    for rid in row_ids:
        item = item_map.get(rid)
        if item:
            data.append(_output_to_dict(item))

    return page_response(data, total, page, page_size)


def _clean_param(value, default=None):
    """Clean parameter - convert empty strings to None."""
    if value == "" or value is None:
        return default
    return value


@router.get("")
async def list_outputs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    instance_id: Optional[int] = Query(default=None),
    agent_id: Optional[int] = Query(default=None),
    output_type: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Output).options(
        selectinload(Output.instance),
        selectinload(Output.agent),
        selectinload(Output.tags),
    )
    count_query = select(func.count(Output.id))

    if instance_id:
        query = query.where(Output.instance_id == instance_id)
        count_query = count_query.where(Output.instance_id == instance_id)
    if agent_id:
        query = query.where(Output.agent_id == agent_id)
        count_query = count_query.where(Output.agent_id == agent_id)
    if output_type:
        query = query.where(Output.output_type == output_type)
        count_query = count_query.where(Output.output_type == output_type)
    if keyword:
        query = query.where(Output.title.contains(keyword) | Output.content.contains(keyword))
        count_query = count_query.where(Output.title.contains(keyword) | Output.content.contains(keyword))
    if status:
        query = query.where(Output.status == status)
        count_query = count_query.where(Output.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Output.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = [_output_to_dict(item) for item in items]

    return page_response(data, total, page, page_size)


@router.get("/{output_id}")
async def get_output(output_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Output).options(
            selectinload(Output.instance),
            selectinload(Output.agent),
            selectinload(Output.tags),
        ).where(Output.id == output_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return error("输出不存在", 404)
    return success(_output_to_dict(item))


@router.post("")
async def create_output(data: OutputCreate, db: AsyncSession = Depends(get_db)):
    output = Output(**data.model_dump())
    # Build search_content for FTS
    output.search_content = f"{output.title} {output.summary or ''} {output.content or ''}"
    db.add(output)
    await db.flush()
    await db.refresh(output)
    return success(_output_to_dict(output), "创建成功")


@router.post("/{output_id}/favorite")
async def toggle_favorite(output_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Output).where(Output.id == output_id))
    output = result.scalar_one_or_none()
    if not output:
        return error("输出不存在", 404)
    output.is_favorite = not output.is_favorite
    await db.flush()
    return success({"id": output_id, "is_favorite": output.is_favorite})


@router.post("/{output_id}/tags")
async def add_tag(output_id: int, data: TagCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Output).where(Output.id == output_id))
    output = result.scalar_one_or_none()
    if not output:
        return error("输出不存在", 404)

    tag = OutputTag(output_id=output_id, tag_name=data.tag_name)
    db.add(tag)
    await db.flush()
    return success({"tag_name": data.tag_name}, "标签添加成功")


@router.delete("/{output_id}/tags/{tag_id}")
async def remove_tag(output_id: int, tag_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OutputTag).where(OutputTag.id == tag_id, OutputTag.output_id == output_id))
    tag = result.scalar_one_or_none()
    if not tag:
        return error("标签不存在", 404)
    await db.delete(tag)
    return success(None, "标签删除成功")


@router.get("/{output_id}/export")
async def export_output(output_id: int, format: str = "json", db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Output).options(selectinload(Output.tags)).where(Output.id == output_id)
    )
    output = result.scalar_one_or_none()
    if not output:
        return error("输出不存在", 404)

    if format == "json":
        return success(OutputOut.model_validate(output).model_dump())
    elif format == "markdown":
        md = f"# {output.title}\n\n"
        md += f"**类型**: {output.output_type}\n"
        md += f"**状态**: {output.status}\n"
        md += f"**时间**: {output.created_at}\n\n"
        md += f"## 内容\n\n{output.content or output.raw_content or ''}\n"
        return success({"content": md, "filename": f"{output.title}.md"})
    else:
        return error("不支持的导出格式")


# ==================== Batch Operations ====================

@router.post("/batch-delete")
async def batch_delete_outputs(data: BatchIds, db: AsyncSession = Depends(get_db)):
    """Delete multiple outputs at once."""
    if not data.ids:
        return error("请选择要删除的输出", 400)
    if len(data.ids) > 100:
        return error("单次最多删除100条", 400)

    result = await db.execute(select(Output).where(Output.id.in_(data.ids)))
    items = result.scalars().all()

    deleted = 0
    for item in items:
        await db.delete(item)
        deleted += 1

    return success({"deleted": deleted}, f"成功删除 {deleted} 条输出")


@router.post("/batch-export")
async def batch_export_outputs(data: BatchIds, db: AsyncSession = Depends(get_db)):
    """Export multiple outputs as JSON array."""
    if not data.ids:
        return error("请选择要导出的输出", 400)

    result = await db.execute(
        select(Output).options(
            selectinload(Output.instance),
            selectinload(Output.agent),
            selectinload(Output.tags),
        ).where(Output.id.in_(data.ids))
    )
    items = result.scalars().all()
    data_list = [_output_to_dict(item) for item in items]
    return success(data_list, f"导出 {len(data_list)} 条输出")
