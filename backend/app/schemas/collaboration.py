"""
Collaboration schemas.
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class CollaborationCreate(BaseModel):
    name: str
    type: str = "chain"
    agent_ids: Optional[str] = None
    routing_rules: Optional[str] = None
    description: Optional[str] = None


class CollaborationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    agent_ids: Optional[str] = None
    routing_rules: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class CollaborationOut(BaseModel):
    id: int
    name: str
    type: str = "chain"
    agent_ids: Optional[str] = None
    routing_rules: Optional[str] = None
    status: str = "inactive"
    description: Optional[str] = None
    is_template: int = 0
    template_name: Optional[str] = None
    agent_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
