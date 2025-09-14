"""
Translation API Endpoints

POST /api/v1/translate - Main translation endpoint
POST /api/v1/translate/{id}/confirm - Confirm and edit translation
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import time
import logging

from ..services.shathyar_translator import ShathyarTranslator, TranslationError, TranslationNotFoundError
from ..services.rate_limiter import RateLimiter, RateLimitResult
from ..services.ai_client import AIClient, CircuitOpenError, AIServiceError
from ..services.dictionary_reader import DictionaryReader
from ..models.translation_request import TranslationRequest
from ..models.user_session import UserSession

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["translation"])


# Request/Response models
class TranslateRequest(BaseModel):
    """Translation request payload"""
    text: str
    source_language: str
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('文本不能为空 / Text cannot be empty')
        if len(v) > 500:
            raise ValueError('古卷无法记录如此冗长的文字... / Text exceeds character limit')
        return v.strip()
    
    @validator('source_language')
    def validate_language(cls, v):
        if v not in ['chinese', 'shathyar']:
            raise ValueError('语言选择无效 / Invalid language selection')
        return v


class ConfirmTranslationRequest(BaseModel):
    """Translation confirmation request payload"""
    edited_text: str
    
    @validator('edited_text')
    def validate_edited_text(cls, v):
        if not v or not v.strip():
            raise ValueError('编辑后的文本不能为空 / Edited text cannot be empty')
        if len(v) > 1000:
            raise ValueError('编辑后的文本过长 / Edited text exceeds limit')
        return v.strip()


class TranslateResponse(BaseModel):
    """Translation response payload"""
    translated_text: str
    source_text: str
    is_cached: bool
    is_ai_generated: bool
    can_edit: bool
    confidence_score: Optional[float] = None
    translation_id: Optional[str] = None
    magic_power_remaining: int
    processing_time_ms: int


class ErrorResponse(BaseModel):
    """Error response payload"""
    error: str
    error_type: str
    magic_power_remaining: Optional[int] = None
    retry_after_seconds: Optional[int] = None


# Dependency injection functions
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


def create_services(db_session: Session):
    """Create service instances (dependency injection)"""
    import os
    from pathlib import Path

    def _load_env_from_file(p: Path):
        try:
            if p.exists():
                for line in p.read_text(encoding='utf-8').splitlines():
                    if not line or line.strip().startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass

    # Configure AI client from environment
    api_key = os.getenv('SHATHYAR_AI_API_KEY') or os.getenv('VOLCENGINE_API_KEY') or ''
    base_url = os.getenv('SHATHYAR_AI_BASE_URL') or None
    if not api_key:
        here = Path(__file__).resolve()
        candidates = [
            Path('.env'),
            Path('backend/.env'),
            here.parents[2] / '.env',
            here.parents[3] / '.env',
        ]
        for env_path in candidates:
            _load_env_from_file(env_path)
            if os.getenv('SHATHYAR_AI_API_KEY') or os.getenv('VOLCENGINE_API_KEY'):
                break
        api_key = os.getenv('SHATHYAR_AI_API_KEY') or os.getenv('VOLCENGINE_API_KEY') or ''
        base_url = os.getenv('SHATHYAR_AI_BASE_URL') or base_url
    ai_client = AIClient(api_key=api_key, base_url=base_url)
    dictionary_reader = DictionaryReader(db_session)
    rate_limiter = RateLimiter(db_session)
    translator = ShathyarTranslator(db_session, ai_client, dictionary_reader)
    
    return {
        'translator': translator,
        'rate_limiter': rate_limiter,
        'ai_client': ai_client,
        'dictionary_reader': dictionary_reader
    }


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(
    request_data: TranslateRequest,
    request: Request,
    db_session: Session = Depends(get_db_session)
):
    """
    Main translation endpoint implementing complete workflow:
    
    1. Rate limiting check (FR-008)
    2. Create translation request record
    3. Perform translation (cache → dictionary → AI)
    4. Update quotas and analytics
    5. Return mystical-themed response
    """
    
    start_time = time.time()
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Initialize services
        services = create_services(db_session)
        rate_limiter = services['rate_limiter']
        translator = services['translator']

        # 0) Try dictionary/cache lookup without consuming quota
        lookup = translator.lookup_without_ai(request_data.text, request_data.source_language)
        if lookup is not None:
            processing_time = int((time.time() - start_time) * 1000)
            # Get current quota status for display
            quota = rate_limiter.get_session_quota(client_ip)
            response = TranslateResponse(
                translated_text=lookup.translated_text,
                source_text=lookup.source_text,
                is_cached=lookup.is_cached,
                is_ai_generated=lookup.is_ai_generated,
                can_edit=lookup.can_edit,
                confidence_score=lookup.confidence_score,
                translation_id=lookup.translation_id,
                magic_power_remaining=quota.get('tokens_remaining', 0),
                processing_time_ms=processing_time
            )
            return response

        # 1) For shathyar→chinese, we do NOT consume quota; if not found above, return not found
        if request_data.source_language == 'shathyar':
            quota = rate_limiter.get_session_quota(client_ip)
            error_response = ErrorResponse(
                error='破译失败...',
                error_type='translation_not_found',
                magic_power_remaining=quota.get('tokens_remaining', 0)
            )
            return JSONResponse(status_code=404, content=error_response.dict())

        # 1.5) Extra safety: use dictionary reader fuzzy search for Chinese→Shathyar
        if request_data.source_language == 'chinese':
            dict_hits = services['dictionary_reader'].search_chinese(request_data.text, exact_match=True, limit=1)
            if dict_hits:
                hit = dict_hits[0]
                processing_time = int((time.time() - start_time) * 1000)
                quota = rate_limiter.get_session_quota(client_ip)
                return TranslateResponse(
                    translated_text=hit.shathyar,
                    source_text=request_data.text,
                    is_cached=True,
                    is_ai_generated=False,
                    can_edit=False,
                    confidence_score=1.0,
                    translation_id=f"dict_{hit.id}",
                    magic_power_remaining=quota.get('tokens_remaining', 0),
                    processing_time_ms=processing_time
                )

        # 2) For chinese→shathyar, ensure AI auth is configured; then check rate limit and consume token
        if not services['ai_client'].api_key:
            quota = rate_limiter.get_session_quota(client_ip)
            error_response = ErrorResponse(
                error='AI 服务未配置或认证失败 / AI service not configured or authentication failed',
                error_type='ai_auth',
                magic_power_remaining=quota.get('tokens_remaining', 0)
            )
            return JSONResponse(status_code=503, content=error_response.dict())

        # Now rate-limit and proceed
        rate_check = await rate_limiter.check_rate_limit(client_ip, user_agent)
        if not rate_check.allowed:
            processing_time = int((time.time() - start_time) * 1000)
            error_response = ErrorResponse(
                error='魔力耗尽，请等待重置 / Magic power exhausted, please wait for reset',
                error_type='rate_limited',
                magic_power_remaining=rate_check.tokens_remaining,
                retry_after_seconds=rate_check.retry_after_seconds
            )
            return JSONResponse(status_code=429, content=error_response.dict(), headers={'Retry-After': str(rate_check.retry_after_seconds)})

        token_result = await rate_limiter.consume_token(client_ip, user_agent)
        if not token_result.allowed:
            raise HTTPException(status_code=429, detail='Rate limit exceeded')

        # Perform translation with AI path
        try:
            translation_result = await translator.translate(
                request_data.text,
                request_data.source_language
            )

            processing_time = int((time.time() - start_time) * 1000)
            response = TranslateResponse(
                translated_text=translation_result.translated_text,
                source_text=translation_result.source_text,
                is_cached=translation_result.is_cached,
                is_ai_generated=translation_result.is_ai_generated,
                can_edit=translation_result.can_edit,
                confidence_score=translation_result.confidence_score,
                translation_id=translation_result.translation_id,
                magic_power_remaining=token_result.tokens_remaining,
                processing_time_ms=processing_time
            )
            return response

        except TranslationNotFoundError:
            processing_time = int((time.time() - start_time) * 1000)
            error_response = ErrorResponse(
                error='破译失败...',
                error_type='translation_not_found',
                magic_power_remaining=token_result.tokens_remaining
            )
            return JSONResponse(status_code=404, content=error_response.dict())
        except (AIServiceError, CircuitOpenError) as e:
            processing_time = int((time.time() - start_time) * 1000)
            msg = str(e)
            if ' 404' in msg or 'Not Found' in msg:
                # Treat unknown model/endpoint as not-found to avoid confusing users
                error_response = ErrorResponse(
                    error='破译失败...',
                    error_type='translation_not_found',
                    magic_power_remaining=token_result.tokens_remaining
                )
                return JSONResponse(status_code=404, content=error_response.dict())
            else:
                error_response = ErrorResponse(
                    error='翻译法阵暂时失效，请稍后重试 / Translation spell temporarily disrupted, please try again later',
                    error_type='ai_service_error',
                    magic_power_remaining=token_result.tokens_remaining
                )
                return JSONResponse(status_code=503, content=error_response.dict())
        except TranslationError as e:
            processing_time = int((time.time() - start_time) * 1000)
            error_response = ErrorResponse(
                error=str(e),
                error_type='translation_error',
                magic_power_remaining=token_result.tokens_remaining
            )
            return JSONResponse(status_code=400, content=error_response.dict())
    
    except Exception as e:
        logger.error(f"Unexpected error in translation endpoint: {str(e)}")
        processing_time = int((time.time() - start_time) * 1000)
        
        error_response = ErrorResponse(
            error="未知的神秘力量干扰了翻译过程... / Unknown mystical forces disrupted the translation",
            error_type="internal_error"
        )
        
        return JSONResponse(status_code=500, content=error_response.dict())


@router.post("/translate/{translation_id}/confirm")
async def confirm_translation(
    translation_id: str,
    request_data: ConfirmTranslationRequest,
    request: Request,
    db_session: Session = Depends(get_db_session)
):
    """
    Confirm and edit AI-generated translation
    
    Allows users to edit and confirm AI translations (FR-006, FR-007).
    Only works for AI-generated translations that haven't been confirmed yet.
    """
    
    start_time = time.time()
    client_ip = get_client_ip(request)
    
    try:
        # Initialize services
        services = create_services(db_session)
        translator = services['translator']
        rate_limiter = services['rate_limiter']
        
        # Get current quota (for response)
        quota_status = rate_limiter.get_session_quota(client_ip)
        
        # Confirm translation with edits
        try:
            translation_result = translator.confirm_translation(
                translation_id, 
                request_data.edited_text
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Build response
            response = TranslateResponse(
                translated_text=translation_result.translated_text,
                source_text=translation_result.source_text,
                is_cached=translation_result.is_cached,
                is_ai_generated=translation_result.is_ai_generated,
                can_edit=translation_result.can_edit,
                confidence_score=translation_result.confidence_score,
                translation_id=translation_result.translation_id,
                magic_power_remaining=quota_status.get('tokens_remaining', 0),
                processing_time_ms=processing_time
            )
            
            return response
            
        except TranslationNotFoundError as e:
            error_response = ErrorResponse(
                error="翻译记录未找到或已确认 / Translation not found or already confirmed",
                error_type="not_found",
                magic_power_remaining=quota_status.get('tokens_remaining', 0)
            )
            
            return JSONResponse(status_code=404, content=error_response.dict())
            
        except ValueError as e:
            error_response = ErrorResponse(
                error=str(e),
                error_type="validation_error",
                magic_power_remaining=quota_status.get('tokens_remaining', 0)
            )
            
            return JSONResponse(status_code=400, content=error_response.dict())
    
    except Exception as e:
        logger.error(f"Unexpected error in confirm translation endpoint: {str(e)}")
        
        error_response = ErrorResponse(
            error="确认翻译时发生未知错误 / Unknown error occurred while confirming translation",
            error_type="internal_error"
        )
        
        return JSONResponse(status_code=500, content=error_response.dict())
