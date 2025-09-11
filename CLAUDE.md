# Shathyar Language Translation Web Application

A bidirectional Chinese ⟷ Shathyar translation web application with AI-powered generation, mystical UI design, and rate limiting.

## Project Context

This is a World of Warcraft fan project that translates between Chinese and Shathyar (the fictional Void Lords' language). The application combines an official dictionary with AI-powered translation generation to create new Shathyar-style text while maintaining linguistic consistency.

## Recent Changes

1. **Planning Phase Complete (2025-09-11)**
   - Comprehensive technical research completed
   - Data model designed with 4 core entities
   - REST API contracts specified in OpenAPI 3.0
   - Quickstart validation guide created

2. **Architecture Decisions**
   - FastAPI backend + React frontend
   - SQLite database with WAL mode
   - Token bucket rate limiting (500/day per IP)
   - Circuit breaker pattern for AI service integration

3. **Next Phase**: Task generation and implementation

## Technical Stack

**Backend**:
- Python 3.11, FastAPI, SQLAlchemy
- SQLite (development), PostgreSQL (production)
- Volcengine API (OpenAI-compatible) for AI translation
- Rate limiting: Token bucket algorithm

**Frontend**:
- React 18, TypeScript, React Query
- Mystical/Cthulhu UI theme with WCAG AA compliance
- Real-time "magic power" quota display

**Key Libraries**:
- `shathyar-translator`: Core translation logic with CLI
- `rate-limiter`: IP-based rate limiting with CLI  
- `dictionary-reader`: CSV dictionary access with CLI

## Core Features

1. **Bidirectional Translation** (FR-001, FR-002)
   - Chinese → Shathyar (AI-generated)
   - Shathyar → Chinese (dictionary lookup)
   - Language selection interface

2. **AI Integration** (FR-005)
   - Volcengine Doubao model integration
   - Dictionary context in prompts
   - Circuit breaker + retry logic
   - Cost optimization through caching

3. **User Workflow** (FR-006, FR-007, FR-008)
   - Edit AI-generated translations
   - Save confirmed translations to database
   - Copy functionality for final results

4. **Rate Limiting** (FR-010, FR-011, FR-012)
   - 500 translations/day per IP address
   - "魔力值" (magic power) quota display
   - 500 character input limit
   - Daily reset at midnight UTC

5. **Mystical UI** (FR-013, FR-014, FR-015)
   - Cthulhu/mystical dark theme
   - Brown-black scroll color scheme
   - Magical icons and animations
   - Immersive error messages

## Database Schema

```sql
-- Core entities with relationships
translation_entries     # User-generated translations
official_dictionary     # shasiyaer.csv import (read-only)
user_sessions          # Rate limiting by IP
translation_requests   # Request logging and analytics
```

## API Endpoints

```
POST /api/v1/translate              # Main translation endpoint
POST /api/v1/translate/{id}/confirm # Confirm edited translation  
GET  /api/v1/dictionary/search      # Search official dictionary
GET  /api/v1/session/quota          # Get current quota
```

## Development Workflow

Following Test-Driven Development (TDD):
1. **Contract Tests**: API endpoint validation
2. **Integration Tests**: Service interaction testing  
3. **E2E Tests**: Complete user workflow validation
4. **Unit Tests**: Individual component testing

**Important**: Tests must be written first and fail before implementation begins.

## File Structure

```
backend/
├── src/
│   ├── models/          # SQLAlchemy data models
│   ├── services/        # Business logic libraries
│   ├── api/             # FastAPI endpoints
│   └── cli/             # Command-line interfaces
└── tests/

frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page components
│   ├── services/        # API client + state management
│   └── styles/          # Mystical theme system
└── tests/

specs/001-ai-ai-shasiyaer/
├── spec.md              # Original requirements
├── plan.md              # Implementation plan  
├── research.md          # Technology research
├── data-model.md        # Database design
├── quickstart.md        # E2E validation guide
└── contracts/           # API specifications
```

## Error Handling

All errors use mystical theming:
- Rate limit: "魔力耗尽！今日翻译次数已达上限。"
- AI service down: "翻译法阵暂时失效，请稍后重试。"
- Translation failed: "破译失败..."
- Service unavailable: "古神的低语暂时无法解读..."

## Security Considerations

- Input validation and sanitization
- Prompt injection prevention
- Rate limiting enforcement  
- API key protection (environment variables)
- CORS configuration for web security

## Performance Goals

- Dictionary lookup: <100ms (p95)
- Cached translation: <200ms (p95)
- AI translation: <5000ms (p95)
- Support 10+ concurrent users
- 70-80% cost reduction through caching

## Current Status

**Phase 1 Complete**: Planning and design finished
**Phase 2 Ready**: Task generation and implementation
**Next Command**: `/tasks` to generate implementation tasks

The application architecture balances technical requirements with mystical theming, ensuring both functionality and immersive user experience for World of Warcraft fans exploring the Shathyar language.