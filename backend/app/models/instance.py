"""
OpenClaw Instance model.
"""
from sqlalchemy import Column, Integer, String, Text, Enum
from app.database import Base
from app.models.base import TimestampMixin
import enum


class InstanceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Instance(Base, TimestampMixin):
    __tablename__ = "instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="实例名称")
    url = Column(String(500), nullable=False, comment="连接地址")
    api_key = Column(String(500), nullable=True, comment="API Key")
    status = Column(String(20), default=InstanceStatus.UNKNOWN.value, comment="状态")
    group_name = Column(String(100), nullable=True, comment="分组名称")
    description = Column(Text, nullable=True, comment="描述")
    agent_count = Column(Integer, default=0, comment="Agent数量")
    last_heartbeat = Column(String(50), nullable=True, comment="最后心跳时间")
