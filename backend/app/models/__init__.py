"""
Import all models so they are registered with Base.metadata.
"""
from app.models.instance import Instance
from app.models.model_config import ModelProvider, ModelConfig
from app.models.agent import Agent, AgentSkill
from app.models.skill import Skill
from app.models.output import Output, OutputTag, OutputAttachment
from app.models.collaboration import Collaboration
from app.models.user import User, AuditLog, SystemSetting

__all__ = [
    "Instance",
    "ModelProvider", "ModelConfig",
    "Agent", "AgentSkill",
    "Skill",
    "Output", "OutputTag", "OutputAttachment",
    "Collaboration",
    "User", "AuditLog", "SystemSetting",
]