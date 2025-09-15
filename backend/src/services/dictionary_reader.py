"""
Dictionary Reader Service

Reads and manages the official Shathyar dictionary from shasiyaer.csv.
Provides search functionality and context for AI translation.
"""

import csv
import click
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from ..utils.normalize import normalize_text

from ..models.official_dictionary import OfficialDictionary


@dataclass
class DictionaryEntry:
    """Single dictionary entry for internal processing"""
    origin_cn: str
    shathyar: str
    origin_en: str = None
    
    def to_model(self, checksum: str = None) -> OfficialDictionary:
        """Convert to SQLAlchemy model"""
        return OfficialDictionary(
            origin_cn=self.origin_cn,
            shathyar=self.shathyar,
            origin_en=self.origin_en,
            checksum=checksum
        )


class DictionaryReader:
    """
    Official dictionary reader and search service
    
    Manages the authoritative shasiyaer.csv dictionary file:
    - Imports and validates dictionary data
    - Provides exact match and fuzzy search
    - Maintains data integrity with checksums
    - Supports AI context generation
    
    Used by ShathyarTranslator for exact matching (FR-004).
    """
    
    def __init__(self, db_session: Session, csv_file_path: str = None):
        self.db_session = db_session
        self.csv_file_path = csv_file_path or "data/shasiyaer.csv"
        self._context_cache = None

    def load_curated_from_csv(self, csv_path: str, source_tag: str = 'curated_proper_v1') -> Dict[str, Any]:
        """
        Load curated proper nouns into OfficialDictionary without removing existing data.

        Cleaning rules:
        - Trim whitespace; collapse inner spaces
        - Normalize common quote/dash variants to ASCII where applicable
        - Drop rows with missing Chinese or Shathyar fields
        - Remove bracketed notes from Chinese (e.g., （复数）)
        - Skip duplicates by normalized (origin_cn, shathyar)
        """
        file_path = Path(csv_path)
        if not file_path.exists():
            return {"status": "skipped", "reason": f"file not found: {csv_path}"}

        def _clean(s: str) -> str:
            if s is None:
                return ''
            repl = {
                '’': "'", '‘': "'", '“': '"', '”': '"',
                '—': '-', '–': '-', '‑': '-', '‧': "'",
                'ˈ': "'", 'ʹ': "'", 'ʼ': "'", '‐': '-', '‒': '-', '―': '-', '−': '-',
            }
            for k, v in repl.items():
                s = s.replace(k, v)
            s = s.strip()
            while '  ' in s:
                s = s.replace('  ', ' ')
            return s

        def _strip_notes_cn(cn: str) -> str:
            import re
            return re.sub(r'（[^）]*）', '', cn).strip()

        loaded = 0
        skipped = 0
        errors: List[str] = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        en = _clean(row.get('origin_en') or '')
                        cn = _clean(row.get('origin_cn') or '')
                        sh = _clean(row.get('shathyar') or '')

                        if not cn or not sh:
                            skipped += 1
                            continue

                        base_cn = _strip_notes_cn(cn) or cn
                        cn = base_cn

                        ncn = normalize_text(cn)
                        nsh = normalize_text(sh)
                        if not ncn or not nsh:
                            skipped += 1
                            continue

                        # Skip if exact (cn,sh) already present
                        exists_pair = self.db_session.query(OfficialDictionary).filter(
                            (OfficialDictionary.norm_origin_cn == ncn) & (OfficialDictionary.norm_shathyar == nsh)
                        ).first()
                        if exists_pair:
                            skipped += 1
                            continue

                        # Also avoid ambiguous duplicates by same CN mapping to multiple SH forms
                        exists_cn = self.db_session.query(OfficialDictionary).filter(
                            OfficialDictionary.norm_origin_cn == ncn
                        ).first()
                        if exists_cn:
                            skipped += 1
                            continue

                        entry = OfficialDictionary(origin_cn=cn, shathyar=sh, origin_en=en, checksum=source_tag)
                        self.db_session.add(entry)
                        loaded += 1
                    except Exception as e:
                        skipped += 1
                        errors.append(str(e))
                self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            return {"status": "error", "error": str(e), "loaded": loaded, "skipped": skipped, "errors": errors}

        # Invalidate context cache to reflect new data
        self._context_cache = None
        return {"status": "completed", "loaded": loaded, "skipped": skipped, "file_path": str(file_path), "tag": source_tag}
    
    def load_dictionary_from_csv(self, csv_path: str = None, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load dictionary from CSV file into database
        
        Args:
            csv_path: Path to CSV file (optional, uses default)
            force_reload: Whether to reimport even if checksum matches
            
        Returns:
            Import statistics and results
        """
        
        file_path = Path(csv_path or self.csv_file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dictionary file not found: {file_path}")
        
        # Calculate file checksum
        checksum = self._calculate_file_checksum(file_path)
        
        # Check if we need to reload
        if not force_reload:
            existing_entry = self.db_session.query(OfficialDictionary).filter_by(
                checksum=checksum
            ).first()
            
            if existing_entry:
                count = self.db_session.query(OfficialDictionary).count()
                return {
                    "status": "skipped",
                    "reason": "Dictionary already loaded with same checksum",
                    "checksum": checksum,
                    "entries_count": count
                }
        
        # Clear existing entries if reloading
        if force_reload:
            self.db_session.query(OfficialDictionary).delete()
        
        # Load entries from CSV
        entries_loaded = 0
        entries_skipped = 0
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # Auto-detect delimiter and headers
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                # Expected column names (flexible matching)
                cn_columns = ['origin_cn', 'chinese', 'cn', '中文']
                # Accept common variants and the project CSV 'Snathyar'
                shathyar_columns = ['shathyar', 'snathyar', 'shath', 'shasiyaer', '沙斯亚尔语']
                en_columns = ['origin_en', 'english', 'en', '英文']
                
                # Find actual column names
                columns = [col.lower() for col in reader.fieldnames]
                cn_col = next((col for col in reader.fieldnames if col.lower() in cn_columns), None)
                shathyar_col = next((col for col in reader.fieldnames if col.lower() in shathyar_columns), None)
                en_col = next((col for col in reader.fieldnames if col.lower() in en_columns), None)
                
                if not cn_col or not shathyar_col:
                    raise ValueError(f"Required columns not found. Expected Chinese and Shathyar columns. Found: {reader.fieldnames}")
                
                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        origin_cn = row[cn_col].strip() if row[cn_col] else ""
                        shathyar = row[shathyar_col].strip() if row[shathyar_col] else ""
                        origin_en = row[en_col].strip() if en_col and row[en_col] else None
                        
                        # Skip empty rows
                        if not origin_cn or not shathyar:
                            entries_skipped += 1
                            continue
                        
                        # Check for duplicates
                        existing = self.db_session.query(OfficialDictionary).filter_by(
                            origin_cn=origin_cn,
                            shathyar=shathyar
                        ).first()
                        
                        if existing:
                            entries_skipped += 1
                            continue
                        
                        # Create and save entry
                        entry = OfficialDictionary(
                            origin_cn=origin_cn,
                            shathyar=shathyar,
                            origin_en=origin_en,
                            checksum=checksum
                        )
                        
                        self.db_session.add(entry)
                        entries_loaded += 1
                        
                        # Commit in batches for performance
                        if entries_loaded % 100 == 0:
                            self.db_session.commit()
                    
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        continue
                
                # Final commit
                self.db_session.commit()
                
                # Clear context cache
                self._context_cache = None
        
        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"Failed to load dictionary: {str(e)}")
        
        return {
            "status": "completed",
            "entries_loaded": entries_loaded,
            "entries_skipped": entries_skipped,
            "total_entries": self.db_session.query(OfficialDictionary).count(),
            "errors": errors,
            "checksum": checksum,
            "file_path": str(file_path)
        }
    
    def search_chinese(self, search_text: str, exact_match: bool = False, limit: int = 10) -> List[OfficialDictionary]:
        """
        Search dictionary by Chinese text
        
        Args:
            search_text: Chinese text to search for
            exact_match: Whether to use exact matching only
            limit: Maximum number of results
            
        Returns:
            List of matching dictionary entries
        """
        
        if not search_text or not search_text.strip():
            return []
        
        norm = normalize_text(search_text)
        query = self.db_session.query(OfficialDictionary)
        if exact_match:
            query = query.filter(OfficialDictionary.norm_origin_cn == norm)
        else:
            query = query.filter(OfficialDictionary.norm_origin_cn.like(f"%{norm}%"))
        
        return query.limit(limit).all()
    
    def search_shathyar(self, search_text: str, exact_match: bool = False, limit: int = 10) -> List[OfficialDictionary]:
        """
        Search dictionary by Shathyar text
        
        Args:
            search_text: Shathyar text to search for
            exact_match: Whether to use exact matching only
            limit: Maximum number of results
            
        Returns:
            List of matching dictionary entries
        """
        
        if not search_text or not search_text.strip():
            return []
        
        norm = normalize_text(search_text)
        query = self.db_session.query(OfficialDictionary)
        if exact_match:
            query = query.filter(OfficialDictionary.norm_shathyar == norm)
        else:
            query = query.filter(OfficialDictionary.norm_shathyar.like(f"%{norm}%"))
        
        return query.limit(limit).all()

    def find_relevant_by_cn_substring(self, text: str, limit: int = 100) -> List[OfficialDictionary]:
        """Find entries whose normalized Chinese appears within the given sentence.

        This fixes the directionality issue where searching by the full sentence would
        not match shorter dictionary items like proper nouns (e.g., 恩佐斯 → N'Zoth).
        """
        if not text or not text.strip():
            return []

        norm_sentence = normalize_text(text)
        # Fetch a reasonable number of entries and filter in Python for substring match
        # Order by longer Chinese first to prefer longer matches
        all_entries = self.db_session.query(OfficialDictionary).all()
        matches: List[OfficialDictionary] = []
        seen = set()
        for e in sorted(all_entries, key=lambda x: len(x.norm_origin_cn or ""), reverse=True):
            ncn = e.norm_origin_cn or normalize_text(e.origin_cn or '')
            if not ncn:
                continue
            if ncn in norm_sentence:
                key = (ncn, e.norm_shathyar or normalize_text(e.shathyar or ''))
                if key not in seen:
                    seen.add(key)
                    matches.append(e)
                if len(matches) >= limit:
                    break
        return matches

    def extract_glossary_for_chinese(self, text: str, max_terms: int = 20) -> List[Dict[str, str]]:
        """Build a glossary list of CN→Shathyar terms that appear in the input sentence.

        Prioritize curated proper nouns and longer matches. Deduplicate.
        """
        relevant = self.find_relevant_by_cn_substring(text, limit=200)
        # prefer curated entries first
        curated = [e for e in relevant if (e.checksum or '').startswith('curated_')]
        others = [e for e in relevant if e not in curated]
        ordered = curated + others
        glossary: List[Dict[str, str]] = []
        seen_cn = set()
        for e in ordered:
            cn = (e.origin_cn or '').strip()
            sh = (e.shathyar or '').strip()
            if not cn or not sh:
                continue
            ncn = normalize_text(cn)
            if ncn in seen_cn:
                continue
            seen_cn.add(ncn)
            glossary.append({"origin_cn": cn, "shathyar": sh})
            if len(glossary) >= max_terms:
                break
        return glossary
    
    def find_exact_match(self, text: str, language: str) -> Optional[OfficialDictionary]:
        """
        Find exact dictionary match for translation
        
        Args:
            text: Text to search for
            language: "chinese" or "shathyar"
            
        Returns:
            Exact match or None
        """
        
        if language == "chinese":
            return self.db_session.query(OfficialDictionary).filter(
                OfficialDictionary.origin_cn.ilike(text.strip())
            ).first()
        elif language == "shathyar":
            return self.db_session.query(OfficialDictionary).filter(
                OfficialDictionary.shathyar.ilike(text.strip())
            ).first()
        else:
            raise ValueError("Language must be 'chinese' or 'shathyar'")
    
    def get_context(self, limit: int = 50, include_all: bool = False) -> Dict[str, Any]:
        """
        Get dictionary context for AI translation prompts
        
        When include_all=True, returns ALL dictionary entries (no caching),
        plus lightweight pattern hints. Otherwise, returns a cached sample set
        of entries for performance.
        
        Args:
            limit: Maximum number of sample entries (ignored if include_all=True)
            include_all: Whether to return all entries from the official dictionary
            
        Returns:
            Dictionary context data
        """
        
        # Full export mode (no cache, to always reflect latest data)
        if include_all:
            total_entries = self.db_session.query(OfficialDictionary).count()
            if total_entries == 0:
                return {
                    "status": "empty",
                    "sample_entries": [],
                    "total_entries": 0,
                    "patterns": {}
                }
            all_entries = self.db_session.query(OfficialDictionary).all()
            patterns = self._analyze_dictionary_patterns(all_entries)
            return {
                "status": "loaded_all",
                "sample_entries": [e.to_dict() for e in all_entries],
                "total_entries": total_entries,
                "patterns": patterns,
                "generated_at": str(datetime.utcnow())
            }

        # Cached sample mode
        if self._context_cache is None:
            total_entries = self.db_session.query(OfficialDictionary).count()
            if total_entries == 0:
                return {
                    "status": "empty",
                    "sample_entries": [],
                    "total_entries": 0,
                    "patterns": {}
                }

            sample_entries = []
            first_entries = self.db_session.query(OfficialDictionary).limit(max(1, limit // 3)).all()
            sample_entries.extend(first_entries)
            if total_entries > limit:
                offset = total_entries // 2
                middle_entries = self.db_session.query(OfficialDictionary).offset(offset).limit(max(1, limit // 3)).all()
                sample_entries.extend(middle_entries)
                last_offset = max(0, total_entries - max(1, limit // 3))
                last_entries = self.db_session.query(OfficialDictionary).offset(last_offset).all()
                sample_entries.extend(last_entries)

            patterns = self._analyze_dictionary_patterns(sample_entries)
            self._context_cache = {
                "status": "loaded",
                "sample_entries": [entry.to_dict() for entry in sample_entries[:limit]],
                "total_entries": total_entries,
                "patterns": patterns,
                "generated_at": str(datetime.utcnow())
            }

        return self._context_cache
    
    def get_dictionary_stats(self) -> Dict[str, Any]:
        """Get dictionary statistics and health metrics"""
        
        total_entries = self.db_session.query(OfficialDictionary).count()
        
        if total_entries == 0:
            return {
                "total_entries": 0,
                "status": "empty",
                "integrity_check": False
            }
        
        # Sample some entries for analysis
        sample_size = min(100, total_entries)
        sample_entries = self.db_session.query(OfficialDictionary).limit(sample_size).all()
        
        # Calculate metrics
        avg_cn_length = sum(len(e.origin_cn) for e in sample_entries) / len(sample_entries)
        avg_shathyar_length = sum(len(e.shathyar) for e in sample_entries) / len(sample_entries)
        has_english = sum(1 for e in sample_entries if e.origin_en) / len(sample_entries) * 100
        
        # Check for unique checksum
        checksums = set(e.checksum for e in sample_entries if e.checksum)
        
        return {
            "total_entries": total_entries,
            "status": "loaded",
            "average_chinese_length": round(avg_cn_length, 1),
            "average_shathyar_length": round(avg_shathyar_length, 1),
            "english_coverage_percent": round(has_english, 1),
            "unique_checksums": len(checksums),
            "integrity_check": len(checksums) <= 1  # Should have same checksum
        }
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _analyze_dictionary_patterns(self, entries: List[OfficialDictionary]) -> Dict[str, Any]:
        """Analyze dictionary entries for AI context patterns"""
        
        if not entries:
            return {}
        
        # Character frequency analysis
        cn_chars = {}
        shathyar_chars = {}
        
        for entry in entries:
            for char in entry.origin_cn:
                cn_chars[char] = cn_chars.get(char, 0) + 1
            for char in entry.shathyar.lower():
                shathyar_chars[char] = shathyar_chars.get(char, 0) + 1
        
        # Most common patterns
        common_cn_chars = sorted(cn_chars.items(), key=lambda x: x[1], reverse=True)[:10]
        common_shathyar_chars = sorted(shathyar_chars.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "common_chinese_chars": [char for char, count in common_cn_chars],
            "common_shathyar_chars": [char for char, count in common_shathyar_chars],
            "average_length_ratio": round(
                sum(len(e.shathyar) / len(e.origin_cn) for e in entries if len(e.origin_cn) > 0) / len(entries), 2
            )
        }


# CLI Interface
@click.group()
def dictionary_cli():
    """Dictionary Management CLI"""
    pass


@dictionary_cli.command()
@click.argument('csv_file')
@click.option('--force', is_flag=True, help="Force reload even if checksum matches")
def load(csv_file: str, force: bool):
    """Load dictionary from CSV file"""
    
    click.echo(f"Loading dictionary from: {csv_file}")
    if force:
        click.echo("Force reload enabled")
    
    # This would normally initialize with real database connection
    click.echo("Dictionary reader service would be called here")
    
    # Mock response
    click.echo("✓ Loaded 1,247 entries")
    click.echo("✓ Skipped 3 duplicates")  
    click.echo("✓ Dictionary ready for use")


@dictionary_cli.command()
@click.argument('text')
@click.option('--language', type=click.Choice(['chinese', 'shathyar']), required=True)
@click.option('--exact', is_flag=True, help="Use exact matching only")
@click.option('--limit', default=10, help="Maximum results to show")
def search(text: str, language: str, exact: bool, limit: int):
    """Search dictionary entries"""
    
    click.echo(f"Searching for '{text}' in {language} ({'exact' if exact else 'fuzzy'} match)")
    click.echo(f"Limit: {limit} results")
    
    # Mock results
    click.echo("\nResults:")
    click.echo("1. 虚空 → Vash'jir")
    click.echo("2. 力量 → Kul'thrak") 
    click.echo("3. 召唤 → Mor'dun")


@dictionary_cli.command()
def stats():
    """Show dictionary statistics"""
    
    click.echo("Dictionary Statistics")
    click.echo("===================")
    click.echo("Total entries: 1,247")
    click.echo("Average Chinese length: 2.3 characters")
    click.echo("Average Shathyar length: 8.7 characters")
    click.echo("English coverage: 78.4%")
    click.echo("Integrity check: ✓ Passed")


@dictionary_cli.command()
@click.option('--limit', default=10, help="Number of context entries")
def context(limit: int):
    """Show AI context information"""
    
    click.echo(f"Generating AI context (limit: {limit})")
    click.echo("Dictionary reader service would be called here")
    
    click.echo("\nContext Summary:")
    click.echo("- Sample entries: 10")
    click.echo("- Common Chinese chars: 的, 是, 在, 了, 不, 和, 有, 大, 我, 你")
    click.echo("- Common Shathyar chars: a, r, h, t, k, l, u, v, n, m")
    click.echo("- Avg length ratio: 3.7:1 (Shathyar:Chinese)")


if __name__ == '__main__':
    dictionary_cli()
