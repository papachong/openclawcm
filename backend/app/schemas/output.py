"""
Output schemas.
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class OutputCreate(BaseModel):
    instance_id: int
    agent_id: int
    task_id: Optional[str] = None
    output_type: str
    content_type: str = "text/plain"
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    raw_content: Optional[str] = None
    metadata_json: Optional[str] = None
    status: str = "success"
    token_usage: Optional[int] = None


class OutputOut(BaseModel):
    id: int
    instance_id: int
    instance_name: Optional[str] = None
    agent_id: int
    agent_name: Optional[str] = None
    task_id: Optional[str] = None
    output_type: str
    content_type: str = "text/plain"
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    raw_content: Optional[str] = None
    metadata_json: Optional[str] = None
    status: str = "success"
    is_favorite: bool = False
    token_usage: Optional[int] = None
    tags: List[str] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    tag_name: str
