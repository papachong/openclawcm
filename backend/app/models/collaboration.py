"""
Multi-agent collaboration model.
"""
from sqlalchemy import Column, Integer, String, Text
from app.database import Base
from app.models.base import TimestampMixin


class Collaboration(Base, TimestampMixin):
    __tablename__ = "collaborations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="协作流程名称")
    type = Column(String(50), nullable=False, default="chain", comment="类型: chain/parallel/conditional/custom")
    agent_ids = Column(Text, nullable=True, comment="参与Agent ID列表(JSON)")
    routing_rules = Column(Text, nullable=True, comment="消息路由规则(JSON)")
    status = Column(String(20), default="inactive", comment="状态: active/inactive")
    description = Column(Text, nullable=True, comment="描述")
    is_template = Column(Integer, default=0, comment="是否为模板")
    template_name = Column(String(200), nullable=True, comment="模板名称")
