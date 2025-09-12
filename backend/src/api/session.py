"""
Session API Endpoints

GET /api/v1/session/quota - Get user quota status
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from ..services.rate_limiter import RateLimiter
from ..models.user_session import UserSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/session", tags=["session"])


class QuotaStatusResponse(BaseModel):
    """User quota status response"""
    tokens_remaining: int
    daily_limit: int
    reset_time: str
    time_to_reset_seconds: int
    is_blocked: bool
    total_requests_today: int
    percentage_used: float
    status: str


class QuotaExtensionRequest(BaseModel):
    """Request to extend user quota (admin function)"""
    additional_tokens: int
    reason: Optional[str] = "Admin quota extension"


from ..db import get_db_session  # Real SQLAlchemy Session provider


def get_client_ip(request: Request) -> str:
    """Extract client IP address"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host


def get_user_agent(request: Request) -> str:
    """Extract user agent"""
    return request.headers.get("User-Agent", "unknown")


@router.get("/quota", response_model=QuotaStatusResponse)
async def get_quota_status(
    request: Request,
    db_session: Session = Depends(get_db_session)
):
    """
    Get current quota status for the requesting user
    
    Returns the user's current magic power (translation quota) status
    including remaining tokens, reset time, and usage statistics.
    
    Used by frontend MagicPowerIndicator component to display quota.
    
    Returns:
    - Current tokens remaining (0-500)
    - Daily limit and reset time
    - Usage statistics and percentage
    - Blocking status
    """
    
    try:
        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Initialize rate limiter service
        rate_limiter = RateLimiter(db_session)
        
        # Get quota status
        quota_status = rate_limiter.get_session_quota(client_ip)
        
        # Determine overall status
        status = "active"
        if quota_status.get('is_blocked', False):
            status = "blocked"
        elif quota_status.get('tokens_remaining', 0) == 0:
            status = "exhausted"
        elif quota_status.get('percentage_used', 0) > 90:
            status = "low"
        
        response = QuotaStatusResponse(
            tokens_remaining=quota_status.get('tokens_remaining', 0),
            daily_limit=quota_status.get('daily_limit', 500),
            reset_time=quota_status.get('reset_time', ''),
            time_to_reset_seconds=quota_status.get('time_to_reset_seconds', 0),
            is_blocked=quota_status.get('is_blocked', False),
            total_requests_today=quota_status.get('total_requests_today', 0),
            percentage_used=quota_status.get('percentage_used', 0.0),
            status=status
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Quota status error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取配额状态时发生错误 / Error retrieving quota status"
        )


@router.post("/quota/extend")
async def extend_quota(
    extension_request: QuotaExtensionRequest,
    request: Request,
    db_session: Session = Depends(get_db_session)
):
    """
    Extend user quota (Admin function)
    
    Allows administrators to grant additional translation tokens
    to users beyond their daily limit.
    
    This endpoint would typically require admin authentication
    and should be used sparingly for special cases.
    
    Body:
    - additional_tokens: Number of tokens to add (positive integer)
    - reason: Optional reason for the extension
    """
    
    try:
        client_ip = get_client_ip(request)
        
        # Validate request
        if extension_request.additional_tokens <= 0:
            raise HTTPException(
                status_code=400,
                detail="附加令牌数必须为正数 / Additional tokens must be positive"
            )
        
        if extension_request.additional_tokens > 1000:
            raise HTTPException(
                status_code=400,
                detail="单次扩展不能超过1000个令牌 / Single extension cannot exceed 1000 tokens"
            )
        
        # Initialize rate limiter service
        rate_limiter = RateLimiter(db_session)
        
        # Extend quota
        updated_quota = rate_limiter.extend_quota(
            client_ip, 
            extension_request.additional_tokens
        )
        
        logger.info(f"Quota extended for {client_ip}: +{extension_request.additional_tokens} tokens. Reason: {extension_request.reason}")
        
        return {
            "success": True,
            "message": f"配额已扩展 {extension_request.additional_tokens} 个令牌 / Quota extended by {extension_request.additional_tokens} tokens",
            "new_quota_status": updated_quota,
            "reason": extension_request.reason
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quota extension error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="扩展配额时发生错误 / Error extending quota"
        )


@router.post("/block")
async def block_session(
    request: Request,
    reason: str = "Manual block",
    db_session: Session = Depends(get_db_session)
):
    """
    Block user session (Admin function)
    
    Prevents a user from making further translation requests.
    Used for abuse prevention and moderation.
    
    This endpoint requires admin authentication in production.
    
    Body:
    - reason: Reason for blocking the session
    """
    
    try:
        client_ip = get_client_ip(request)
        
        # Initialize rate limiter service
        rate_limiter = RateLimiter(db_session)
        
        # Block session
        session_status = rate_limiter.block_session(client_ip, reason)
        
        logger.warning(f"Session blocked for {client_ip}. Reason: {reason}")
        
        return {
            "success": True,
            "message": f"会话已被阻止 / Session has been blocked",
            "reason": reason,
            "session_status": session_status
        }
    
    except Exception as e:
        logger.error(f"Session blocking error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="阻止会话时发生错误 / Error blocking session"
        )


@router.post("/unblock")
async def unblock_session(
    request: Request,
    db_session: Session = Depends(get_db_session)
):
    """
    Remove block from user session (Admin function)
    
    Restores translation access for a previously blocked user.
    
    This endpoint requires admin authentication in production.
    """
    
    try:
        client_ip = get_client_ip(request)
        
        # Initialize rate limiter service
        rate_limiter = RateLimiter(db_session)
        
        # Unblock session
        session_status = rate_limiter.unblock_session(client_ip)
        
        logger.info(f"Session unblocked for {client_ip}")
        
        return {
            "success": True,
            "message": "会话阻止已解除 / Session block has been removed",
            "session_status": session_status
        }
    
    except Exception as e:
        logger.error(f"Session unblocking error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="解除会话阻止时发生错误 / Error unblocking session"
        )


@router.get("/stats")
async def get_session_stats(db_session: Session = Depends(get_db_session)):
    """
    Get system-wide session statistics (Admin function)
    
    Returns aggregate statistics about user sessions and quota usage
    for system monitoring and capacity planning.
    
    This endpoint requires admin authentication in production.
    """
    
    try:
        # Initialize rate limiter service
        rate_limiter = RateLimiter(db_session)
        
        # Get system stats
        stats = rate_limiter.get_rate_limit_stats()
        
        return {
            "system_stats": stats,
            "status": "active",
            "description": "系统会话统计信息 / System session statistics"
        }
    
    except Exception as e:
        logger.error(f"Session stats error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取会话统计时发生错误 / Error retrieving session statistics"
        )
