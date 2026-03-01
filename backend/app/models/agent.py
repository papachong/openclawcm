"""
Agent model with memory configuration support.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="Agent名称")
    instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False, comment="所属实例ID")
    role = Column(String(200), nullable=True, comment="角色")
    model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=True, comment="使用的模型配置ID")
    system_prompt = Column(Text, nullable=True, comment="System Prompt")
    status = Column(String(20), default="stopped", comment="状态: running/stopped/error")
    description = Column(Text, nullable=True, comment="描述")
    skills_count = Column(Integer, default=0, comment="Skills数量")

    # ---- Memory Configuration ----
    memory_type = Column(String(30), default="buffer", comment="记忆类型: buffer/summary/buffer_summary/none")
    max_history_messages = Column(Integer, default=20, comment="最大历史消息数(buffer模式)")
    max_token_limit = Column(Integer, default=4000, comment="最大token数限制")
    summary_model_id = Column(Integer, ForeignKey("model_configs.id"), nullable=True, comment="摘要用模型配置ID")
    memory_persistence = Column(Integer, default=1, comment="是否持久化记忆(0=否,1=是)")
    auto_cleanup_days = Column(Integer, default=0, comment="自动清理天数(0=不清理)")

    # Relationships
    instance = relationship("Instance", foreign_keys=[instance_id])
    model_config = relationship("ModelConfig", foreign_keys=[model_config_id])
    summary_model = relationship("ModelConfig", foreign_keys=[summary_model_id])
    skills = relationship("AgentSkill", back_populates="agent", cascade="all, delete-orphan")
    memory_pool_bindings = relationship("AgentMemoryPoolBinding", back_populates="agent", cascade="all, delete-orphan")


class AgentSkill(Base, TimestampMixin):
    """Agent-Skill binding (many-to-many)."""
    __tablename__ = "agent_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)

    agent = relationship("Agent", back_populates="skills")
    skill = relationship("Skill")


class SharedMemoryPool(Base, TimestampMixin):
    """Shared memory pool for multi-agent collaboration."""
    __tablename__ = "shared_memory_pools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="记忆池名称")
    description = Column(Text, nullable=True, comment="描述")
    memory_type = Column(String(30), default="buffer", comment="记忆类型: buffer/summary/buffer_summary")
    max_history_messages = Column(Integer, default=50, comment="最大历史消息数")
    max_token_limit = Column(Integer, default=8000, comment="最大token数限制")
    status = Column(String(20), default="active", comment="状态: active/inactive")
    collaboration_id = Column(Integer, ForeignKey("collaborations.id"), nullable=True, comment="关联协作流程ID")
    # Runtime stats (updated by OpenClaw instances)
    message_count = Column(Integer, default=0, comment="当前消息条数")
    total_tokens = Column(Integer, default=0, comment="总token数")

    # Relationships
    agent_bindings = relationship("AgentMemoryPoolBinding", back_populates="pool", cascade="all, delete-orphan")


class AgentMemoryPoolBinding(Base, TimestampMixin):
    """Binding between Agent and SharedMemoryPool."""
    __tablename__ = "agent_memory_pool_bindings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    pool_id = Column(Integer, ForeignKey("shared_memory_pools.id", ondelete="CASCADE"), nullable=False)
    permission = Column(String(20), default="readwrite", comment="权限: read/write/readwrite")

    agent = relationship("Agent", back_populates="memory_pool_bindings")
    pool = relationship("SharedMemoryPool", back_populates="agent_bindings")
