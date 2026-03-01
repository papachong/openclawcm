"""
Multi-agent collaboration API endpoints - CRUD + flow editor + control.
"""
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models.collaboration import Collaboration, CollaborationNode, CollaborationEdge
from app.schemas.collaboration import (
    CollaborationCreate, CollaborationUpdate, CollaborationOut,
    NodeCreate, NodeUpdate, NodeOut,
    EdgeCreate, EdgeUpdate, EdgeOut,
    LayoutSave, FlowDetailOut,
)
from app.utils.response import success, error, page_response

router = APIRouter()


def _collab_to_dict(item) -> dict:
    loaded = item.__dict__
    nodes = loaded.get('nodes') or []
    edges = loaded.get('edges') or []
    agent_count = 0
    try:
        agent_list = json.loads(item.agent_ids) if item.agent_ids else []
        agent_count = len(agent_list)
    except Exception:
        pass
    # If nodes exist, count agent nodes instead
    agent_nodes = [n for n in nodes if n.node_type == 'agent']
    if agent_nodes:
        agent_count = len(agent_nodes)

    return {
        "id": item.id,
        "name": item.name,
        "type": item.type,
        "execution_mode": item.execution_mode or "sequential",
        "agent_ids": item.agent_ids,
        "routing_rules": item.routing_rules,
        "status": item.status,
        "description": item.description,
        "is_template": item.is_template,
        "template_name": item.template_name,
        "agent_count": agent_count,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "viewport_zoom": item.viewport_zoom or 1.0,
        "viewport_x": item.viewport_x or 0.0,
        "viewport_y": item.viewport_y or 0.0,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _node_to_dict(node) -> dict:
    loaded = node.__dict__
    agent = loaded.get('agent')
    return {
        "id": node.id,
        "collaboration_id": node.collaboration_id,
        "node_type": node.node_type,
        "label": node.label,
        "agent_id": node.agent_id,
        "agent_name": agent.name if agent else None,
        "config_json": node.config_json,
        "position_x": node.position_x or 0.0,
        "position_y": node.position_y or 0.0,
        "width": node.width or 180,
        "height": node.height or 40,
        "created_at": node.created_at.isoformat() if node.created_at else None,
    }


def _edge_to_dict(edge) -> dict:
    return {
        "id": edge.id,
        "collaboration_id": edge.collaboration_id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "label": edge.label,
        "condition_json": edge.condition_json,
        "edge_type": edge.edge_type or "default",
        "created_at": edge.created_at.isoformat() if edge.created_at else None,
    }


# ==================== Collaboration CRUD ====================

@router.get("")
async def list_collaborations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count(Collaboration.id)).where(Collaboration.is_template == 0)
    )
    total = count_result.scalar() or 0

    query = select(Collaboration).options(
        selectinload(Collaboration.nodes),
        selectinload(Collaboration.edges),
    ).where(Collaboration.is_template == 0)\
        .order_by(Collaboration.id.desc())\
        .offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    data = [_collab_to_dict(item) for item in items]
    return page_response(data, total, page, page_size)


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collaboration).where(Collaboration.is_template == 1))
    items = result.scalars().all()
    data = [_collab_to_dict(item) for item in items]
    return success(data)


@router.get("/{collab_id}")
async def get_collaboration(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collaboration).options(
            selectinload(Collaboration.nodes),
            selectinload(Collaboration.edges),
        ).where(Collaboration.id == collab_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return error("协作配置不存在", 404)
    return success(_collab_to_dict(item))


@router.post("")
async def create_collaboration(data: CollaborationCreate, db: AsyncSession = Depends(get_db)):
    collab = Collaboration(**data.model_dump())
    db.add(collab)
    await db.flush()
    await db.refresh(collab)
    return success(_collab_to_dict(collab), "创建成功")


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
    return success(_collab_to_dict(collab), "更新成功")


@router.delete("/{collab_id}")
async def delete_collaboration(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collaboration).where(Collaboration.id == collab_id))
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)
    await db.delete(collab)
    return success(None, "删除成功")


# ==================== Flow Control ====================

@router.post("/{collab_id}/start")
async def start_collaboration(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collaboration).options(selectinload(Collaboration.nodes)).where(Collaboration.id == collab_id)
    )
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)
    if collab.status == "running":
        return error("协作流程已在运行中", 400)
    # Validate: must have at least one agent node
    agent_nodes = [n for n in collab.nodes if n.node_type == 'agent']
    if not agent_nodes:
        return error("协作流程中没有Agent节点，无法启动", 400)
    collab.status = "running"
    await db.flush()
    return success({"id": collab.id, "status": "running"}, "协作流程已启动")


