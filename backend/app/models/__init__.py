"""
Import all models so they are registered with Base.metadata.
"""
from app.models.instance import Instance
from app.models.model_config import ModelProvider, ModelConfig
from app.models.agent import Agent, AgentSkill, SharedMemoryPool, AgentMemoryPoolBinding
from app.models.skill import Skill
from app.models.output import Output, OutputTag, OutputAttachment
from app.models.collaboration import Collaboration, CollaborationNode, CollaborationEdge
from app.models.user import User, AuditLog, SystemSetting

__all__ = [
    "Instance",
    "ModelProvider", "ModelConfig",
    "Agent", "AgentSkill", "SharedMemoryPool", "AgentMemoryPoolBinding",
    "Skill",
    "Output", "OutputTag", "OutputAttachment",
    "Collaboration", "CollaborationNode", "CollaborationEdge",
    "User", "AuditLog", "SystemSetting",
]