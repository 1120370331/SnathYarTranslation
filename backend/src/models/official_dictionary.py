"""
Official Dictionary Model

Represents entries from the official shasiyaer.csv file (read-only reference data).
Based on data-model.md specifications.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy.sql import func
from .translation_entry import Base
from ..utils.normalize import normalize_text


class OfficialDictionary(Base):
    """
    Official Shathyar dictionary entries from shasiyaer.csv
    
    This is authoritative, read-only reference data from World of Warcraft.
    Used for exact matching before AI generation (FR-004).
    
    Attributes:
        id: Primary key (auto-increment)
        origin_cn: Original Chinese text (max 500 chars)
        shathyar: Shathyar translation (max 500 chars) 
        origin_en: Original English text (max 500 chars, optional)
        created_at: Import timestamp
        checksum: File integrity verification
    """
    
    __tablename__ = "official_dictionary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_cn = Column(String(500), nullable=False)
    shathyar = Column(String(500), nullable=False)
    origin_en = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    checksum = Column(String(64), nullable=True)  # SHA256 hash of source file
    # Normalized columns for efficient fuzzy/forgiving lookups
    norm_origin_cn = Column(String(600), nullable=True, index=True)
    norm_shathyar = Column(String(600), nullable=True, index=True)
    
    def __init__(self, origin_cn: str, shathyar: str, origin_en: str = None, checksum: str = None):
        """Initialize dictionary entry with validation"""
        
        if not origin_cn or not origin_cn.strip():
            raise ValueError("Origin Chinese text is required")
        if not shathyar or not shathyar.strip():
            raise ValueError("Shathyar text is required")
        if len(origin_cn) > 500:
            raise ValueError("Origin Chinese text exceeds 500 character limit")
        if len(shathyar) > 500:
            raise ValueError("Shathyar text exceeds 500 character limit")
        if origin_en and len(origin_en) > 500:
            raise ValueError("Origin English text exceeds 500 character limit")
            
        self.origin_cn = origin_cn.strip()
        self.shathyar = shathyar.strip()
        self.origin_en = origin_en.strip() if origin_en else None
        self.checksum = checksum
        # Set normalized fields
        self.norm_origin_cn = normalize_text(self.origin_cn)
        self.norm_shathyar = normalize_text(self.shathyar)
    
    def search_chinese(self, search_text: str) -> bool:
        """Check if this entry matches Chinese search text"""
        return search_text.lower() in self.origin_cn.lower()
    
    def search_shathyar(self, search_text: str) -> bool:
        """Check if this entry matches Shathyar search text"""
        return search_text.lower() in self.shathyar.lower()
    
    def exact_match_chinese(self, text: str) -> bool:
        """Check for exact Chinese match"""
        return self.origin_cn.lower() == text.lower().strip()
    
    def exact_match_shathyar(self, text: str) -> bool:
        """Check for exact Shathyar match"""
        return self.shathyar.lower() == text.lower().strip()
    
    def to_translation_entry(self) -> dict:
        """Convert to TranslationEntry format for consistent API responses"""
        return {
            "id": f"dict_{self.id}",
            "source_text": self.origin_cn,
            "translated_text": self.shathyar,
            "source_language": "chinese",
            "is_ai_generated": False,
            "is_user_confirmed": False,
            "confidence_score": 1.0,  # Dictionary entries have perfect confidence
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.created_at.isoformat() if self.created_at else None,
            "usage_count": 0,
            "can_edit": False,  # Dictionary entries cannot be edited
            "state": "dictionary"
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "origin_cn": self.origin_cn,
            "shathyar": self.shathyar,
            "origin_en": self.origin_en,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "checksum": self.checksum
        }
    
    @classmethod
    def get_reverse_lookup(cls, shathyar_text: str):
        """Get Chinese translation for Shathyar text (reverse lookup)"""
        # This method would be used by the service layer
        # Returns the Chinese text for a given Shathyar input
        pass
    
    def __repr__(self) -> str:
        return f"<OfficialDictionary(id={self.id}, cn='{self.origin_cn}', shathyar='{self.shathyar}')>"

# Explicit index declarations (composite if needed later)
Index('idx_official_dictionary_norm_cn', OfficialDictionary.norm_origin_cn)
Index('idx_official_dictionary_norm_sh', OfficialDictionary.norm_shathyar)
