"""
Agent schemas with memory configuration support.
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


# ==================== Agent ====================
class AgentCreate(BaseModel):
    name: str
    instance_id: int
    role: Optional[str] = None
    model_config_id: Optional[int] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    # Memory config
    memory_type: str = "buffer"
    max_history_messages: int = 20
    max_token_limit: int = 4000
    summary_model_id: Optional[int] = None
    memory_persistence: int = 1
    auto_cleanup_days: int = 0


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    instance_id: Optional[int] = None
    role: Optional[str] = None
    model_config_id: Optional[int] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    # Memory config
    memory_type: Optional[str] = None
    max_history_messages: Optional[int] = None
    max_token_limit: Optional[int] = None
    summary_model_id: Optional[int] = None
    memory_persistence: Optional[int] = None
    auto_cleanup_days: Optional[int] = None


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
    # Memory config
    memory_type: str = "buffer"
    max_history_messages: int = 20
    max_token_limit: int = 4000
    summary_model_id: Optional[int] = None
    summary_model_name: Optional[str] = None
    memory_persistence: int = 1
    auto_cleanup_days: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Agent Skills Binding ====================
class AgentSkillBind(BaseModel):
    skill_id: int


class AgentSkillOut(BaseModel):
    id: int
    agent_id: int
    skill_id: int
    skill_name: Optional[str] = None
    skill_version: Optional[str] = None
    skill_status: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Shared Memory Pool ====================
class SharedMemoryPoolCreate(BaseModel):
    name: str
    description: Optional[str] = None
    memory_type: str = "buffer"
    max_history_messages: int = 50
    max_token_limit: int = 8000
    collaboration_id: Optional[int] = None


class SharedMemoryPoolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    memory_type: Optional[str] = None
    max_history_messages: Optional[int] = None
    max_token_limit: Optional[int] = None
    status: Optional[str] = None
    collaboration_id: Optional[int] = None


class SharedMemoryPoolOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    memory_type: str = "buffer"
    max_history_messages: int = 50
    max_token_limit: int = 8000
    status: str = "active"
    collaboration_id: Optional[int] = None
    message_count: int = 0
    total_tokens: int = 0
    agent_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PoolAgentBind(BaseModel):
    agent_id: int
    permission: str = "readwrite"


class PoolAgentBindingOut(BaseModel):
    id: int
    agent_id: int
    pool_id: int
    agent_name: Optional[str] = None
    permission: str = "readwrite"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
