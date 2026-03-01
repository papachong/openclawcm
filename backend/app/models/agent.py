"""
Agent model.
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

    # Relationships
    instance = relationship("Instance", foreign_keys=[instance_id])
    model_config = relationship("ModelConfig", foreign_keys=[model_config_id])
    skills = relationship("AgentSkill", back_populates="agent")


class AgentSkill(Base, TimestampMixin):
    """Agent-Skill binding (many-to-many)."""
    __tablename__ = "agent_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)

    agent = relationship("Agent", back_populates="skills")
    skill = relationship("Skill")
