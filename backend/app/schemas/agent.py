"""
Agent schemas.
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class AgentCreate(BaseModel):
    name: str
    instance_id: int
    role: Optional[str] = None
    model_config_id: Optional[int] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    instance_id: Optional[int] = None
    role: Optional[str] = None
    model_config_id: Optional[int] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None


class AgentOut(BaseModel):
    id: int
    name: str
    instance_id: int
    instance_name: Optional[str] = None
    role: Optional[str] = None
    model_config_id: Optional[int] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    status: str = "stopped"
    description: Optional[str] = None
    skills_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
