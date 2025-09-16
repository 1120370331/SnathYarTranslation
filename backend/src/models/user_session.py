"""
User Session Model

Tracks user sessions and rate limiting quotas for translation API.
Implements token bucket algorithm for quota management.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from .translation_entry import Base
import uuid


class UserSession(Base):
    """
    User session tracking with rate limiting quotas
    
    Implements token bucket algorithm for rate limiting (FR-008):
    - 500 translations per day per IP address
    - Daily reset at midnight UTC
    - Persistent storage in SQLite database
    
    Attributes:
        id: Primary key (UUID string)
        ip_address: Client IP address (anonymized/hashed for privacy)
        user_agent_hash: Hashed user agent string for additional tracking
        tokens_remaining: Current available translation tokens (0-500)
        daily_limit: Maximum tokens per day (default 500)
        reset_time: Next token reset timestamp (daily)
        first_request_at: Timestamp of first request in current period
        total_requests: Total translation requests made
        is_blocked: Emergency block flag (manual override)
        created_at: Session creation timestamp
        updated_at: Last activity timestamp
    """
    
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address_hash = Column(String(64), nullable=False, unique=True)  # SHA256 hash
    user_agent_hash = Column(String(64), nullable=True)  # SHA256 hash for additional tracking
    tokens_remaining = Column(Integer, nullable=False, default=500)
    daily_limit = Column(Integer, nullable=False, default=500)
    reset_time = Column(DateTime(timezone=True), nullable=False)
    first_request_at = Column(DateTime(timezone=True), nullable=True)
    total_requests = Column(Integer, nullable=False, default=0)
    is_blocked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __init__(self, ip_address_hash: str, user_agent_hash: str = None, 
                 daily_limit: int = 500):
        """Initialize user session with rate limiting setup"""
        
        if not ip_address_hash:
            raise ValueError("IP address hash is required")
        if daily_limit < 1 or daily_limit > 10000:
            raise ValueError("Daily limit must be between 1 and 10000")
            
        self.ip_address_hash = ip_address_hash
        self.user_agent_hash = user_agent_hash
        self.daily_limit = daily_limit
        self.tokens_remaining = daily_limit
        self.reset_time = self._calculate_next_reset()
        self.total_requests = 0
        self.is_blocked = False
    
    def can_make_request(self) -> bool:
        """Check if session can make a translation request"""
        
        # Check for manual block
        if self.is_blocked:
            return False
        
        # Auto-reset if time has passed
        if datetime.now(timezone.utc) >= self.reset_time:
            self._reset_daily_quota()
        
        return self.tokens_remaining > 0
    
    def consume_token(self) -> bool:
        """
        Consume one translation token
        
        Returns:
            bool: True if token consumed successfully, False if no tokens available
        """
        
        if not self.can_make_request():
            return False
        
        self.tokens_remaining -= 1
        self.total_requests += 1
        self.updated_at = datetime.now(timezone.utc)
        
        # Set first request timestamp if this is the first request today
        if self.tokens_remaining == self.daily_limit - 1:
            self.first_request_at = datetime.now(timezone.utc)
        
        return True
    
    def get_quota_status(self) -> dict:
        """Get current quota status for API responses"""
        
        # Auto-reset if needed
        if datetime.now(timezone.utc) >= self.reset_time:
            self._reset_daily_quota()
        
        time_to_reset = max(0, int((self.reset_time - datetime.now(timezone.utc)).total_seconds()))
        
        return {
            "tokens_remaining": self.tokens_remaining,
            "daily_limit": self.daily_limit,
            "reset_time": self.reset_time.isoformat(),
            "time_to_reset_seconds": time_to_reset,
            "is_blocked": self.is_blocked,
            "total_requests_today": self.daily_limit - self.tokens_remaining,
            "percentage_used": round((1 - self.tokens_remaining / self.daily_limit) * 100, 1)
        }
    
    def _reset_daily_quota(self) -> None:
        """Reset daily quota (called automatically)"""
        self.tokens_remaining = self.daily_limit
        self.reset_time = self._calculate_next_reset()
        self.first_request_at = None
        self.updated_at = datetime.now(timezone.utc)
    
    def _calculate_next_reset(self) -> datetime:
        """Calculate next daily reset time (midnight UTC)"""
        now = datetime.now(timezone.utc)
        next_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return next_reset
    
    def block_session(self, reason: str = "Manual block") -> None:
        """Manually block session (admin override)"""
        self.is_blocked = True
        self.updated_at = datetime.now(timezone.utc)
    
    def unblock_session(self) -> None:
        """Remove manual block from session"""
        self.is_blocked = False
        self.updated_at = datetime.now(timezone.utc)
    
    def extend_quota(self, additional_tokens: int) -> None:
        """Add extra tokens to current quota (admin action)"""
        if additional_tokens < 0:
            raise ValueError("Additional tokens must be positive")
        
        self.tokens_remaining = min(
            self.tokens_remaining + additional_tokens, 
            self.daily_limit * 2  # Cap at 2x daily limit
        )
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "tokens_remaining": self.tokens_remaining,
            "daily_limit": self.daily_limit,
            "reset_time": self.reset_time.isoformat() if self.reset_time else None,
            "total_requests": self.total_requests,
            "is_blocked": self.is_blocked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "quota_status": self.get_quota_status()
        }
    
    @staticmethod
    def hash_ip_address(ip_address: str) -> str:
        """Hash IP address for privacy compliance"""
        import hashlib
        return hashlib.sha256(ip_address.encode()).hexdigest()
    
    @staticmethod
    def hash_user_agent(user_agent: str) -> str:
        """Hash user agent for privacy compliance"""
        import hashlib
        return hashlib.sha256(user_agent.encode()).hexdigest()
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, tokens={self.tokens_remaining}/{self.daily_limit}, blocked={self.is_blocked})>"