"""
Shathyar Translation Web Application - Main FastAPI Application

Entry point for the backend server with all route configurations,
middleware setup, and mystical error handling.
"""

import logging
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
import os
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from .db import get_db_session
from .utils.normalize import normalize_text
from .services.dictionary_reader import DictionaryReader
from .models.official_dictionary import OfficialDictionary

# Import API routers
from .api.translate import router as translate_router
from .api.dictionary import router as dictionary_router  
from .api.session import router as session_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🔮 启动沙斯亚尔语翻译服务... / Starting Shathyar Translation Service...")
    logger.info("📚 Loading mystical knowledge from ancient scrolls...")
    
    # Initialize dictionary from CSV if table seems empty
    try:
      # Peek a DB session
      from sqlalchemy import select
      db_gen = get_db_session()
      db_session: Session = next(db_gen)
      try:
        count = db_session.query(OfficialDictionary).count()
        # Anchor phrases that must exist
        anchors = [
          (None, "Aglathrax hig' thrixa."),
          ("我在你肺里安家了！", None),
        ]
        need_reload = (count == 0)
        if not need_reload:
          # Verify normalized presence of anchors
          if anchors[0][1]:
            nsh = normalize_text(anchors[0][1])
            if db_session.query(OfficialDictionary).filter(OfficialDictionary.norm_shathyar == nsh).count() == 0:
              need_reload = True
          if anchors[1][0]:
            ncn = normalize_text(anchors[1][0])
            if db_session.query(OfficialDictionary).filter(OfficialDictionary.norm_origin_cn == ncn).count() == 0:
              need_reload = True
        if need_reload:
          logger.info("📖 Official dictionary empty; attempting to import shasiyaer.csv")
          reader = DictionaryReader(db_session)
          # Try multiple common locations
          candidates = [
            Path('shasiyaer.csv'),
            Path('data/shasiyaer.csv'),
            Path(__file__).resolve().parent.parent.parent / 'shasiyaer.csv',
          ]
          csv_path = next((p for p in candidates if p.exists()), None)
          if csv_path:
            stats = reader.load_dictionary_from_csv(str(csv_path), force_reload=True)
            logger.info(f"📥 Dictionary imported: {stats}")
          else:
            logger.warning("⚠️ Could not locate shasiyaer.csv; dictionary remains empty")

        # Always attempt to load curated proper nouns for AI context
        try:
          curated_path = Path(__file__).resolve().parent.parent / 'data' / 'official_proper_nouns.csv'
          if curated_path.exists():
            reader = DictionaryReader(db_session)
            cstats = reader.load_curated_from_csv(str(curated_path), source_tag='curated_proper_v1')
            logger.info(f"📚 Curated proper nouns loaded: {cstats}")
          else:
            logger.info("ℹ️ Curated proper nouns file not found; skipping")
        except Exception as ce:
          logger.warning(f"⚠️ Curated proper nouns load failed: {ce}")
      finally:
        try:
          next(db_gen)
        except StopIteration:
          pass
    except Exception as e:
      logger.warning(f"⚠️ Dictionary autoload skipped due to error: {e}")
    
    logger.info("✨ Translation spells are ready!")
    yield
    
    # Shutdown
    logger.info("🌙 Closing mystical portals...")
    logger.info("👋 Translation service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="沙斯亚尔语翻译器 / Shathyar Translator",
    description="""
    🔮 **神秘的沙斯亚尔语翻译门户 / Mystical Shathyar Translation Portal**
    
    探索虚空语言的奥秘，在中文与沙斯亚尔语之间架起桥梁。
    *Explore the mysteries of the Void language, bridging Chinese and Shathyar.*
    
    ## Features / 功能特色
    
    - 🌟 AI驱动的智能翻译 / AI-Powered Intelligent Translation
    - 📖 官方词典精准匹配 / Official Dictionary Exact Matching  
    - ⚡ 每日500次翻译配额 / 500 Daily Translation Quota
    - 🎨 神秘主题界面 / Mystical Themed Interface
    - 🛡️ 用户编辑确认机制 / User Edit Confirmation System
    
    ## Rate Limiting / 速率限制
    
    - **Daily Limit**: 500 translations per IP address
    - **Reset Time**: Midnight UTC daily  
    - **Quota Status**: Available via `/api/v1/session/quota`
    
    ## Mystical Error Messages / 神秘错误信息
    
    All error responses include mystical theming with bilingual Chinese/English messages.
    
    ---
    
    *"在虚空的低语中，寻找语言的真谛... / In the whispers of the Void, seek the essence of language..."*
    """,
    version="1.0.1",
    contact={
        "name": "Shathyar Translation Team",
        "email": "noreply@shathyar.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

# CORS Configuration (configurable via env)
default_origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Append optional frontend origins from env
# FRONTEND_ORIGIN=https://1120370331.github.io
frontend_origin = os.getenv("FRONTEND_ORIGIN")
if frontend_origin:
    default_origins.append(frontend_origin)

# Or multiple, comma-separated
# CORS_ALLOW_ORIGINS=https://a.example.com,https://b.example.com
env_origins = os.getenv("CORS_ALLOW_ORIGINS")
if env_origins:
    default_origins.extend([o.strip() for o in env_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Custom middleware for request logging and mystical headers
@app.middleware("http")
async def mystical_middleware(request: Request, call_next):
    """Add mystical headers and request logging"""
    
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"🔮 Incoming spell request: {request.method} {request.url.path}")
    
    # Process request
    try:
        response = await call_next(request)
        
        # Add mystical headers
        response.headers["X-Powered-By"] = "Ancient Void Magic"
        response.headers["X-Translation-Portal"] = "Shathyar-Gateway-v1.0"
        response.headers["X-Mystical-Blessing"] = "May the Void guide your words"
        
        # Calculate processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}s"
        
        logger.info(f"✨ Spell completed in {process_time:.3f}s - Status: {response.status_code}")
        
        return response
        
    except Exception as e:
        # Log error with mystical flair
        process_time = time.time() - start_time
        logger.error(f"💀 Mystical error after {process_time:.3f}s: {str(e)}")
        
        # Return mystical error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "未知的神秘力量干扰了翻译过程... / Unknown mystical forces disrupted the translation",
                "error_type": "mystical_interference",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time": f"{process_time:.3f}s"
            }
        )


# Include API routers
app.include_router(translate_router)
app.include_router(dictionary_router)
app.include_router(session_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "shathyar-translator",
        "version": "1.0.1",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "翻译法阵运行正常 / Translation spells operating normally"
    }


# Root endpoint with mystical greeting
@app.get("/")
async def root():
    """Root endpoint with mystical welcome message"""
    return {
        "message": "🔮 欢迎来到沙斯亚尔语翻译门户 / Welcome to the Shathyar Translation Portal",
        "description": "探索虚空语言的奥秘 / Explore the mysteries of the Void language",
        "endpoints": {
            "translate": "/api/v1/translate",
            "dictionary": "/api/v1/dictionary/search", 
            "quota": "/api/v1/session/quota",
            "health": "/health",
            "docs": "/docs"
        },
        "mystical_quote": "在无尽虚空中，语言是唯一的真理... / In the endless Void, language is the only truth...",
        "status": "ready"
    }


# Custom 404 handler with mystical theme
@app.exception_handler(404)
async def mystical_404_handler(request: Request, exc: HTTPException):
    """Custom 404 handler with mystical messaging"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "古卷中未记录此路径... / This path is not recorded in the ancient scrolls...",
            "error_type": "path_not_found", 
            "path": str(request.url.path),
            "suggestion": "请查阅 /docs 获取完整的法术目录 / Please consult /docs for the complete spell catalog",
            "mystical_hint": "迷失者需寻找正确的虚空之门 / The lost must seek the correct portal to the Void"
        }
    )


# Rate limit exceeded handler
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc: HTTPException):
    """Custom rate limit handler"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "魔力耗尽，请等待重置 / Magic power exhausted, please wait for reset",
            "error_type": "rate_limited",
            "message": "每日翻译配额已达上限 / Daily translation quota limit reached",
            "reset_info": "配额将在明日子夜重置 / Quota will reset at midnight",
            "mystical_wisdom": "耐心是掌握虚空语言的第一步 / Patience is the first step in mastering the Void language"
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Read runtime configuration from environment
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    workers = int(os.getenv("UVICORN_WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info")
    reload_flag = os.getenv("RELOAD", "false").strip().lower() in {"1", "true", "yes"}

    print("🔮 启动沙斯亚尔语翻译服务器... / Starting Shathyar Translation Server...")
    print(f"📍 服务地址 / Server Address: http://{host}:{port}")
    print(f"📚 API文档 / API Documentation: http://{host}:{port}/docs")
    print("✨ 准备接收翻译请求... / Ready to receive translation requests...")

    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload_flag,
        log_level=log_level,
        workers=workers if not reload_flag else 1,
    )
