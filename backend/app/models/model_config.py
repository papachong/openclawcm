"""
Model provider and model configuration models.
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class ModelProvider(Base, TimestampMixin):
    """Model provider (OpenAI, Anthropic, etc.)"""
    __tablename__ = "model_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="供应商名称")
    api_type = Column(String(50), nullable=False, default="openai", comment="API类型: openai/anthropic/custom")
    base_url = Column(String(500), nullable=True, comment="API基础地址")
    api_key = Column(String(500), nullable=True, comment="API Key (加密存储)")
    status = Column(String(20), default="active", comment="状态")
    description = Column(Text, nullable=True, comment="描述")

    # Relationships
    model_configs = relationship("ModelConfig", back_populates="provider")


class ModelConfig(Base, TimestampMixin):
    """Model configuration (global / instance-level / agent-level)."""
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="配置名称")
    provider_id = Column(Integer, ForeignKey("model_providers.id"), nullable=True, comment="供应商ID")
    model_name = Column(String(200), nullable=False, comment="模型名称")
    scope = Column(String(20), nullable=False, default="global", comment="作用域: global/instance/agent")
    instance_id = Column(Integer, ForeignKey("instances.id"), nullable=True, comment="关联实例ID")
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, comment="关联Agent ID")
    temperature = Column(Float, default=0.7, comment="Temperature")
    max_tokens = Column(Integer, default=4096, comment="最大Token数")
    top_p = Column(Float, default=1.0, comment="Top P")
    extra_params = Column(Text, nullable=True, comment="额外参数(JSON)")
    description = Column(Text, nullable=True, comment="描述")
    is_default = Column(Integer, default=0, comment="是否默认配置")

    # Relationships
    provider = relationship("ModelProvider", back_populates="model_configs")
