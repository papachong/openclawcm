"""
Skill model.
"""
from sqlalchemy import Column, Integer, String, Text
from app.database import Base
from app.models.base import TimestampMixin


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="Skill名称")
    version = Column(String(50), default="1.0.0", comment="版本")
    status = Column(String(20), default="available", comment="状态: available/installed")
    description = Column(Text, nullable=True, comment="描述")
    config_json = Column(Text, nullable=True, comment="配置参数(JSON)")
    package_path = Column(String(500), nullable=True, comment="包路径/URL")
    dependencies = Column(Text, nullable=True, comment="依赖项(JSON)")
