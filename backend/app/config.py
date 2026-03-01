"""
Application configuration.
Supports SQLite (default) and MySQL via DATABASE_URL environment variable.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "OpenClawCM"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    # SQLite: sqlite+aiosqlite:///./data/openclawcm.db
    # MySQL:  mysql+aiomysql://user:pass@host:3306/openclawcm
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/openclawcm.db"
    DATABASE_ECHO: bool = False

    # JWT Auth
    SECRET_KEY: str = "openclawcm-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # File storage for outputs
    OUTPUT_STORAGE_PATH: str = "./data/outputs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
