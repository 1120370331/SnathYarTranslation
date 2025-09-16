"""
Translation Entry Model

Represents a Chinese-Shathyar translation pair stored in the system database.
Based on data-model.md specifications.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Integer, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from ..utils.normalize import normalize_text

Base = declarative_base()


class TranslationEntry(Base):
    """
    User-generated translation pairs with AI generation and user confirmation tracking
    
    Attributes:
        id: Primary key (UUID string)
        source_text: Original text input (max 500 chars)
        translated_text: Generated or confirmed translation (max 1000 chars)
        source_language: Language direction ("chinese" or "shathyar")
        is_ai_generated: Boolean flag indicating AI vs dictionary source
        is_user_confirmed: Boolean flag for user-edited AI translations
        confidence_score: AI translation confidence (0-1, nullable)
        created_at: Timestamp of creation
        updated_at: Timestamp of last modification
        usage_count: Number of times served (analytics)
    """
    
    __tablename__ = "translation_entries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_text = Column(String(500), nullable=False)
    translated_text = Column(String(1000), nullable=False)
    source_language = Column(String(10), nullable=False)  # "chinese" or "shathyar"
    is_ai_generated = Column(Boolean, nullable=False, default=True)
    is_user_confirmed = Column(Boolean, nullable=False, default=False)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00-1.00
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    usage_count = Column(Integer, default=0)
    # Normalized columns for fast fuzzy/forgiving lookups
    norm_source_text = Column(String(1100), nullable=True, index=True)
    norm_translated_text = Column(String(1100), nullable=True, index=True)
    
    def __init__(self, source_text: str, translated_text: str, source_language: str,
                 is_ai_generated: bool = True, is_user_confirmed: bool = False,
                 confidence_score: float = None):
        """Initialize translation entry with validation"""
        
        # Validation rules from FR-012
        if len(source_text) > 500:
            raise ValueError("Source text exceeds 500 character limit")
        if len(translated_text) > 1000:
            raise ValueError("Translated text exceeds 1000 character limit")
        if source_language not in ["chinese", "shathyar"]:
            raise ValueError("Source language must be 'chinese' or 'shathyar'")
        if confidence_score is not None and not (0 <= confidence_score <= 1):
            raise ValueError("Confidence score must be between 0 and 1")
            
        self.source_text = source_text
        self.translated_text = translated_text
        self.source_language = source_language
        self.is_ai_generated = is_ai_generated
        self.is_user_confirmed = is_user_confirmed
        self.confidence_score = confidence_score
        self.usage_count = 0
        # Set normalized fields
        self.norm_source_text = normalize_text(self.source_text)
        self.norm_translated_text = normalize_text(self.translated_text)
    
    def confirm_user_edit(self, edited_translation: str) -> None:
        """Mark translation as user-confirmed with edited content"""
        if len(edited_translation) > 1000:
            raise ValueError("Edited translation exceeds 1000 character limit")
            
        self.translated_text = edited_translation
        self.is_user_confirmed = True
        self.updated_at = datetime.utcnow()
        self.norm_translated_text = normalize_text(self.translated_text)
    
    def increment_usage(self) -> None:
        """Increment usage counter for analytics"""
        self.usage_count += 1
    
    def get_state(self) -> str:
        """Get current translation state for UI display"""
        if not self.is_ai_generated:
            return "dictionary"
        elif not self.is_user_confirmed:
            return "ai_draft"
        else:
            return "user_confirmed"
    
    def can_edit(self) -> bool:
        """Check if this translation can be edited by user"""
        return self.is_ai_generated and not self.is_user_confirmed
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "source_text": self.source_text,
            "translated_text": self.translated_text,
            "source_language": self.source_language,
            "is_ai_generated": self.is_ai_generated,
            "is_user_confirmed": self.is_user_confirmed,
            "confidence_score": float(self.confidence_score) if self.confidence_score else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "usage_count": self.usage_count,
            "can_edit": self.can_edit(),
            "state": self.get_state()
        }
    
    def __repr__(self) -> str:
        return f"<TranslationEntry(id={self.id}, source='{self.source_text[:20]}...', language={self.source_language})>"

# Explicit indices (composite ones could be added for source_language + norm fields)
Index('idx_translation_norm_source', TranslationEntry.norm_source_text)
Index('idx_translation_norm_translated', TranslationEntry.norm_translated_text)
