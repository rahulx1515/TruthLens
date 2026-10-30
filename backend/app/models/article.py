"""
Article Database Model
Stores raw or extracted news articles analyzed in the system.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    url = Column(String(2048), nullable=True, index=True)
    domain = Column(String(255), nullable=True, index=True)
    author = Column(String(255), nullable=True)
    published_date = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    analyses = relationship("Analysis", back_populates="article", cascade="all, delete-orphan")

