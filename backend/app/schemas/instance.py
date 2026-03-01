"""
Instance schemas.
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class InstanceCreate(BaseModel):
    name: str
    url: str
    api_key: Optional[str] = None
    group_name: Optional[str] = None
    description: Optional[str] = None


class InstanceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    api_key: Optional[str] = None
    group_name: Optional[str] = None
    description: Optional[str] = None


class InstanceOut(BaseModel):
    id: int
    name: str
    url: str
    api_key: Optional[str] = None
    status: str = "unknown"
    group_name: Optional[str] = None
    description: Optional[str] = None
    agent_count: int = 0
    last_heartbeat: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
