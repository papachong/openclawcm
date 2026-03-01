"""
Output model - unified output schema for all agent outputs.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
import enum


class OutputType(str, enum.Enum):
    CODE = "CODE"
    DOCUMENT = "DOCUMENT"
    DATA = "DATA"
    CONVERSATION = "CONVERSATION"
    FILE = "FILE"
    COMMAND = "COMMAND"
    STRUCTURED = "STRUCTURED"


class Output(Base, TimestampMixin):
    __tablename__ = "outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False, comment="来源实例ID")
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, comment="产出Agent ID")
    task_id = Column(String(200), nullable=True, comment="关联任务ID")
    output_type = Column(String(20), nullable=False, comment="输出类型")
    content_type = Column(String(100), default="text/plain", comment="MIME类型")
    title = Column(String(500), nullable=False, comment="输出标题")
    summary = Column(Text, nullable=True, comment="摘要")
    content = Column(Text, nullable=True, comment="结构化内容(JSON)")
    raw_content = Column(Text, nullable=True, comment="原始内容")
    metadata_json = Column(Text, nullable=True, comment="元数据(JSON): 执行耗时、Token用量等")
    status = Column(String(20), default="success", comment="状态: success/failed/partial")
    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    token_usage = Column(Integer, nullable=True, comment="Token用量")

    # For FTS
    search_content = Column(Text, nullable=True, comment="全文搜索用的拼接内容")

    # Relationships
    instance = relationship("Instance")
    agent = relationship("Agent")
    tags = relationship("OutputTag", back_populates="output")
    attachments = relationship("OutputAttachment", back_populates="output")


class OutputTag(Base, TimestampMixin):
    __tablename__ = "output_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    output_id = Column(Integer, ForeignKey("outputs.id"), nullable=False)
    tag_name = Column(String(100), nullable=False, comment="标签名")

    output = relationship("Output", back_populates="tags")


class OutputAttachment(Base, TimestampMixin):
    __tablename__ = "output_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    output_id = Column(Integer, ForeignKey("outputs.id"), nullable=False)
    file_name = Column(String(500), nullable=False, comment="文件名")
    file_path = Column(String(1000), nullable=False, comment="文件路径")
    file_size = Column(Integer, nullable=True, comment="文件大小(bytes)")
    mime_type = Column(String(100), nullable=True, comment="MIME类型")

    output = relationship("Output", back_populates="attachments")
