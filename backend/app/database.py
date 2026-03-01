"""
Database engine & session configuration.
Supports SQLite and MySQL via DATABASE_URL.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    # SQLite specific: enable WAL mode for better concurrency
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency: yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (for development). Use Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create FTS5 virtual table for full-text search on outputs (SQLite only)
    if "sqlite" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.execute(
                __import__("sqlalchemy").text(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS outputs_fts USING fts5(
                        title,
                        summary,
                        content,
                        content='outputs',
                        content_rowid='id'
                    )
                    """
                )
            )
            # Create triggers to keep FTS in sync
            for trigger_sql in [
                """
                CREATE TRIGGER IF NOT EXISTS outputs_ai AFTER INSERT ON outputs BEGIN
                    INSERT INTO outputs_fts(rowid, title, summary, content)
                    VALUES (new.id, new.title, new.summary, new.content);
                END;
                """,
                """
                CREATE TRIGGER IF NOT EXISTS outputs_ad AFTER DELETE ON outputs BEGIN
                    INSERT INTO outputs_fts(outputs_fts, rowid, title, summary, content)
                    VALUES ('delete', old.id, old.title, old.summary, old.content);
                END;
                """,
                """
                CREATE TRIGGER IF NOT EXISTS outputs_au AFTER UPDATE ON outputs BEGIN
                    INSERT INTO outputs_fts(outputs_fts, rowid, title, summary, content)
                    VALUES ('delete', old.id, old.title, old.summary, old.content);
                    INSERT INTO outputs_fts(rowid, title, summary, content)
                    VALUES (new.id, new.title, new.summary, new.content);
                END;
                """,
            ]:
                await conn.execute(__import__("sqlalchemy").text(trigger_sql))
