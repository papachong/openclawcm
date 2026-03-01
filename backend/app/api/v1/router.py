"""
API v1 router - aggregates all module routers.
"""
from fastapi import APIRouter, Depends

from app.api.v1 import instances, models, agents, skills, outputs, collaborations, dashboard, system, auth, memory_pools
from app.utils.auth import require_auth

api_router = APIRouter()

# Auth router - login endpoint is public, other endpoints handle auth internally
api_router.include_router(auth.router, prefix="/auth", tags=["认证管理"])

# All other routers require authentication
api_router.include_router(instances.router, prefix="/instances", tags=["实例管理"], dependencies=[Depends(require_auth)])
api_router.include_router(models.router, prefix="/models", tags=["模型管理"], dependencies=[Depends(require_auth)])
api_router.include_router(agents.router, prefix="/agents", tags=["Agent管理"], dependencies=[Depends(require_auth)])
api_router.include_router(skills.router, prefix="/skills", tags=["Skills管理"], dependencies=[Depends(require_auth)])
api_router.include_router(outputs.router, prefix="/outputs", tags=["输出管理"], dependencies=[Depends(require_auth)])
api_router.include_router(collaborations.router, prefix="/collaborations", tags=["协作配置"], dependencies=[Depends(require_auth)])
api_router.include_router(memory_pools.router, prefix="/memory-pools", tags=["共享记忆池"], dependencies=[Depends(require_auth)])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"], dependencies=[Depends(require_auth)])
api_router.include_router(system.router, prefix="/system", tags=["系统设置"], dependencies=[Depends(require_auth)])
