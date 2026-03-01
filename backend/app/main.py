"""
FastAPI application entry point.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import select

from app.config import settings
from app.database import init_db, async_session
from app.api.v1.router import api_router
from app.middleware.audit import AuditMiddleware


async def ensure_default_admin():
    """Create default admin user if no users exist."""
    from app.models.user import User
    from app.utils.auth import get_password_hash

    async with async_session() as session:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is None:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                display_name="系统管理员",
                role="admin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin user created (admin / admin123)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup & shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Ensure data directories exist
    os.makedirs("./data/outputs", exist_ok=True)
    # Initialize database tables
    await init_db()
    logger.info("Database initialized")
    # Create default admin
    await ensure_default_admin()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="OpenClaw Configuration Manager - Multi-instance management platform",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit logging middleware
app.add_middleware(AuditMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
