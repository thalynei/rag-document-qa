"""Database connection and session management."""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

# Database path - configurable via environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/rag_qa.db")

# Ensure data directory exists for SQLite
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not db_path.startswith(":"):
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables and migrate existing schema."""
    Base.metadata.create_all(bind=engine)

    # 迁移：为已有表添加新列（SQLite 不支持 IF NOT EXISTS，用 try/except）
    _migrate_schema()


def _migrate_schema() -> None:
    """为已有数据库添加新列（幂等操作）"""
    import logging
    from sqlalchemy import text

    logger = logging.getLogger(__name__)

    migrations = [
        # (table, column, column_definition)
        ("users", "avatar_path", "ALTER TABLE users ADD COLUMN avatar_path VARCHAR(500)"),
        ("messages", "model_name", "ALTER TABLE messages ADD COLUMN model_name VARCHAR(100)"),
    ]

    with engine.connect() as conn:
        for table, column, ddl in migrations:
            try:
                conn.execute(text(ddl))
                conn.commit()
                logger.info(f"迁移: {table}.{column} 列已添加")
            except Exception:
                # 列已存在，忽略
                conn.rollback()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
