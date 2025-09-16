"""
Translation Request Model

Tracks individual translation requests for analytics and debugging.
Links requests to user sessions and translation results.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Numeric, Text
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from .translation_entry import Base
import uuid


class TranslationRequest(Base):
    """
    Individual translation request tracking
    
    Records each translation API call for analytics, debugging, and audit trail.
    Links user sessions to translation results for complete request lifecycle.
    
    Attributes:
        id: Primary key (UUID string)
        session_id: Foreign key to UserSession (for rate limiting context)
        translation_id: Foreign key to TranslationEntry (result, nullable for failed requests)
        source_text: Original input text (max 500 chars)
        source_language: Input language ("chinese" or "shathyar")
        request_ip: Client IP address (hashed for privacy)
        user_agent: Client user agent (truncated for storage)
        status: Request status ("pending", "completed", "failed", "rate_limited")
        error_message: Error details if request failed
        processing_time_ms: Time taken to process request in milliseconds
        ai_tokens_used: Number of AI API tokens consumed (if applicable)
        cache_hit: Whether result was served from cache
        created_at: Request timestamp
        completed_at: Completion timestamp (nullable)
    """
    
    __tablename__ = "translation_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('user_sessions.id'), nullable=False)
    translation_id = Column(String, ForeignKey('translation_entries.id'), nullable=True)
    
    # Request details
    source_text = Column(String(500), nullable=False)
    source_language = Column(String(10), nullable=False)  # "chinese" or "shathyar"
    request_ip_hash = Column(String(64), nullable=False)  # Hashed IP for privacy
    user_agent = Column(String(500), nullable=True)  # Truncated user agent
    
    # Request lifecycle
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, failed, rate_limited
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # AI and performance metrics
    ai_tokens_used = Column(Integer, nullable=True, default=0)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00-1.00
    cache_hit = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # session = relationship("UserSession", back_populates="requests")
    # translation = relationship("TranslationEntry", back_populates="requests")
    
    def __init__(self, session_id: str, source_text: str, source_language: str, 
                 request_ip_hash: str, user_agent: str = None):
        """Initialize translation request"""
        
        # Validation
        if not session_id:
            raise ValueError("Session ID is required")
        if not source_text or len(source_text.strip()) == 0:
            raise ValueError("Source text cannot be empty")
        if len(source_text) > 500:
            raise ValueError("Source text exceeds 500 character limit")
        if source_language not in ["chinese", "shathyar"]:
            raise ValueError("Source language must be 'chinese' or 'shathyar'")
        if not request_ip_hash:
            raise ValueError("Request IP hash is required")
            
        self.session_id = session_id
        self.source_text = source_text.strip()
        self.source_language = source_language
        self.request_ip_hash = request_ip_hash
        self.user_agent = user_agent[:500] if user_agent else None  # Truncate for storage
        self.status = "pending"
        self.ai_tokens_used = 0
        self.cache_hit = False
    
    def mark_completed(self, translation_id: str, processing_time_ms: int, 
                      cache_hit: bool = False, ai_tokens_used: int = 0, 
                      confidence_score: float = None) -> None:
        """Mark request as completed successfully"""
        
        self.translation_id = translation_id
        self.status = "completed"
        self.processing_time_ms = processing_time_ms
        self.cache_hit = cache_hit
        self.ai_tokens_used = ai_tokens_used
        self.confidence_score = confidence_score
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str, processing_time_ms: int = None) -> None:
        """Mark request as failed with error details"""
        
        self.status = "failed"
        self.error_message = error_message[:1000] if error_message else "Unknown error"  # Truncate
        self.processing_time_ms = processing_time_ms
        self.completed_at = datetime.utcnow()
    
    def mark_rate_limited(self, processing_time_ms: int = None) -> None:
        """Mark request as rate limited"""
        
        self.status = "rate_limited"
        self.error_message = "Rate limit exceeded - 500 translations per day"
        self.processing_time_ms = processing_time_ms or 0
        self.completed_at = datetime.utcnow()
    
    def get_duration_ms(self) -> int:
        """Get request duration in milliseconds"""
        if self.processing_time_ms:
            return self.processing_time_ms
        
        if self.completed_at:
            duration = (self.completed_at - self.created_at).total_seconds() * 1000
            return int(duration)
        
        # Request still pending
        duration = (datetime.utcnow() - self.created_at).total_seconds() * 1000
        return int(duration)
    
    def is_completed(self) -> bool:
        """Check if request has completed (success or failure)"""
        return self.status in ["completed", "failed", "rate_limited"]
    
    def is_successful(self) -> bool:
        """Check if request completed successfully"""
        return self.status == "completed"
    
    def get_analytics_data(self) -> dict:
        """Get analytics data for this request"""
        return {
            "request_id": self.id,
            "source_language": self.source_language,
            "text_length": len(self.source_text),
            "status": self.status,
            "processing_time_ms": self.processing_time_ms,
            "cache_hit": self.cache_hit,
            "ai_tokens_used": self.ai_tokens_used,
            "confidence_score": float(self.confidence_score) if self.confidence_score else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "translation_id": self.translation_id,
            "source_text": self.source_text,
            "source_language": self.source_language,
            "status": self.status,
            "error_message": self.error_message,
            "processing_time_ms": self.processing_time_ms,
            "cache_hit": self.cache_hit,
            "ai_tokens_used": self.ai_tokens_used,
            "confidence_score": float(self.confidence_score) if self.confidence_score else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @staticmethod
    def get_success_rate_by_language(requests: list) -> dict:
        """Calculate success rates by source language from request list"""
        
        stats = {
            "chinese": {"total": 0, "successful": 0, "rate": 0.0},
            "shathyar": {"total": 0, "successful": 0, "rate": 0.0},
            "overall": {"total": 0, "successful": 0, "rate": 0.0}
        }
        
        for req in requests:
            stats[req.source_language]["total"] += 1
            stats["overall"]["total"] += 1
            
            if req.is_successful():
                stats[req.source_language]["successful"] += 1
                stats["overall"]["successful"] += 1
        
        # Calculate rates
        for lang_stats in stats.values():
            if lang_stats["total"] > 0:
                lang_stats["rate"] = round(lang_stats["successful"] / lang_stats["total"], 3)
        
        return stats
    
    @staticmethod
    def get_average_processing_time(requests: list) -> dict:
        """Calculate average processing times from request list"""
        
        completed_requests = [r for r in requests if r.processing_time_ms is not None]
        
        if not completed_requests:
            return {"average_ms": 0, "count": 0}
        
        total_time = sum(r.processing_time_ms for r in completed_requests)
        average_ms = round(total_time / len(completed_requests), 1)
        
        return {
            "average_ms": average_ms,
            "count": len(completed_requests),
            "min_ms": min(r.processing_time_ms for r in completed_requests),
            "max_ms": max(r.processing_time_ms for r in completed_requests)
        }
    
    def __repr__(self) -> str:
        return f"<TranslationRequest(id={self.id}, status={self.status}, lang={self.source_language})>"