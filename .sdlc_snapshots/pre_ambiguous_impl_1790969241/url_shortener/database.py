"""
SQLAlchemy Database Layer for URL Shortener & Analytics.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from .config import settings

Base = declarative_base()


class URLRecord(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_code = Column(String(32), unique=True, nullable=False, index=True)
    original_url = Column(Text, nullable=False)
    custom_alias = Column(String(64), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    click_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("idx_urls_active_code", "short_code", "is_active"),
    )


class ClickEvent(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_code = Column(String(32), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_hash = Column(String(64), nullable=False)
    referrer = Column(String(255), nullable=True)
    user_agent = Column(String(255), nullable=True)
    device_type = Column(String(32), default="desktop", nullable=False)
    country = Column(String(64), default="United States", nullable=False)

    __table_args__ = (
        Index("idx_clicks_code_time", "short_code", "timestamp"),
    )


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
