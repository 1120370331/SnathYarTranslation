"""
Integration test for Shathyar to Chinese dictionary lookup workflow

Tests the complete user workflow as described in quickstart.md Workflow 2
This test MUST FAIL initially (no implementation exists yet)
"""

import pytest
import httpx
from typing import Dict, Any


class TestShathyarLookupWorkflow:
    """Integration tests for Shathyar → Chinese dictionary lookup workflow"""
    
    BASE_URL = "http://localhost:8000"
    TRANSLATE_ENDPOINT = "/api/v1/translate"
    DICTIONARY_ENDPOINT = "/api/v1/dictionary/search"
    QUOTA_ENDPOINT = "/api/v1/session/quota"
    
    async def test_shathyar_dictionary_lookup_workflow(self):
        """Test complete Shathyar to Chinese dictionary lookup from quickstart.md"""
        async with httpx.AsyncClient() as client:
            # Step 1: Check initial magic power
            quota_response = await client.get(f"{self.BASE_URL}{self.QUOTA_ENDPOINT}")
            
            if quota_response.status_code == 200:
                initial_quota = quota_response.json()
                initial_magic_power = initial_quota["magic_power_remaining"]
            
            # Step 2: Translate known Shathyar text (should be in dictionary)
            translate_payload = {
                "text": "Mor'dun kul'thrak",
                "source_language": "shathyar"
            }
            
            translate_response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json=translate_payload
            )
            
            # Should succeed if dictionary entry exists
            if translate_response.status_code == 200:
                translate_data = translate_response.json()
                
                # Validate dictionary lookup characteristics
                assert translate_data["source_text"] == translate_payload["text"]
                assert len(translate_data["translated_text"]) > 0
                assert translate_data["is_cached"] is True  # Dictionary lookups are cached
                assert translate_data["is_ai_generated"] is False  # Not AI generated
                
                # Magic power should NOT decrease for dictionary lookups
                assert translate_data["magic_power_remaining"] == initial_magic_power
            
            # Step 3: Verify dictionary search endpoint directly
            dictionary_response = await client.get(
                f"{self.BASE_URL}{self.DICTIONARY_ENDPOINT}",
                params={"text": "Mor'dun kul'thrak", "language": "shathyar"}
            )
            
            if dictionary_response.status_code == 200:
                dict_data = dictionary_response.json()
                assert dict_data["total_count"] >= 1
                assert len(dict_data["results"]) >= 1
                
                result = dict_data["results"][0]
                assert "shathyar" in result
                assert "origin_cn" in result
    
    async def test_shathyar_translation_not_found(self):
        """Test Shathyar text not found in dictionary (Workflow 3 from quickstart.md)"""
        async with httpx.AsyncClient() as client:
            # Use text that definitely doesn't exist in dictionary
            translate_payload = {
                "text": "Zyx'qwerty unknown'phrase",
                "source_language": "shathyar"
            }
            
            translate_response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json=translate_payload
            )
            
            # Should return 404 with mystical error message
            assert translate_response.status_code == 404
            
            error_data = translate_response.json()
            assert "error" in error_data
            assert error_data["error"] == "dictionary_entry_not_found"
            assert "破译失败" in error_data["message"]
            
            # Dictionary search should also return not found
            dict_response = await client.get(
                f"{self.BASE_URL}{self.DICTIONARY_ENDPOINT}",
                params={"text": "Zyx'qwerty unknown'phrase", "language": "shathyar"}
            )
            
            assert dict_response.status_code == 404
            dict_error = dict_response.json()
            assert "破译失败" in dict_error["message"]
    
    async def test_shathyar_input_validation(self):
        """Test input validation for Shathyar translation"""
        async with httpx.AsyncClient() as client:
            # Test empty Shathyar text
            response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json={"text": "", "source_language": "shathyar"}
            )
            assert response.status_code == 400
            
            # Test Shathyar text too long
            long_shathyar = "Kul'thrak " * 100  # Very long Shathyar phrase
            response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json={"text": long_shathyar, "source_language": "shathyar"}
            )
            
            if len(long_shathyar) > 500:
                assert response.status_code == 400