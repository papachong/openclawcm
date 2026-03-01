"""
Model configuration schemas.
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ProviderCreate(BaseModel):
    name: str
    api_type: str = "openai"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    description: Optional[str] = None


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    api_type: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    description: Optional[str] = None


class ProviderOut(BaseModel):
    id: int
    name: str
    api_type: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    status: str = "active"
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelConfigCreate(BaseModel):
    name: str
    provider_id: Optional[int] = None
    model_name: str
    scope: str = "global"
    instance_id: Optional[int] = None
    agent_id: Optional[int] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    extra_params: Optional[str] = None
    description: Optional[str] = None
    is_default: int = 0


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider_id: Optional[int] = None
    model_name: Optional[str] = None
    scope: Optional[str] = None
    instance_id: Optional[int] = None
    agent_id: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    extra_params: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[int] = None


class ModelConfigOut(BaseModel):
    id: int
    name: str
    provider_id: Optional[int] = None
    provider_name: Optional[str] = None
    model_name: str
    scope: str
    instance_id: Optional[int] = None
    agent_id: Optional[int] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    extra_params: Optional[str] = None
    description: Optional[str] = None
    is_default: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
