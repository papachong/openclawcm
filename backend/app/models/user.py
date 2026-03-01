"""
User and system models.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(500), nullable=False, comment="密码哈希")
    display_name = Column(String(200), nullable=True, comment="显示名称")
    role = Column(String(20), default="operator", comment="角色: admin/operator/viewer")
    is_active = Column(Boolean, default=True, comment="是否激活")
    email = Column(String(200), nullable=True, comment="邮箱")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, comment="操作用户ID")
    username = Column(String(100), nullable=True, comment="操作用户名")
    action = Column(String(50), nullable=False, comment="操作类型")
    resource_type = Column(String(50), nullable=True, comment="资源类型")
    resource_id = Column(Integer, nullable=True, comment="资源ID")
    detail = Column(Text, nullable=True, comment="详细信息")
    ip_address = Column(String(50), nullable=True, comment="IP地址")


class SystemSetting(Base, TimestampMixin):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(200), unique=True, nullable=False, comment="配置键")
    value = Column(Text, nullable=True, comment="配置值")
    description = Column(String(500), nullable=True, comment="说明")
