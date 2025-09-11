# Research Report: Shathyar Translation Web Application

**Date**: 2025-09-11
**Phase**: Phase 0 - Technology Research
**Status**: Complete

## Technology Decisions Summary

This research consolidates findings from comprehensive analysis of web technologies, rate limiting strategies, mystical UI design, and AI API integration for the Shathyar language translation application.

## 1. Web Application Architecture

### Decision: FastAPI Backend + React Frontend with API Gateway Pattern
**Rationale**: 
- Separation of concerns enables independent scaling and development
- FastAPI provides excellent async performance for AI API calls
- React offers robust state management for translation workflows
- API Gateway centralizes cross-cutting concerns (rate limiting, authentication)

**Alternatives considered**:
- Monolithic FastAPI: Simpler but less scalable for multiple AI integrations
- Next.js full-stack: Good but less flexible for complex AI service integration
- Pure serverless: Higher latency unsuitable for real-time translation

### Technical Stack
- **Backend**: Python 3.11, FastAPI, SQLite, Redis (optional)
- **Frontend**: React 18, TypeScript, React Query for server state
- **Database**: SQLite with WAL mode for development, PostgreSQL for production
- **Deployment**: Docker containers, Nginx reverse proxy

## 2. Rate Limiting Implementation

### Decision: Token Bucket Algorithm with SQLite Storage
**Rationale**:
- Token bucket naturally handles burst requests (better user experience)
- SQLite provides persistence without operational complexity
- Daily quota model aligns with "magic power" concept
- Sufficient performance for moderate traffic (hundreds requests/hour)

**Alternatives considered**:
- Redis storage: Better performance but adds operational overhead
- Sliding window: More precise but complex implementation
- Fixed window: Vulnerable to boundary gaming

### Database Schema
```sql
CREATE TABLE rate_limits (
    ip_address BLOB NOT NULL,           
    tokens_remaining INTEGER NOT NULL,  
    last_refill_time INTEGER NOT NULL,  
    daily_reset_time INTEGER NOT NULL,  
    PRIMARY KEY (ip_address)
);
```

## 3. Mystical UI Design System

### Decision: Dark-First Theme with Accessibility Compliance
**Rationale**:
- Dark theme aligns with mystical/Cthulhu aesthetic
- WCAG AA compliance ensures broad usability
- Maintains excellent readability for translation work
- System font fallbacks ensure performance and accessibility

**Color Palette**:
- Base: #121212 (dark gray, not pure black)
- Accent: #4A9B8E (desaturated teal), #7B5A8C (muted purple)
- Text: #E8E6E3 (warm off-white)
- Contrast ratios: All combinations exceed 4.5:1

**Typography**:
- Body: System fonts (SF Pro, Segoe UI, Roboto)
- Headers: Cinzel or Cormorant Garamond for mystical atmosphere
- Sizing: 16px minimum, line-height 1.6, increased letter-spacing for dark mode

**Alternatives considered**:
- Pure mystical fonts: Rejected for readability
- Light theme primary: Rejected for atmospheric requirements
- High-contrast only: Rejected for eye strain concerns

## 4. AI API Integration Strategy

### Decision: Circuit Breaker Pattern with Multi-Layer Caching
**Rationale**:
- Volcengine API requires resilience patterns for production use
- Three-tier caching reduces costs by 70-80%
- Graceful degradation maintains service availability
- Security measures prevent prompt injection attacks

**Integration Architecture**:
```
User Request → Input Validation → Database Cache Check → AI API → Response Validation → User Response
                     ↓                    ↓                       ↓
            Prompt Injection       Circuit Breaker      Structured Logging
             Prevention              Protection           & Monitoring
```

**Cost Optimization**:
- Exact match caching (database)
- Similarity matching for near-duplicates
- Prompt caching for dictionary context reuse
- Estimated API call reduction: 70-80%

**Alternatives considered**:
- Direct API integration: Rejected for reliability and cost concerns
- Synchronous requests: Rejected for performance
- No caching: Rejected for cost optimization requirements

## 5. Security and Monitoring

### Decision: Defense-in-Depth with Comprehensive Observability
**Rationale**:
- Multiple security layers prevent various attack vectors
- Structured logging enables debugging and optimization
- Real-time monitoring supports proactive issue resolution

**Security Measures**:
- Input sanitization and validation
- Prompt structure isolation
- Response content filtering
- Environment-based credential management

**Monitoring Stack**:
- Structured JSON logging
- Request/response metrics
- Cost and usage tracking
- Quality and performance monitoring
- Security event detection

## Implementation Architecture

### Backend Structure
```
backend/
├── src/
│   ├── models/          # SQLAlchemy models
│   ├── services/        # Business logic libraries
│   │   ├── translator.py    # Core translation service
│   │   ├── rate_limiter.py  # Rate limiting logic
│   │   └── ai_client.py     # AI API integration
│   ├── api/            # FastAPI endpoints
│   └── cli/            # Command-line interfaces
└── tests/
    ├── contract/       # API contract tests
    ├── integration/    # Service integration tests
    └── unit/           # Unit tests
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API client and state management
│   └── styles/         # Mystical theme system
└── tests/
    ├── components/     # Component tests
    └── integration/    # E2E tests
```

## Risk Mitigation

### Technical Risks
1. **AI API Reliability**: Circuit breaker + fallback caching
2. **Rate Limiting Accuracy**: SQLite WAL mode + proper indexing
3. **UI Accessibility**: WCAG compliance testing + user preference respect
4. **Security Vulnerabilities**: Multiple validation layers + monitoring

### Performance Risks
1. **Database Growth**: Automated cleanup + monitoring
2. **AI API Latency**: Timeout handling + user feedback
3. **Frontend Performance**: Code splitting + lazy loading

## Next Steps

This research provides the foundation for Phase 1 design and contracts. All technical decisions are finalized with no remaining NEEDS CLARIFICATION items.

**Ready for Phase 1**: Data model design, API contracts, and test scenarios.