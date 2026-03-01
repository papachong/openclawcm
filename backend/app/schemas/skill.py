"""
Skill schemas.
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class SkillCreate(BaseModel):
    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    config_json: Optional[str] = None
    package_path: Optional[str] = None
    dependencies: Optional[str] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[str] = None
    package_path: Optional[str] = None
    dependencies: Optional[str] = None


class SkillOut(BaseModel):
    id: int
    name: str
    version: str = "1.0.0"
    status: str = "available"
    description: Optional[str] = None
    config_json: Optional[str] = None
    package_path: Optional[str] = None
    dependencies: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
