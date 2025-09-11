# Data Model: Shathyar Translation Application

**Date**: 2025-09-11
**Phase**: Phase 1 - Data Model Design
**Based on**: research.md findings and feature specification

## Core Entities

### 1. Translation Entry
Represents a Chinese-Shathyar translation pair stored in the system database.

**Attributes**:
- `id`: Primary key (UUID)
- `source_text`: Original text input (VARCHAR 500, NOT NULL)
- `translated_text`: Generated or confirmed Shathyar translation (VARCHAR 1000, NOT NULL)
- `source_language`: Language direction ("chinese" or "shathyar", NOT NULL)
- `is_ai_generated`: Boolean flag indicating AI vs dictionary source
- `is_user_confirmed`: Boolean flag for user-edited AI translations
- `confidence_score`: AI translation confidence (DECIMAL 0-1, nullable)
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last modification
- `usage_count`: Number of times this translation was served (for analytics)

**Relationships**:
- May be referenced by multiple TranslationRequest records
- Links to User Session through request history

**Validation Rules** (from FR-012):
- `source_text` maximum length: 500 characters
- `source_language` must be "chinese" or "shathyar"
- Both `source_text` and `translated_text` required (NOT NULL)

**State Transitions**:
```
AI Generated → User Editing → User Confirmed
     ↓              ↓              ↓
   Draft         Modified        Final
```

### 2. Official Dictionary Record
Represents entries from the official shasiyaer.csv file (read-only reference data).

**Attributes**:
- `id`: Primary key (auto-increment)
- `origin_cn`: Original Chinese text (VARCHAR 500, NOT NULL)
- `shathyar`: Shathyar translation (VARCHAR 500, NOT NULL)
- `origin_en`: Original English text (VARCHAR 500, nullable)
- `created_at`: Import timestamp
- `checksum`: File integrity verification

**Relationships**:
- Used as reference by Translation Service
- May be matched against user input for exact lookups

**Validation Rules** (from FR-004):
- Authoritative source for Shathyar-to-Chinese translations
- Read-only after import (immutable reference data)
- Used for exact matching before AI generation

### 3. User Session
Tracks IP-based sessions for rate limiting and usage analytics.

**Attributes**:
- `ip_address`: Client IP address (BINARY, PRIMARY KEY)
- `tokens_remaining`: Current translation quota (INTEGER, NOT NULL)
- `last_refill_time`: Unix timestamp of last token refill
- `daily_reset_time`: Unix timestamp of next daily reset  
- `first_seen`: Timestamp of first session
- `last_activity`: Timestamp of most recent activity
- `total_translations`: Lifetime translation count
- `blocked_until`: Temporary ban timestamp (nullable)

**Relationships**:
- Associates with multiple TranslationRequest records
- Used by Rate Limiting Service

**Validation Rules** (from FR-010, FR-011):
- Daily limit: 500 translations per IP address
- `tokens_remaining` range: 0-500
- Automatic daily reset at midnight UTC

**State Transitions**:
```
New Session → Active → Rate Limited → Daily Reset → Active
     ↓          ↓           ↓             ↓          ↓
   500 tokens  Consuming   0 tokens    Reset    500 tokens
```

### 4. Translation Request  
Represents a single translation attempt with full context and results.

**Attributes**:
- `id`: Primary key (UUID)
- `ip_address`: Client IP (links to User Session)
- `input_text`: User input text (VARCHAR 500, NOT NULL)
- `input_language`: Selected input language ("chinese" or "shathyar")
- `output_text`: Final translation result (VARCHAR 1000)
- `processing_status`: Current request state (enum)
- `cache_hit`: Boolean indicating if served from cache
- `ai_response_time_ms`: AI API response time (nullable)
- `tokens_used`: AI API token consumption (nullable)
- `cost_usd`: Request processing cost (nullable)
- `error_message`: Error details if failed (nullable)
- `created_at`: Request timestamp
- `completed_at`: Processing completion timestamp

**Relationships**:
- Links to User Session via `ip_address`
- May reference Translation Entry for cached results
- Used for analytics and monitoring

**Validation Rules**:
- `input_text` maximum length: 500 characters (from FR-012)
- `input_language` must be "chinese" or "shathyar"
- `processing_status` enum values: pending, processing, completed, failed, rate_limited

**Processing States**:
```
Pending → Processing → [Cache Check] → [AI Call] → Completed
   ↓         ↓             ↓              ↓         ↓
Request   Validating   Cache Hit    AI Response  Success
Created               Cache Miss   or Timeout   or Error
```

## Database Schema

