"""
Collaboration schemas - including flow editor nodes & edges.
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


# ==================== Collaboration CRUD ====================
class CollaborationCreate(BaseModel):
    name: str
    type: str = "chain"
    execution_mode: str = "sequential"
    agent_ids: Optional[str] = None
    routing_rules: Optional[str] = None
    description: Optional[str] = None


class CollaborationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    execution_mode: Optional[str] = None
    agent_ids: Optional[str] = None
    routing_rules: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class CollaborationOut(BaseModel):
    id: int
    name: str
    type: str = "chain"
    execution_mode: str = "sequential"
    agent_ids: Optional[str] = None
    routing_rules: Optional[str] = None
    status: str = "inactive"
    description: Optional[str] = None
    is_template: int = 0
    template_name: Optional[str] = None
    agent_count: int = 0
    node_count: int = 0
    edge_count: int = 0
    viewport_zoom: float = 1.0
    viewport_x: float = 0.0
    viewport_y: float = 0.0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Node CRUD ====================
class NodeCreate(BaseModel):
    node_type: str = "agent"
    label: Optional[str] = None
    agent_id: Optional[int] = None
    config_json: Optional[str] = None
    position_x: float = 0.0
    position_y: float = 0.0
    width: int = 180
    height: int = 40


class NodeUpdate(BaseModel):
    node_type: Optional[str] = None
    label: Optional[str] = None
    agent_id: Optional[int] = None
    config_json: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None


class NodeOut(BaseModel):
    id: int
    collaboration_id: int
    node_type: str
    label: Optional[str] = None
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    config_json: Optional[str] = None
    position_x: float = 0.0
    position_y: float = 0.0
    width: int = 180
    height: int = 40
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Edge CRUD ====================
class EdgeCreate(BaseModel):
    source_node_id: int
    target_node_id: int
    label: Optional[str] = None
    condition_json: Optional[str] = None
    edge_type: str = "default"


class EdgeUpdate(BaseModel):
    label: Optional[str] = None
    condition_json: Optional[str] = None
    edge_type: Optional[str] = None


class EdgeOut(BaseModel):
    id: int
    collaboration_id: int
    source_node_id: int
    target_node_id: int
    label: Optional[str] = None
    condition_json: Optional[str] = None
    edge_type: str = "default"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Layout batch save ====================
class NodePosition(BaseModel):
    id: int
    position_x: float
    position_y: float


class LayoutSave(BaseModel):
    nodes: List[NodePosition] = []
    viewport_zoom: Optional[float] = None
    viewport_x: Optional[float] = None
    viewport_y: Optional[float] = None


# ==================== Full flow detail ====================
class FlowDetailOut(BaseModel):
    id: int
    name: str
    type: str
    execution_mode: str = "sequential"
    status: str = "inactive"
    description: Optional[str] = None
    viewport_zoom: float = 1.0
    viewport_x: float = 0.0
    viewport_y: float = 0.0
    nodes: List[NodeOut] = []
    edges: List[EdgeOut] = []
    created_at: Optional[datetime] = None
