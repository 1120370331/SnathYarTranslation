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
        
        # Step 2: Check official dictionary (not for Chinese→Shathyar, but for consistency)
        # Official dictionary is primarily for Shathyar→Chinese lookup
        
        # Step 3: Generate AI translation (FR-005)
        try:
            ai_result = await self.ai_client.translate_chinese_to_shathyar(
                chinese_text, 
                dictionary_context=self.dictionary_reader.get_context()
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
        
        # Step 2: Check user database cache
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
        """Find exact match in official dictionary"""
        if language == "chinese":
            return self.db_session.query(OfficialDictionary).filter(
                OfficialDictionary.origin_cn.ilike(f"%{text}%")
            ).first()
        else:  # shathyar
            return self.db_session.query(OfficialDictionary).filter(
                OfficialDictionary.shathyar.ilike(f"%{text}%")
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