# Tasks: Shathyar Language Translation Web Application

**Input**: Design documents from `/specs/001-ai-ai-shasiyaer/`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓), quickstart.md (✓)

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: FastAPI + React, SQLite, Python 3.11, TypeScript
   → Libraries: shathyar-translator, rate-limiter, dictionary-reader
   → Structure: Web app (backend/, frontend/)
2. Load optional design documents ✓
   → data-model.md: 4 entities → model tasks
   → contracts/api-spec.yaml: 4 endpoints → contract tests
   → quickstart.md: 6 workflows → integration tests
   → research.md: Architecture decisions → setup tasks
3. Generate tasks by category ✓
4. Apply task rules ✓
5. Number tasks sequentially (T001, T002...) ✓
6. Dependencies and parallel execution ✓
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Paths based on web app structure: `backend/src/`, `frontend/src/`

## Phase 3.1: Setup

- [ ] T001 Create project structure (backend/, frontend/, tests/, docs/)
- [ ] T002 Initialize Python backend with FastAPI, SQLAlchemy, Pydantic dependencies in backend/pyproject.toml
- [ ] T003 Initialize React frontend with TypeScript, React Query, Tailwind CSS dependencies in frontend/package.json  
- [ ] T004 [P] Configure backend linting (black, flake8, mypy) in backend/pyproject.toml
- [ ] T005 [P] Configure frontend linting (ESLint, Prettier, TypeScript) in frontend/.eslintrc.json
- [ ] T006 [P] Setup SQLite database initialization script in backend/scripts/init_db.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoints)
- [ ] T007 [P] Contract test POST /api/v1/translate in backend/tests/contract/test_translate_post.py
- [ ] T008 [P] Contract test POST /api/v1/translate/{id}/confirm in backend/tests/contract/test_confirm_post.py
- [ ] T009 [P] Contract test GET /api/v1/dictionary/search in backend/tests/contract/test_dictionary_get.py
- [ ] T010 [P] Contract test GET /api/v1/session/quota in backend/tests/contract/test_quota_get.py

### Integration Tests (User Workflows)
- [ ] T011 [P] Integration test Chinese→Shathyar translation workflow in backend/tests/integration/test_chinese_translation.py
- [ ] T012 [P] Integration test Shathyar→Chinese dictionary lookup in backend/tests/integration/test_shathyar_lookup.py
- [ ] T013 [P] Integration test AI translation editing and confirmation in backend/tests/integration/test_edit_translation.py
- [ ] T014 [P] Integration test rate limiting enforcement in backend/tests/integration/test_rate_limiting.py
- [ ] T015 [P] Integration test input validation and error handling in backend/tests/integration/test_validation.py
- [ ] T016 [P] Integration test translation not found scenario in backend/tests/integration/test_not_found.py

### Frontend Component Tests
- [ ] T017 [P] Test TranslationForm component in frontend/tests/components/TranslationForm.test.tsx
- [ ] T018 [P] Test MagicPowerIndicator component in frontend/tests/components/MagicPowerIndicator.test.tsx
- [ ] T019 [P] Test TranslationResult component in frontend/tests/components/TranslationResult.test.tsx
- [ ] T020 [P] Test ErrorDisplay component in frontend/tests/components/ErrorDisplay.test.tsx

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models (Parallel - different files)
- [ ] T021 [P] TranslationEntry model in backend/src/models/translation_entry.py
- [ ] T022 [P] OfficialDictionary model in backend/src/models/official_dictionary.py
- [ ] T023 [P] UserSession model in backend/src/models/user_session.py
- [ ] T024 [P] TranslationRequest model in backend/src/models/translation_request.py

### Service Libraries with CLI (Parallel - different files)
- [ ] T025 [P] ShathyarTranslator service with CLI in backend/src/services/shathyar_translator.py
- [ ] T026 [P] RateLimiter service with CLI in backend/src/services/rate_limiter.py  
- [ ] T027 [P] DictionaryReader service with CLI in backend/src/services/dictionary_reader.py
- [ ] T028 [P] AIClient service with circuit breaker in backend/src/services/ai_client.py

### API Endpoints (Sequential - shared dependency on services)
- [ ] T029 Translation endpoint POST /api/v1/translate in backend/src/api/translate.py
- [ ] T030 Confirmation endpoint POST /api/v1/translate/{id}/confirm in backend/src/api/translate.py
- [ ] T031 Dictionary search GET /api/v1/dictionary/search in backend/src/api/dictionary.py
- [ ] T032 Quota endpoint GET /api/v1/session/quota in backend/src/api/session.py

### Frontend Core Components (Parallel - different files)
- [ ] T033 [P] TranslationForm component in frontend/src/components/TranslationForm.tsx
- [ ] T034 [P] MagicPowerIndicator component in frontend/src/components/MagicPowerIndicator.tsx
- [ ] T035 [P] TranslationResult component in frontend/src/components/TranslationResult.tsx
- [ ] T036 [P] ErrorDisplay component in frontend/src/components/ErrorDisplay.tsx
- [ ] T037 [P] MysticalTheme CSS system in frontend/src/styles/mystical-theme.css

## Phase 3.4: Integration

