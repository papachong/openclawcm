"""
Multi-agent collaboration model with visual flow editor support.
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class Collaboration(Base, TimestampMixin):
    __tablename__ = "collaborations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="协作流程名称")
    type = Column(String(50), nullable=False, default="chain", comment="类型: chain/parallel/conditional/custom")
    execution_mode = Column(String(30), default="sequential", comment="执行模式: sequential/parallel/conditional")
    agent_ids = Column(Text, nullable=True, comment="参与Agent ID列表(JSON) - 兼容旧数据")
    routing_rules = Column(Text, nullable=True, comment="消息路由规则(JSON)")
    status = Column(String(20), default="inactive", comment="状态: active/inactive/running/error")
    description = Column(Text, nullable=True, comment="描述")
    is_template = Column(Integer, default=0, comment="是否为模板")
    template_name = Column(String(200), nullable=True, comment="模板名称")
    viewport_zoom = Column(Float, default=1.0, comment="画布缩放比例")
    viewport_x = Column(Float, default=0.0, comment="画布视口X偏移")
    viewport_y = Column(Float, default=0.0, comment="画布视口Y偏移")

    # Relationships
    nodes = relationship("CollaborationNode", back_populates="collaboration", cascade="all, delete-orphan")
    edges = relationship("CollaborationEdge", back_populates="collaboration", cascade="all, delete-orphan")
    runs = relationship("CollaborationRun", back_populates="collaboration", cascade="all, delete-orphan")


class CollaborationNode(Base, TimestampMixin):
    """DAG node - represents an Agent, start/end point, or condition in the flow."""
    __tablename__ = "collaboration_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collaboration_id = Column(Integer, ForeignKey("collaborations.id", ondelete="CASCADE"), nullable=False)
    node_type = Column(String(30), nullable=False, default="agent", comment="节点类型: agent/start/end/condition/parallel_gateway")
    label = Column(String(200), nullable=True, comment="节点显示名称")
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, comment="关联Agent ID")
    config_json = Column(Text, nullable=True, comment="节点配置(JSON): 条件表达式、超时等")
    position_x = Column(Float, default=0.0, comment="画布X坐标")
    position_y = Column(Float, default=0.0, comment="画布Y坐标")
    width = Column(Integer, default=180, comment="节点宽度")
    height = Column(Integer, default=40, comment="节点高度")

    # Relationships
    collaboration = relationship("Collaboration", back_populates="nodes")
    agent = relationship("Agent")


class CollaborationEdge(Base, TimestampMixin):
    """DAG edge - connection between two nodes, optionally with a condition."""
    __tablename__ = "collaboration_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collaboration_id = Column(Integer, ForeignKey("collaborations.id", ondelete="CASCADE"), nullable=False)
    source_node_id = Column(Integer, ForeignKey("collaboration_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("collaboration_nodes.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(200), nullable=True, comment="边标签 / 条件名称")
    condition_json = Column(Text, nullable=True, comment="条件路由表达式(JSON)")
    edge_type = Column(String(20), default="default", comment="边类型: default/success/failure/conditional")

    # Relationships
    collaboration = relationship("Collaboration", back_populates="edges")
    source_node = relationship("CollaborationNode", foreign_keys=[source_node_id])
    target_node = relationship("CollaborationNode", foreign_keys=[target_node_id])


class CollaborationRun(Base, TimestampMixin):
    """Tracks execution runs of a collaboration workflow."""
    __tablename__ = "collaboration_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collaboration_id = Column(Integer, ForeignKey("collaborations.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(Integer, ForeignKey("instances.id", ondelete="SET NULL"), nullable=True, comment="执行的实例ID")
    status = Column(String(20), default="pending", comment="状态: pending/running/completed/failed/cancelled")
    current_node_id = Column(Integer, ForeignKey("collaboration_nodes.id", ondelete="SET NULL"), nullable=True, comment="当前执行节点")
    input_message = Column(Text, nullable=True, comment="输入消息")
    output_summary = Column(Text, nullable=True, comment="输出摘要")
    error_message = Column(Text, nullable=True, comment="错误信息")
    started_at = Column(String(30), nullable=True, comment="开始时间")
    completed_at = Column(String(30), nullable=True, comment="完成时间")
    session_keys_json = Column(Text, nullable=True, comment="会话键列表(JSON)")
    token_usage_json = Column(Text, nullable=True, comment="Token使用统计(JSON)")

    # Relationships
    collaboration = relationship("Collaboration", back_populates="runs")
