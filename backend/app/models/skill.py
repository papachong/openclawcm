"""
Skill model.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base
from app.models.base import TimestampMixin


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(Integer, nullable=True, comment="关联实例ID")
    name = Column(String(200), nullable=False, comment="Skill名称")
    skill_key = Column(String(200), nullable=True, comment="Skill配置键")
    version = Column(String(50), default="1.0.0", comment="版本")
    status = Column(String(20), default="available", comment="状态: available/installed/unavailable")
    description = Column(Text, nullable=True, comment="描述")
    source = Column(String(100), nullable=True, comment="来源: openclaw-bundled/openclaw-workspace/etc")
    bundled = Column(Boolean, default=False, comment="是否内置")
    file_path = Column(String(500), nullable=True, comment="SKILL.md文件路径")
    base_dir = Column(String(500), nullable=True, comment="Skill目录")
    primary_env = Column(String(100), nullable=True, comment="主要环境变量")
    emoji = Column(String(10), nullable=True, comment="Emoji图标")
    homepage = Column(String(500), nullable=True, comment="主页URL")
    config_json = Column(Text, nullable=True, comment="配置参数(JSON)")
    package_path = Column(String(500), nullable=True, comment="包路径/URL")
    dependencies = Column(Text, nullable=True, comment="依赖项(JSON)")