@router.post("/{collab_id}/stop")
async def stop_collaboration(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collaboration).where(Collaboration.id == collab_id))
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)
    collab.status = "inactive"
    await db.flush()
    return success({"id": collab.id, "status": "inactive"}, "协作流程已停止")


@router.post("/{collab_id}/save-template")
async def save_as_template(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collaboration).options(
            selectinload(Collaboration.nodes),
            selectinload(Collaboration.edges),
        ).where(Collaboration.id == collab_id)
    )
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)

    template = Collaboration(
        name=collab.name,
        type=collab.type,
        execution_mode=collab.execution_mode,
        agent_ids=collab.agent_ids,
        routing_rules=collab.routing_rules,
        description=collab.description,
        is_template=1,
        template_name=f"{collab.name}_模板",
    )
    db.add(template)
    await db.flush()

    # Copy nodes with old_id -> new_id mapping
    node_id_map = {}
    for node in (collab.nodes or []):
        new_node = CollaborationNode(
            collaboration_id=template.id,
            label=node.label,
            node_type=node.node_type,
            agent_id=node.agent_id,
            config_json=node.config_json,
            position_x=node.position_x,
            position_y=node.position_y,
            width=node.width,
            height=node.height,
        )
        db.add(new_node)
        await db.flush()
        node_id_map[node.id] = new_node.id

    # Copy edges
    for edge in (collab.edges or []):
        new_edge = CollaborationEdge(
            collaboration_id=template.id,
            source_node_id=node_id_map.get(edge.source_node_id, edge.source_node_id),
            target_node_id=node_id_map.get(edge.target_node_id, edge.target_node_id),
            edge_type=edge.edge_type,
            condition_json=edge.condition_json,
            label=edge.label,
        )
        db.add(new_edge)

    await db.flush()
    await db.refresh(template)
    return success(_collab_to_dict(template), "已保存为模板")


# ==================== Flow Detail (nodes + edges) ====================

@router.get("/{collab_id}/flow")
async def get_flow_detail(collab_id: int, db: AsyncSession = Depends(get_db)):
    """Get full flow with nodes and edges for the visual editor."""
    result = await db.execute(
        select(Collaboration).options(
            selectinload(Collaboration.nodes).selectinload(CollaborationNode.agent),
            selectinload(Collaboration.edges),
        ).where(Collaboration.id == collab_id)
    )
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)

    return success({
        "id": collab.id,
        "name": collab.name,
        "type": collab.type,
        "execution_mode": collab.execution_mode or "sequential",
        "status": collab.status,
        "description": collab.description,
        "viewport_zoom": collab.viewport_zoom or 1.0,
        "viewport_x": collab.viewport_x or 0.0,
        "viewport_y": collab.viewport_y or 0.0,
        "nodes": [_node_to_dict(n) for n in collab.nodes],
        "edges": [_edge_to_dict(e) for e in collab.edges],
        "created_at": collab.created_at.isoformat() if collab.created_at else None,
    })


# ==================== Nodes CRUD ====================

@router.get("/{collab_id}/nodes")
async def list_nodes(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CollaborationNode).options(
            selectinload(CollaborationNode.agent)
        ).where(CollaborationNode.collaboration_id == collab_id)
        .order_by(CollaborationNode.id)
    )
    nodes = result.scalars().all()
    return success([_node_to_dict(n) for n in nodes])


@router.post("/{collab_id}/nodes")
async def create_node(collab_id: int, data: NodeCreate, db: AsyncSession = Depends(get_db)):
    # Verify collaboration exists
    collab = await db.execute(select(Collaboration).where(Collaboration.id == collab_id))
    if not collab.scalar_one_or_none():
        return error("协作配置不存在", 404)

    node = CollaborationNode(collaboration_id=collab_id, **data.model_dump())
    # Auto-set label
    if not node.label:
        if node.node_type == 'start':
            node.label = '开始'
        elif node.node_type == 'end':
            node.label = '结束'
        elif node.node_type == 'condition':
            node.label = '条件'
        elif node.node_type == 'parallel_gateway':
            node.label = '并行网关'

    db.add(node)
    await db.flush()

    # Reload with agent relationship
    result = await db.execute(
        select(CollaborationNode).options(
            selectinload(CollaborationNode.agent)
        ).where(CollaborationNode.id == node.id)
    )
    node = result.scalar_one()
    return success(_node_to_dict(node), "节点创建成功")


