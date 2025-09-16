# Implementation Plan: Shathyar Language Translation Web Application

**Branch**: `001-ai-ai-shasiyaer` | **Date**: 2025-09-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-ai-shasiyaer/spec.md`
**User Context**: 实现如@PRD.md中所述的网页功能

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✓
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below ✓
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md [IN PROGRESS]
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Bidirectional Chinese-Shathyar translation web application with AI-powered translation generation, rate limiting, mystical UI design, and integration with World of Warcraft's fictional language dictionary. Technical approach involves web application with backend API and frontend interface, leveraging external AI service for translation generation.

## Technical Context
**Language/Version**: Python 3.11 (backend), JavaScript/TypeScript (frontend)  
**Primary Dependencies**: FastAPI (backend), React (frontend), SQLite (database)  
**Storage**: SQLite database + CSV file (shasiyaer.csv dictionary)  
**Testing**: pytest (backend), Jest/React Testing Library (frontend)  
**Target Platform**: Web browsers + Linux/Windows server
**Project Type**: web - determines frontend+backend structure  
**Performance Goals**: <200ms translation response time, handle 500 requests/day per IP  
**Constraints**: 500 character input limit, 500 translations per IP per day, AI service integration  
**Scale/Scope**: Single-user web app, mystical UI theme, rate limiting by IP

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (backend API, frontend web app)
- Using framework directly? Yes (FastAPI, React without wrapper layers)
- Single data model? Yes (shared entities between frontend/backend)
- Avoiding patterns? Yes (direct SQLite access, no Repository/UoW)

**Architecture**:
- EVERY feature as library? Yes (translation-lib, rate-limit-lib, ui-components-lib)
- Libraries listed: 
  - shathyar-translator (core translation logic + CLI)
  - rate-limiter (IP-based rate limiting + CLI)
  - dictionary-reader (CSV dictionary access + CLI)
- CLI per library: --help/--version/--format supported
- Library docs: llms.txt format planned? Yes

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes (test MUST fail first)
- Git commits show tests before implementation? Yes
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes (actual SQLite DB, real AI API calls in integration tests)
- Integration tests for: new libraries, contract changes, shared schemas? Yes
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? Yes (JSON logs with correlation IDs)
- Frontend logs → backend? Yes (unified log stream via API)
- Error context sufficient? Yes (full request context, stack traces)

**Versioning**:
- Version number assigned? 1.0.1 (MAJOR.MINOR.BUILD)
- BUILD increments on every change? Yes
- Breaking changes handled? Yes (API versioning strategy)

## Project Structure

### Documentation (this feature)
```
specs/001-ai-ai-shasiyaer/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/
```

**Structure Decision**: Option 2 (Web application) - frontend + backend detected from requirements

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - No NEEDS CLARIFICATION remaining - all tech choices specified
   - Research tasks: AI integration patterns, rate limiting strategies, mystical UI design patterns

2. **Generate and dispatch research agents**:
   ```
   Task: "Research FastAPI + React integration patterns for translation applications"
   Task: "Research IP-based rate limiting implementation with SQLite"
   Task: "Research mystical/Cthulhu UI design patterns and color schemes"
   Task: "Research AI API integration best practices for external services"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Translation Entry, Official Dictionary Record, User Session, Translation Request
   - Validation rules from FR-010, FR-011, FR-012
   - State transitions for translation workflow

2. **Generate API contracts** from functional requirements:
   - POST /api/translate (FR-001, FR-002, FR-005)
   - GET /api/dictionary/search (FR-004, FR-009) 
   - GET /api/session/quota (FR-011)
   - Output OpenAPI schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each acceptance scenario → integration test scenario
   - Quickstart test = translation workflow validation

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh claude` for Claude Code
   - Add FastAPI, React, SQLite context
   - Update with translation domain knowledge
   - Keep under 150 lines for token efficiency

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each API contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Library creation tasks for shathyar-translator, rate-limiter, dictionary-reader
- Frontend component tasks for mystical UI
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models → Services → API → Frontend → Integration
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations identified - all checks passed*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*