"""
Shathyar Translator Service

Core translation logic with CLI interface.
Implements the main translation workflow with caching, AI integration, and dictionary lookup.
"""

import asyncio
import click
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from ..models.translation_entry import TranslationEntry
from ..models.official_dictionary import OfficialDictionary
import re
import string
from ..utils.normalize import normalize_text


class TranslationSource(Enum):
    """Source of translation result"""
    CACHE = "cache"
    DICTIONARY = "dictionary"
    AI_GENERATED = "ai_generated"


@dataclass
class TranslationResult:
    """Result of translation operation"""
    translated_text: str
    source_text: str
    source: TranslationSource
    is_cached: bool
    is_ai_generated: bool
    can_edit: bool
    confidence_score: Optional[float] = None
    translation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "translated_text": self.translated_text,
            "source_text": self.source_text,
            "is_cached": self.is_cached,
            "is_ai_generated": self.is_ai_generated,
            "can_edit": self.can_edit,
            "confidence_score": self.confidence_score,
            "translation_id": self.translation_id
        }


class ShathyarTranslator:
    """
    Core translation service implementing the complete workflow:
    
    1. Check database cache for existing translations (FR-003)
    2. Check official dictionary for exact matches (FR-004)
    3. Generate AI translation if needed (FR-005)
    4. Support user editing and confirmation (FR-006, FR-007)
    """
    
    def __init__(self, db_session, ai_client, dictionary_reader):
        self.db_session = db_session
        self.ai_client = ai_client
        self.dictionary_reader = dictionary_reader
    
    async def translate(self, text: str, source_language: str) -> TranslationResult:
        """
        Main translation method implementing the complete workflow
        
        Args:
            text: Input text to translate (max 500 chars per FR-012)
            source_language: "chinese" or "shathyar"
            
        Returns:
            TranslationResult with all metadata
            
        Raises:
            ValueError: Invalid input parameters
            TranslationError: Translation process errors
        """
        
        # Input validation (FR-012)
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
        if len(text) > 500:
            raise ValueError("古卷无法记录如此冗长的文字...")  # Text exceeds character limit
        
        if source_language not in ["chinese", "shathyar"]:
            raise ValueError("Source language must be 'chinese' or 'shathyar'")
        
        text = text.strip()
        
        if source_language == "chinese":
            return await self._translate_chinese_to_shathyar(text)
        else:
            return await self._translate_shathyar_to_chinese(text)

    # Lookup-only path used by API to avoid consuming quota when a result
    # already exists in dictionary or cache. Never calls AI client or writes.
    def lookup_without_ai(self, text: str, source_language: str) -> Optional[TranslationResult]:
        if not text or not text.strip():
            return None
        text = text.strip()
        if source_language == 'shathyar':
            # Dictionary exact
            dictionary_entry = self._find_dictionary_match(text, 'shathyar')
            if dictionary_entry:
                return TranslationResult(
                    translated_text=dictionary_entry.origin_cn,
                    source_text=text,
                    source=TranslationSource.DICTIONARY,
                    is_cached=True,
                    is_ai_generated=False,
                    can_edit=False,
                    confidence_score=1.0,
                    translation_id=f"dict_{dictionary_entry.id}"
                )
            # Dictionary fuzzy
            fuzzy_dict_entry = self._find_dictionary_fuzzy_shathyar(text)
            if fuzzy_dict_entry:
                return TranslationResult(
                    translated_text=fuzzy_dict_entry.origin_cn,
                    source_text=text,
                    source=TranslationSource.DICTIONARY,
                    is_cached=True,
                    is_ai_generated=False,
                    can_edit=False,
                    confidence_score=0.99,
                    translation_id=f"dict_{fuzzy_dict_entry.id}"
                )
            # Cache direct exact
            cached = self._find_cached_translation(text, 'shathyar')
            if cached:
                return TranslationResult(
                    translated_text=cached.translated_text,
                    source_text=text,
                    source=TranslationSource.CACHE,
                    is_cached=True,
                    is_ai_generated=cached.is_ai_generated,
                    can_edit=False,
                    confidence_score=cached.confidence_score,
                    translation_id=cached.id
                )
            # Cache direct fuzzy
            cached_fuzzy = self._find_cached_fuzzy_shathyar(text)
            if cached_fuzzy:
                return TranslationResult(
                    translated_text=cached_fuzzy.translated_text,
                    source_text=text,
                    source=TranslationSource.CACHE,
                    is_cached=True,
                    is_ai_generated=cached_fuzzy.is_ai_generated,
                    can_edit=False,
                    confidence_score=cached_fuzzy.confidence_score,
                    translation_id=cached_fuzzy.id
                )
            # Reverse cache exact
            rev = self._find_reverse_cached_exact_shathyar(text)
            if rev:
                return TranslationResult(
                    translated_text=rev.source_text,
                    source_text=text,
                    source=TranslationSource.CACHE,
                    is_cached=True,
                    is_ai_generated=rev.is_ai_generated,
                    can_edit=False,
                    confidence_score=rev.confidence_score,
                    translation_id=rev.id
                )
            # Reverse cache fuzzy
            rev_fuzzy = self._find_reverse_cached_fuzzy_shathyar(text)
            if rev_fuzzy:
                return TranslationResult(
                    translated_text=rev_fuzzy.source_text,
                    source_text=text,
                    source=TranslationSource.CACHE,
                    is_cached=True,
                    is_ai_generated=rev_fuzzy.is_ai_generated,
                    can_edit=False,
                    confidence_score=rev_fuzzy.confidence_score,
                    translation_id=rev_fuzzy.id
                )
            return None
        elif source_language == 'chinese':
            # Cache exact
            cached = self._find_cached_translation(text, 'chinese')
            if cached:
                return TranslationResult(
                    translated_text=cached.translated_text,
                    source_text=text,
                    source=TranslationSource.CACHE,
                    is_cached=True,
                    is_ai_generated=cached.is_ai_generated,
                    can_edit=False,
                    confidence_score=cached.confidence_score,
                    translation_id=cached.id
                )
            # Cache fuzzy
            cached_fuzzy = self._find_cached_fuzzy_chinese(text)
            if cached_fuzzy:
                return TranslationResult(
                    translated_text=cached_fuzzy.translated_text,
                    source_text=text,
                    source=TranslationSource.CACHE,
                    is_cached=True,
                    is_ai_generated=cached_fuzzy.is_ai_generated,
                    can_edit=False,
                    confidence_score=cached_fuzzy.confidence_score,
                    translation_id=cached_fuzzy.id
                )
            # Dictionary exact
            dict_exact = self._find_dictionary_match(text, 'chinese')
            if dict_exact:
                return TranslationResult(
                    translated_text=dict_exact.shathyar,
                    source_text=text,
                    source=TranslationSource.DICTIONARY,
                    is_cached=True,
                    is_ai_generated=False,
                    can_edit=False,
                    confidence_score=1.0,
                    translation_id=f"dict_{dict_exact.id}"
                )
            # Dictionary fuzzy
            dict_fuzzy = self._find_dictionary_fuzzy_chinese(text)
            if dict_fuzzy:
                return TranslationResult(
                    translated_text=dict_fuzzy.shathyar,
                    source_text=text,
                    source=TranslationSource.DICTIONARY,
                    is_cached=True,
                    is_ai_generated=False,
                    can_edit=False,
                    confidence_score=0.99,
                    translation_id=f"dict_{dict_fuzzy.id}"
                )
            return None
        else:
            return None
    
    async def _translate_chinese_to_shathyar(self, chinese_text: str) -> TranslationResult:
        """Translate Chinese to Shathyar with caching and AI generation"""
        
        # Step 1: Check database cache (FR-003)
        cached_entry = self._find_cached_translation(chinese_text, "chinese")
        if cached_entry:
            cached_entry.increment_usage()
            self.db_session.commit()
            
            return TranslationResult(
                translated_text=cached_entry.translated_text,
                source_text=chinese_text,
                source=TranslationSource.CACHE,
                is_cached=True,
                is_ai_generated=cached_entry.is_ai_generated,
                can_edit=False,  # Cached entries cannot be edited
                confidence_score=cached_entry.confidence_score,
                translation_id=cached_entry.id
            )

        # Step 1.5: Fuzzy cache match (punctuation forgiveness)
        fuzzy_cached_entry = self._find_cached_fuzzy_chinese(chinese_text)
        if fuzzy_cached_entry:
            fuzzy_cached_entry.increment_usage()
            self.db_session.commit()
            return TranslationResult(
                translated_text=fuzzy_cached_entry.translated_text,
                source_text=chinese_text,
                source=TranslationSource.CACHE,
                is_cached=True,
                is_ai_generated=fuzzy_cached_entry.is_ai_generated,
                can_edit=False,
                confidence_score=fuzzy_cached_entry.confidence_score,
                translation_id=fuzzy_cached_entry.id
            )
        
        # Step 2: Check official dictionary (Chinese → Shathyar using dictionary pair)
        dict_exact = self._find_dictionary_match(chinese_text, "chinese")
        if dict_exact:
            return TranslationResult(
                translated_text=dict_exact.shathyar,
                source_text=chinese_text,
                source=TranslationSource.DICTIONARY,
                is_cached=True,
                is_ai_generated=False,
                can_edit=False,
                confidence_score=1.0,
                translation_id=f"dict_{dict_exact.id}"
            )

        # Step 2.5: Fuzzy dictionary match (punctuation forgiveness)
        dict_fuzzy = self._find_dictionary_fuzzy_chinese(chinese_text)
        if dict_fuzzy:
            return TranslationResult(
                translated_text=dict_fuzzy.shathyar,
                source_text=chinese_text,
                source=TranslationSource.DICTIONARY,
                is_cached=True,
                is_ai_generated=False,
                can_edit=False,
                confidence_score=0.99,
                translation_id=f"dict_{dict_fuzzy.id}"
            )
        
        # Step 3: Generate AI translation (FR-005)
        try:
            # Build dictionary context for AI prompt (full export per PRD, dictionary is small)
            ctx = self.dictionary_reader.get_context(include_all=True)
            try:
                relevant = self.dictionary_reader.search_chinese(chinese_text, exact_match=False, limit=100)
                ctx["relevant_entries"] = [e.to_dict() for e in relevant]
            except Exception:
                ctx["relevant_entries"] = []

            ai_result = await self.ai_client.translate_chinese_to_shathyar(
                chinese_text,
                dictionary_context=ctx
            )
            
            # Create new translation entry (not yet confirmed)
            translation_entry = TranslationEntry(
                source_text=chinese_text,
                translated_text=ai_result.translated_text,
                source_language="chinese",
                is_ai_generated=True,
                is_user_confirmed=False,
                confidence_score=ai_result.confidence_score
            )
            
            self.db_session.add(translation_entry)
            self.db_session.commit()
            
            return TranslationResult(
                translated_text=ai_result.translated_text,
                source_text=chinese_text,
                source=TranslationSource.AI_GENERATED,
                is_cached=False,
                is_ai_generated=True,
                can_edit=True,
                confidence_score=ai_result.confidence_score,
                translation_id=translation_entry.id
            )
            
        except Exception as e:
            raise TranslationError(f"翻译法阵暂时失效，请稍后重试: {str(e)}")
    
    async def _translate_shathyar_to_chinese(self, shathyar_text: str) -> TranslationResult:
        """Translate Shathyar to Chinese using dictionary lookup"""
        
        # Step 1: Check official dictionary first (FR-004)
        dictionary_entry = self._find_dictionary_match(shathyar_text, "shathyar")
        if dictionary_entry:
            return TranslationResult(
                translated_text=dictionary_entry.origin_cn,
                source_text=shathyar_text,
                source=TranslationSource.DICTIONARY,
                is_cached=True,
                is_ai_generated=False,
                can_edit=False,
                confidence_score=1.0,  # Dictionary has perfect confidence
                translation_id=f"dict_{dictionary_entry.id}"
            )
        
        # Step 1.5: Fuzzy dictionary match with punctuation forgiveness
        fuzzy_dict_entry = self._find_dictionary_fuzzy_shathyar(shathyar_text)
        if fuzzy_dict_entry:
            return TranslationResult(
                translated_text=fuzzy_dict_entry.origin_cn,
                source_text=shathyar_text,
                source=TranslationSource.DICTIONARY,
                is_cached=True,
                is_ai_generated=False,
                can_edit=False,
                confidence_score=0.99,
                translation_id=f"dict_{fuzzy_dict_entry.id}"
            )
        
        # Step 2: Check user database cache (direct shathyar-source entries)
        cached_entry = self._find_cached_translation(shathyar_text, "shathyar")
        if cached_entry:
            cached_entry.increment_usage()
            self.db_session.commit()
            
            return TranslationResult(
                translated_text=cached_entry.translated_text,
                source_text=shathyar_text,
                source=TranslationSource.CACHE,
                is_cached=True,
                is_ai_generated=cached_entry.is_ai_generated,
                can_edit=False,
                confidence_score=cached_entry.confidence_score,
                translation_id=cached_entry.id
            )
        
        # Step 2.5: Fuzzy cache match with punctuation forgiveness (direct shathyar-source entries)
        fuzzy_cached_entry = self._find_cached_fuzzy_shathyar(shathyar_text)
        if fuzzy_cached_entry:
            fuzzy_cached_entry.increment_usage()
            self.db_session.commit()
            return TranslationResult(
                translated_text=fuzzy_cached_entry.translated_text,
                source_text=shathyar_text,
                source=TranslationSource.CACHE,
                is_cached=True,
                is_ai_generated=fuzzy_cached_entry.is_ai_generated,
                can_edit=False,
                confidence_score=fuzzy_cached_entry.confidence_score,
                translation_id=fuzzy_cached_entry.id
            )

        # Step 2.6: Reverse lookup in user cache: entries where source_language='chinese'
        reverse_entry = self._find_reverse_cached_exact_shathyar(shathyar_text)
        if reverse_entry:
            reverse_entry.increment_usage()
            self.db_session.commit()
            return TranslationResult(
                translated_text=reverse_entry.source_text,
                source_text=shathyar_text,
                source=TranslationSource.CACHE,
                is_cached=True,
                is_ai_generated=reverse_entry.is_ai_generated,
                can_edit=False,
                confidence_score=reverse_entry.confidence_score,
                translation_id=reverse_entry.id
            )

        reverse_fuzzy = self._find_reverse_cached_fuzzy_shathyar(shathyar_text)
        if reverse_fuzzy:
            reverse_fuzzy.increment_usage()
            self.db_session.commit()
            return TranslationResult(
                translated_text=reverse_fuzzy.source_text,
                source_text=shathyar_text,
                source=TranslationSource.CACHE,
                is_cached=True,
                is_ai_generated=reverse_fuzzy.is_ai_generated,
                can_edit=False,
                confidence_score=reverse_fuzzy.confidence_score,
                translation_id=reverse_fuzzy.id
            )
        
        # Step 3: No match found (FR-009)
        raise TranslationNotFoundError("破译失败...")
    
    def confirm_translation(self, translation_id: str, edited_text: str) -> TranslationResult:
        """
        Confirm and save user-edited translation (FR-006, FR-007)
        
        Args:
            translation_id: ID of translation to confirm
            edited_text: User's edited version
            
        Returns:
            Updated TranslationResult
            
        Raises:
            TranslationNotFoundError: Translation ID not found
            ValueError: Invalid edited text
        """
        
        # Find the translation entry
        entry = self.db_session.query(TranslationEntry).filter_by(id=translation_id).first()
        if not entry:
            raise TranslationNotFoundError("Translation not found or already confirmed")
        
        if not entry.can_edit():
            raise ValueError("This translation cannot be edited")
        
        # Validate edited text
        if not edited_text or not edited_text.strip():
            raise ValueError("Edited text cannot be empty")
        
        if len(edited_text) > 1000:
            raise ValueError("Edited text exceeds maximum length")
        
        # Update and save
        entry.confirm_user_edit(edited_text.strip())
        self.db_session.commit()
        
        return TranslationResult(
            translated_text=entry.translated_text,
            source_text=entry.source_text,
            source=TranslationSource.CACHE,
            is_cached=True,
            is_ai_generated=True,
            can_edit=False,  # No longer editable
            confidence_score=entry.confidence_score,
            translation_id=entry.id
        )
    
    def _find_cached_translation(self, text: str, source_language: str) -> Optional[TranslationEntry]:
        """Find existing translation in database cache"""
        return self.db_session.query(TranslationEntry).filter_by(
            source_text=text,
            source_language=source_language
        ).first()
    
    def _find_dictionary_match(self, text: str, language: str) -> Optional[OfficialDictionary]:
        """Find normalized exact match in official dictionary (punctuation forgiveness only)."""
        target_norm = self._normalize_for_match(text)
        if language == "chinese":
            return self.db_session.query(OfficialDictionary).filter(
                OfficialDictionary.norm_origin_cn == target_norm
            ).first()
        else:  # shathyar
            return self.db_session.query(OfficialDictionary).filter(
                OfficialDictionary.norm_shathyar == target_norm
            ).first()

    # --- Fuzzy helpers (punctuation forgiveness) ---
    @classmethod
    def _normalize_for_match(cls, s: str) -> str:
        """Use shared normalizer so DB columns and queries stay consistent."""
        return normalize_text(s)

    def _find_dictionary_fuzzy_shathyar(self, shathyar_text: str) -> Optional[OfficialDictionary]:
        target_norm = self._normalize_for_match(shathyar_text)
        if not target_norm:
            return None
        return self.db_session.query(OfficialDictionary).filter(
            OfficialDictionary.norm_shathyar == target_norm
        ).first()

    def _find_cached_fuzzy_shathyar(self, shathyar_text: str) -> Optional[TranslationEntry]:
        target_norm = self._normalize_for_match(shathyar_text)
        if not target_norm:
            return None
        return self.db_session.query(TranslationEntry).filter(
            TranslationEntry.source_language == 'shathyar',
            TranslationEntry.norm_source_text == target_norm
        ).first()

    def _find_reverse_cached_exact_shathyar(self, shathyar_text: str) -> Optional[TranslationEntry]:
        """Find reverse user cache where CN→SH entry matches given SH text exactly (normalized)."""
        target_norm = self._normalize_for_match(shathyar_text)
        return self.db_session.query(TranslationEntry).filter(
            TranslationEntry.source_language == 'chinese',
            TranslationEntry.norm_translated_text == target_norm
        ).first()

    def _find_reverse_cached_fuzzy_shathyar(self, shathyar_text: str) -> Optional[TranslationEntry]:
        target_norm = self._normalize_for_match(shathyar_text)
        if not target_norm:
            return None
        return self.db_session.query(TranslationEntry).filter(
            TranslationEntry.source_language == 'chinese',
            TranslationEntry.norm_translated_text == target_norm
        ).first()

    def _find_dictionary_fuzzy_chinese(self, chinese_text: str) -> Optional[OfficialDictionary]:
        target_norm = self._normalize_for_match(chinese_text)
        if not target_norm:
            return None
        return self.db_session.query(OfficialDictionary).filter(
            OfficialDictionary.norm_origin_cn == target_norm
        ).first()

    def _find_cached_fuzzy_chinese(self, chinese_text: str) -> Optional[TranslationEntry]:
        target_norm = self._normalize_for_match(chinese_text)
        if not target_norm:
            return None
        return self.db_session.query(TranslationEntry).filter(
            TranslationEntry.source_language == 'chinese',
            TranslationEntry.norm_source_text == target_norm
        ).first()


# Custom exceptions
class TranslationError(Exception):
    """Base exception for translation errors"""
    pass


class TranslationNotFoundError(TranslationError):
    """Exception for translation not found scenarios"""
    pass


# CLI Interface
@click.group()
def translate_cli():
    """Shathyar Translation CLI"""
    pass


@translate_cli.command()
@click.argument('text')
@click.option('--source', type=click.Choice(['chinese', 'shathyar']), required=True)
@click.option('--format', type=click.Choice(['json', 'text']), default='text')
def translate(text: str, source: str, format: str):
    """Translate text between Chinese and Shathyar"""
    
    # This would normally initialize with real dependencies
    # For CLI usage, we'd need to set up database and AI client
    
    click.echo(f"Translating '{text}' from {source}")
    click.echo("Translation service would be called here")
    
    if format == 'json':
        result = {
            "source_text": text,
            "translated_text": "Mock translation result",
            "source_language": source,
            "is_cached": False
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Translation: Mock translation result")


@translate_cli.command()
def stats():
    """Show translation statistics"""
    click.echo("Translation statistics would be displayed here")


if __name__ == '__main__':
    translate_cli()
