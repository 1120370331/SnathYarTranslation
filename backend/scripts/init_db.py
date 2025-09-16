"""
Shathyar Translation Database Initialization Script

Creates SQLite database with all required tables for the translation application.
Imports official dictionary from shasiyaer.csv if available.
"""

import sqlite3
import csv
import hashlib
import sys
from pathlib import Path
from typing import Optional

# Database schema as defined in data-model.md
SCHEMA_SQL = """
-- Translation entries (user-generated translations)
CREATE TABLE IF NOT EXISTS translation_entries (
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
CREATE TABLE IF NOT EXISTS official_dictionary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_cn TEXT NOT NULL,
    shathyar TEXT NOT NULL,
    origin_en TEXT,
    created_at INTEGER DEFAULT (unixepoch()),
    checksum TEXT
);

-- Rate limiting sessions
CREATE TABLE IF NOT EXISTS user_sessions (
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
CREATE TABLE IF NOT EXISTS translation_requests (
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
CREATE INDEX IF NOT EXISTS idx_translation_entries_source 
    ON translation_entries(source_text, source_language);
CREATE INDEX IF NOT EXISTS idx_translation_entries_usage 
    ON translation_entries(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_official_dictionary_cn 
    ON official_dictionary(origin_cn);
CREATE INDEX IF NOT EXISTS idx_official_dictionary_shathyar 
    ON official_dictionary(shathyar);
CREATE INDEX IF NOT EXISTS idx_user_sessions_reset_time 
    ON user_sessions(daily_reset_time);
CREATE INDEX IF NOT EXISTS idx_translation_requests_created 
    ON translation_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_translation_requests_ip 
    ON translation_requests(ip_address, created_at);

-- Triggers for automatic timestamps
CREATE TRIGGER IF NOT EXISTS update_translation_entry_timestamp 
    AFTER UPDATE ON translation_entries
BEGIN
    UPDATE translation_entries 
    SET updated_at = unixepoch() 
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_session_activity
    AFTER UPDATE ON user_sessions  
BEGIN
    UPDATE user_sessions
    SET last_activity = unixepoch()
    WHERE ip_address = NEW.ip_address;
END;
"""

# SQLite optimization settings
PRAGMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = normal;
PRAGMA temp_store = memory;
PRAGMA cache_size = 10000;
PRAGMA foreign_keys = ON;
"""


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def import_dictionary(conn: sqlite3.Connection, csv_path: Optional[Path] = None) -> bool:
    """Import official dictionary from CSV file."""
    if not csv_path:
        # Look for shasiyaer.csv in common locations
        search_paths = [
            Path("shasiyaer.csv"),
            Path("data/shasiyaer.csv"),
            Path("../shasiyaer.csv"),
            Path("../../shasiyaer.csv"),
        ]
        
        for path in search_paths:
            if path.exists():
                csv_path = path
                break
        
        if not csv_path:
            print("Warning: shasiyaer.csv not found. Dictionary will be empty.")
            return False
    
    if not csv_path.exists():
        print(f"Error: Dictionary file {csv_path} not found.")
        return False
    
    # Calculate checksum
    checksum = calculate_file_checksum(csv_path)
    
    # Check if this version is already imported
    cursor = conn.execute(
        "SELECT COUNT(*) FROM official_dictionary WHERE checksum = ?", (checksum,)
    )
    if cursor.fetchone()[0] > 0:
        print(f"Dictionary {csv_path} already imported (checksum match).")
        return True
    
    # Clear existing entries (new version)
    conn.execute("DELETE FROM official_dictionary")
    
    # Import new entries
    imported_count = 0
    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            # Auto-detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Validate expected columns
            expected_cols = {"origin_CN", "Snathyar", "origin_EN"}
            if not expected_cols.issubset(set(reader.fieldnames or [])):
                print(f"Error: CSV must contain columns: {expected_cols}")
                return False
            
            # Import rows
            for row in reader:
                origin_cn = row["origin_CN"].strip()
                shathyar = row["Snathyar"].strip()
                origin_en = row.get("origin_EN", "").strip() or None
                
                if origin_cn and shathyar:  # Both required fields must be present
                    conn.execute(
                        """
                        INSERT INTO official_dictionary 
                        (origin_cn, shathyar, origin_en, checksum)
                        VALUES (?, ?, ?, ?)
                        """,
                        (origin_cn, shathyar, origin_en, checksum)
                    )
                    imported_count += 1
        
        conn.commit()
        print(f"Successfully imported {imported_count} dictionary entries from {csv_path}")
        return True
        
    except Exception as e:
        print(f"Error importing dictionary: {e}")
        conn.rollback()
        return False


def init_database(db_path: Path, csv_path: Optional[Path] = None) -> bool:
    """Initialize the Shathyar translation database."""
    try:
        # Create database connection
        conn = sqlite3.connect(str(db_path))
        
        # Apply optimization settings
        conn.executescript(PRAGMA_SQL)
        
        # Create schema
        conn.executescript(SCHEMA_SQL)
        
        print(f"Database schema created at: {db_path}")
        
        # Import dictionary if available
        import_dictionary(conn, csv_path)
        
        # Verify schema
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        print(f"Created tables: {[t[0] for t in tables]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Shathyar translation database")
    parser.add_argument(
        "--db-path", 
        type=Path, 
        default=Path("shathyar.db"),
        help="Database file path (default: shathyar.db)"
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        help="Path to shasiyaer.csv dictionary file"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recreate database if it exists"
    )
    
    args = parser.parse_args()
    
    # Check if database exists
    if args.db_path.exists() and not args.force:
        print(f"Database {args.db_path} already exists. Use --force to recreate.")
        sys.exit(1)
    
    # Remove existing database if force is specified
    if args.force and args.db_path.exists():
        args.db_path.unlink()
        print(f"Removed existing database: {args.db_path}")
    
    # Initialize database
    success = init_database(args.db_path, args.csv_path)
    
    if success:
        print("✓ Database initialization completed successfully")
        sys.exit(0)
    else:
        print("✗ Database initialization failed")
        sys.exit(1)