@router.put("/{collab_id}/nodes/{node_id}")
async def update_node(collab_id: int, node_id: int, data: NodeUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CollaborationNode).where(
            CollaborationNode.id == node_id,
            CollaborationNode.collaboration_id == collab_id,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        return error("节点不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(node, key, value)

    await db.flush()

    # Reload with agent
    result = await db.execute(
        select(CollaborationNode).options(
            selectinload(CollaborationNode.agent)
        ).where(CollaborationNode.id == node.id)
    )
    node = result.scalar_one()
    return success(_node_to_dict(node), "节点更新成功")


@router.delete("/{collab_id}/nodes/{node_id}")
async def delete_node(collab_id: int, node_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CollaborationNode).where(
            CollaborationNode.id == node_id,
            CollaborationNode.collaboration_id == collab_id,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        return error("节点不存在", 404)

    # Also delete connected edges
    edges_result = await db.execute(
        select(CollaborationEdge).where(
            (CollaborationEdge.source_node_id == node_id) | (CollaborationEdge.target_node_id == node_id)
        )
    )
    for edge in edges_result.scalars().all():
        await db.delete(edge)

    await db.delete(node)
    return success(None, "节点删除成功")


# ==================== Edges CRUD ====================

@router.get("/{collab_id}/edges")
async def list_edges(collab_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CollaborationEdge)
        .where(CollaborationEdge.collaboration_id == collab_id)
        .order_by(CollaborationEdge.id)
    )
    edges = result.scalars().all()
    return success([_edge_to_dict(e) for e in edges])


@router.post("/{collab_id}/edges")
async def create_edge(collab_id: int, data: EdgeCreate, db: AsyncSession = Depends(get_db)):
    # Validate source and target exist in this collaboration
    for nid in [data.source_node_id, data.target_node_id]:
        r = await db.execute(
            select(CollaborationNode).where(
                CollaborationNode.id == nid,
                CollaborationNode.collaboration_id == collab_id,
            )
        )
        if not r.scalar_one_or_none():
            return error(f"节点 {nid} 不存在于此协作流程中", 400)

    edge = CollaborationEdge(collaboration_id=collab_id, **data.model_dump())
    db.add(edge)
    await db.flush()
    await db.refresh(edge)
    return success(_edge_to_dict(edge), "连线创建成功")


@router.put("/{collab_id}/edges/{edge_id}")
async def update_edge(collab_id: int, edge_id: int, data: EdgeUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CollaborationEdge).where(
            CollaborationEdge.id == edge_id,
            CollaborationEdge.collaboration_id == collab_id,
        )
    )
    edge = result.scalar_one_or_none()
    if not edge:
        return error("连线不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(edge, key, value)

    await db.flush()
    await db.refresh(edge)
    return success(_edge_to_dict(edge), "连线更新成功")


@router.delete("/{collab_id}/edges/{edge_id}")
async def delete_edge(collab_id: int, edge_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CollaborationEdge).where(
            CollaborationEdge.id == edge_id,
            CollaborationEdge.collaboration_id == collab_id,
        )
    )
    edge = result.scalar_one_or_none()
    if not edge:
        return error("连线不存在", 404)
    await db.delete(edge)
    return success(None, "连线删除成功")


# ==================== Layout Save ====================

@router.put("/{collab_id}/layout")
async def save_layout(collab_id: int, data: LayoutSave, db: AsyncSession = Depends(get_db)):
    """Batch update node positions and viewport settings."""
    result = await db.execute(select(Collaboration).where(Collaboration.id == collab_id))
    collab = result.scalar_one_or_none()
    if not collab:
        return error("协作配置不存在", 404)

    # Update viewport
    if data.viewport_zoom is not None:
        collab.viewport_zoom = data.viewport_zoom
    if data.viewport_x is not None:
        collab.viewport_x = data.viewport_x
    if data.viewport_y is not None:
        collab.viewport_y = data.viewport_y

    # Update node positions
    for pos in data.nodes:
        node_result = await db.execute(
            select(CollaborationNode).where(
                CollaborationNode.id == pos.id,
                CollaborationNode.collaboration_id == collab_id,
            )
        )
        node = node_result.scalar_one_or_none()
        if node:
            node.position_x = pos.position_x
            node.position_y = pos.position_y

    await db.flush()
    return success(None, "布局保存成功")
