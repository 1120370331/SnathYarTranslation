"""
Dictionary API Endpoints

GET /api/v1/dictionary/search - Search official dictionary
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..services.dictionary_reader import DictionaryReader
from ..models.official_dictionary import OfficialDictionary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dictionary", tags=["dictionary"])


class DictionaryEntryResponse(BaseModel):
    """Single dictionary entry response"""
    id: int
    origin_cn: str
    shathyar: str
    origin_en: Optional[str] = None
    created_at: Optional[str] = None


class DictionarySearchResponse(BaseModel):
    """Dictionary search results response"""
    query: str
    language: str
    exact_match: bool
    results: List[DictionaryEntryResponse]
    total_results: int
    search_time_ms: int


class DictionaryStatsResponse(BaseModel):
    """Dictionary statistics response"""
    total_entries: int
    average_chinese_length: float
    average_shathyar_length: float
    english_coverage_percent: float
    status: str
    integrity_check: bool


def get_db_session() -> Session:
    """Get database session (dependency injection)"""
    # Mock for now - would return actual SQLAlchemy session
    pass


@router.get("/search", response_model=DictionarySearchResponse)
async def search_dictionary(
    q: str = Query(..., description="Search query text"),
    language: str = Query(..., description="Search language: chinese or shathyar"),
    exact: bool = Query(False, description="Use exact matching only"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    db_session: Session = Depends(get_db_session)
):
    """
    Search the official Shathyar dictionary
    
    Provides search functionality for the authoritative shasiyaer.csv dictionary.
    Supports both fuzzy and exact matching in Chinese or Shathyar text.
    
    Query Parameters:
    - q: Search query text (required)
    - language: "chinese" or "shathyar" (required)  
    - exact: True for exact matching, False for fuzzy (default: False)
    - limit: Maximum results (1-50, default: 10)
    
    Returns:
    - Matching dictionary entries with metadata
    - Search performance metrics
    - Total result count
    """
    
    import time
    start_time = time.time()
    
    try:
        # Validate parameters
        if language not in ['chinese', 'shathyar']:
            raise HTTPException(
                status_code=400,
                detail="语言参数无效 / Invalid language parameter. Must be 'chinese' or 'shathyar'"
            )
        
        if not q or not q.strip():
            raise HTTPException(
                status_code=400,
                detail="搜索查询不能为空 / Search query cannot be empty"
            )
        
        if len(q) > 100:
            raise HTTPException(
                status_code=400,
                detail="搜索查询过长 / Search query too long (max 100 characters)"
            )
        
        # Initialize dictionary service
        dictionary_reader = DictionaryReader(db_session)
        
        # Perform search
        if language == 'chinese':
            results = dictionary_reader.search_chinese(q.strip(), exact_match=exact, limit=limit)
        else:
            results = dictionary_reader.search_shathyar(q.strip(), exact_match=exact, limit=limit)
        
        # Convert to response format
        entry_responses = []
        for entry in results:
            entry_responses.append(DictionaryEntryResponse(
                id=entry.id,
                origin_cn=entry.origin_cn,
                shathyar=entry.shathyar,
                origin_en=entry.origin_en,
                created_at=entry.created_at.isoformat() if entry.created_at else None
            ))
        
        search_time = int((time.time() - start_time) * 1000)
        
        response = DictionarySearchResponse(
            query=q.strip(),
            language=language,
            exact_match=exact,
            results=entry_responses,
            total_results=len(entry_responses),
            search_time_ms=search_time
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dictionary search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="词典搜索时发生内部错误 / Internal error during dictionary search"
        )


@router.get("/stats", response_model=DictionaryStatsResponse)
async def get_dictionary_stats(db_session: Session = Depends(get_db_session)):
    """
    Get dictionary statistics and health metrics
    
    Returns:
    - Total entry count
    - Average text lengths  
    - Language coverage statistics
    - Dictionary integrity status
    """
    
    try:
        # Initialize dictionary service
        dictionary_reader = DictionaryReader(db_session)
        
        # Get statistics
        stats = dictionary_reader.get_dictionary_stats()
        
        response = DictionaryStatsResponse(
            total_entries=stats.get('total_entries', 0),
            average_chinese_length=stats.get('average_chinese_length', 0.0),
            average_shathyar_length=stats.get('average_shathyar_length', 0.0),
            english_coverage_percent=stats.get('english_coverage_percent', 0.0),
            status=stats.get('status', 'unknown'),
            integrity_check=stats.get('integrity_check', False)
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Dictionary stats error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取词典统计信息时发生错误 / Error retrieving dictionary statistics"
        )


@router.get("/context")
async def get_dictionary_context(
    limit: int = Query(10, ge=1, le=100, description="Number of context entries"),
    db_session: Session = Depends(get_db_session)
):
    """
    Get dictionary context for AI translation prompts
    
    Returns sample dictionary entries and linguistic patterns 
    used to improve AI translation quality.
    
    This endpoint is primarily used by the translation service
    to provide context to AI models.
    
    Query Parameters:
    - limit: Number of context entries to return (1-100, default: 10)
    """
    
    try:
        # Initialize dictionary service
        dictionary_reader = DictionaryReader(db_session)
        
        # Get context data
        context = dictionary_reader.get_context(limit=limit)
        
        return {
            "status": context.get("status", "unknown"),
            "sample_entries": context.get("sample_entries", []),
            "total_entries": context.get("total_entries", 0),
            "patterns": context.get("patterns", {}),
            "generated_at": context.get("generated_at"),
            "usage_note": "此数据用于AI翻译上下文增强 / This data is used for AI translation context enhancement"
        }
    
    except Exception as e:
        logger.error(f"Dictionary context error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取词典上下文时发生错误 / Error retrieving dictionary context"
        )