### SQLite Implementation (Development/Small Scale)
```sql
-- Translation entries (user-generated translations)
CREATE TABLE translation_entries (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    source_text TEXT NOT NULL CHECK(length(source_text) <= 500),
    translated_text TEXT NOT NULL CHECK(length(translated_text) <= 1000),
    source_language TEXT NOT NULL CHECK(source_language IN ('chinese', 'shathyar')),
    is_ai_generated BOOLEAN NOT NULL DEFAULT 1,
    is_user_confirmed BOOLEAN NOT NULL DEFAULT 0,
    confidence_score REAL CHECK(confidence_score BETWEEN 0 AND 1),
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch()),
    usage_count INTEGER DEFAULT 0
);

-- Official dictionary (imported from shasiyaer.csv)
CREATE TABLE official_dictionary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_cn TEXT NOT NULL,
    shathyar TEXT NOT NULL,
    origin_en TEXT,
    created_at INTEGER DEFAULT (unixepoch()),
    checksum TEXT
);

-- Rate limiting sessions
CREATE TABLE user_sessions (
    ip_address BLOB PRIMARY KEY,
    tokens_remaining INTEGER NOT NULL DEFAULT 500 CHECK(tokens_remaining BETWEEN 0 AND 500),
    last_refill_time INTEGER NOT NULL DEFAULT (unixepoch()),
    daily_reset_time INTEGER NOT NULL,
    first_seen INTEGER DEFAULT (unixepoch()),
    last_activity INTEGER DEFAULT (unixepoch()),
    total_translations INTEGER DEFAULT 0,
    blocked_until INTEGER
);

-- Translation request log
CREATE TABLE translation_requests (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    ip_address BLOB NOT NULL,
    input_text TEXT NOT NULL CHECK(length(input_text) <= 500),
    input_language TEXT NOT NULL CHECK(input_language IN ('chinese', 'shathyar')),
    output_text TEXT,
    processing_status TEXT NOT NULL DEFAULT 'pending' 
        CHECK(processing_status IN ('pending', 'processing', 'completed', 'failed', 'rate_limited')),
    cache_hit BOOLEAN DEFAULT 0,
    ai_response_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd REAL,
    error_message TEXT,
    created_at INTEGER DEFAULT (unixepoch()),
    completed_at INTEGER,
    FOREIGN KEY (ip_address) REFERENCES user_sessions(ip_address)
);

-- Indexes for performance
CREATE INDEX idx_translation_entries_source ON translation_entries(source_text, source_language);
CREATE INDEX idx_translation_entries_usage ON translation_entries(usage_count DESC);
CREATE INDEX idx_official_dictionary_cn ON official_dictionary(origin_cn);
CREATE INDEX idx_official_dictionary_shathyar ON official_dictionary(shathyar);
CREATE INDEX idx_user_sessions_reset_time ON user_sessions(daily_reset_time);
CREATE INDEX idx_translation_requests_created ON translation_requests(created_at);
CREATE INDEX idx_translation_requests_ip ON translation_requests(ip_address, created_at);

-- Triggers for automatic timestamps
CREATE TRIGGER update_translation_entry_timestamp 
    AFTER UPDATE ON translation_entries
BEGIN
    UPDATE translation_entries 
    SET updated_at = unixepoch() 
    WHERE id = NEW.id;
END;

CREATE TRIGGER update_user_session_activity
    AFTER UPDATE ON user_sessions  
BEGIN
    UPDATE user_sessions
    SET last_activity = unixepoch()
    WHERE ip_address = NEW.ip_address;
END;
```

## Data Access Patterns

### High-Frequency Operations
1. **Rate Limit Check**: Query user_sessions by ip_address (~100-500/hour)
2. **Translation Lookup**: Search translation_entries by source_text (~50-200/hour)
3. **Dictionary Search**: Query official_dictionary by origin_cn or shathyar (~50-200/hour)

### Medium-Frequency Operations  
1. **New Translation Storage**: Insert into translation_entries (~10-50/hour)
2. **Request Logging**: Insert into translation_requests (~100-500/hour)
3. **Session Updates**: Update user_sessions tokens (~100-500/hour)

### Low-Frequency Operations
1. **Dictionary Import**: Bulk insert into official_dictionary (daily/weekly)
2. **Cleanup Operations**: Delete old translation_requests (daily)
3. **Analytics Queries**: Complex aggregations (on-demand)

## Data Integrity Constraints

### Business Rules
- Translation entries must have both source and translated text
- Rate limiting strictly enforced at database level
- Official dictionary is immutable after import
- All timestamps use UTC Unix epochs

### Referential Integrity
- Translation requests must reference valid user sessions
- Cascade delete policies for cleanup operations
- Foreign key constraints maintain data consistency

### Performance Considerations
- Indexes optimized for common query patterns
- WAL mode enables concurrent access
- Automatic cleanup prevents unbounded growth

This data model supports all functional requirements while maintaining performance, integrity, and scalability for the expected usage patterns.