### Backend Integration
- [ ] T038 Database connection and session management in backend/src/database.py
- [ ] T039 Rate limiting middleware integration in backend/src/middleware/rate_limit.py
- [ ] T040 CORS configuration and security headers in backend/src/main.py
- [ ] T041 Request/response logging with structured JSON in backend/src/middleware/logging.py

### Frontend Integration
- [ ] T042 API client with error handling in frontend/src/services/api-client.ts
- [ ] T043 React Query setup and cache configuration in frontend/src/services/query-client.ts
- [ ] T044 Main translation page integration in frontend/src/pages/TranslationPage.tsx
- [ ] T045 Global error boundary and mystical error handling in frontend/src/components/ErrorBoundary.tsx

## Phase 3.5: Polish

### Unit Tests (Parallel - different files)
- [ ] T046 [P] Unit tests for input validation in backend/tests/unit/test_validation.py
- [ ] T047 [P] Unit tests for AI prompt generation in backend/tests/unit/test_ai_prompts.py
- [ ] T048 [P] Unit tests for rate limiting logic in backend/tests/unit/test_rate_logic.py
- [ ] T049 [P] Unit tests for mystical UI helpers in frontend/tests/unit/mystical-helpers.test.ts

### Performance and Quality
- [ ] T050 Performance testing (translation <5s, rate limit <50ms) in backend/tests/performance/test_response_times.py
- [ ] T051 Load testing with 50+ concurrent users in backend/tests/performance/test_concurrent_load.py
- [ ] T052 Frontend accessibility testing (WCAG AA compliance) in frontend/tests/accessibility/test_a11y.py
- [ ] T053 End-to-end testing with quickstart scenarios in tests/e2e/test_quickstart_workflows.py

### Documentation and Deployment
- [ ] T054 [P] Update API documentation with OpenAPI schema in docs/api.md
- [ ] T055 [P] Create deployment configuration (Docker, docker-compose) in docker/
- [ ] T056 [P] Environment configuration guide in docs/setup.md
- [ ] T057 [P] CSV dictionary import script in backend/scripts/import_dictionary.py

## Dependencies

### Sequential Requirements
- **Setup (T001-T006)** → Tests (T007-T020) → Implementation (T021-T037) → Integration (T038-T045) → Polish (T046-T057)
- **T021-T024** (models) → T025-T028 (services) → T029-T032 (endpoints)
- **T025-T028** (services) → T038-T041 (backend integration)
- **T033-T037** (components) → T042-T045 (frontend integration)

### Parallel Execution Points
- **T007-T020**: All test files can be created in parallel
- **T021-T024**: All model files independent
- **T025-T028**: All service files independent  
- **T033-T037**: All frontend components independent
- **T046-T049**: All unit test files independent
- **T054-T057**: All documentation and deployment files independent

## Parallel Example
```
# Phase 3.2: Launch contract tests together
Task: "Contract test POST /api/v1/translate in backend/tests/contract/test_translate_post.py"
Task: "Contract test POST /api/v1/translate/{id}/confirm in backend/tests/contract/test_confirm_post.py"  
Task: "Contract test GET /api/v1/dictionary/search in backend/tests/contract/test_dictionary_get.py"
Task: "Contract test GET /api/v1/session/quota in backend/tests/contract/test_quota_get.py"

# Phase 3.3: Launch model creation together
Task: "TranslationEntry model in backend/src/models/translation_entry.py"
Task: "OfficialDictionary model in backend/src/models/official_dictionary.py"
Task: "UserSession model in backend/src/models/user_session.py"
Task: "TranslationRequest model in backend/src/models/translation_request.py"
```

## Critical TDD Requirements

### RED Phase Validation
Before implementing any code (T021+), verify:
1. All contract tests (T007-T010) return 404/500 errors
2. All integration tests (T011-T016) fail with import/connection errors
3. All frontend tests (T017-T020) fail with component not found errors

### Implementation Order
1. **Models first** (T021-T024) - Enable service layer
2. **Services next** (T025-T028) - Enable API endpoints
3. **Endpoints after** (T029-T032) - Make contract tests pass
4. **Frontend components** (T033-T037) - Enable integration
5. **Integration layer** (T038-T045) - Complete functionality

### Success Criteria
- All tests pass after implementation
- Quickstart guide workflows complete successfully
- Performance benchmarks met (<200ms translation response, <50ms rate limit)
- Mystical theme consistent throughout
- Rate limiting enforced accurately (500/day per IP)

## Task Generation Rules Applied

1. **From Contracts**: 4 endpoints → 4 contract test tasks (T007-T010) + 4 implementation tasks (T029-T032)
2. **From Data Model**: 4 entities → 4 model tasks (T021-T024)
3. **From Quickstart**: 6 workflows → 6 integration tests (T011-T016)
4. **From Research**: Architecture decisions → service libraries (T025-T028)

## Validation Checklist

- [x] All contracts have corresponding tests (T007-T010 → T029-T032)
- [x] All entities have model tasks (4 entities → T021-T024)
- [x] All tests come before implementation (T007-T020 before T021+)
- [x] Parallel tasks truly independent (different files, no shared state)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

**Total Tasks**: 57 tasks organized in 5 phases
**Estimated Timeline**: 15-20 days for solo implementation
**Critical Path**: Setup → Tests → Models → Services → Endpoints → Integration → Polish

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task completion
- Follow constitutional TDD principles strictly