"""
Analysis Database Model
Stores credibility predictions, confidence scores, models used, and XAI metadata.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Classification details
    prediction = Column(String(50), nullable=False, index=True)  # "FAKE" or "REAL"
    label = Column(String(50), nullable=False)                    # "Likely Fake" or "Likely Authentic"
    confidence = Column(Float, nullable=False)
    prob_fake = Column(Float, nullable=False)
    prob_real = Column(Float, nullable=False)
    
    # Model tracking
    model_name = Column(String(100), nullable=False, default="Logistic Regression")
    model_version = Column(String(50), nullable=False, default="1.0.0")
    processing_time_ms = Column(Float, nullable=False, default=0.0)
    
    # Explainable AI Metadata (JSON-encoded string)
    explanation_json = Column(Text, nullable=True)
    
    # Metadata
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="analyses")
    article = relationship("Article", back_populates="analyses")

