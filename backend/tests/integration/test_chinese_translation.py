"""
Integration test for Chinese to Shathyar translation workflow

Tests the complete user workflow as described in quickstart.md Workflow 1
This test MUST FAIL initially (no implementation exists yet)
"""

import pytest
import httpx
from typing import Dict, Any


class TestChineseTranslationWorkflow:
    """Integration tests for Chinese → Shathyar translation workflow"""
    
    BASE_URL = "http://localhost:8000"
    TRANSLATE_ENDPOINT = "/api/v1/translate"
    QUOTA_ENDPOINT = "/api/v1/session/quota"
    
    async def test_complete_chinese_to_shathyar_workflow(self):
        """Test complete Chinese to Shathyar translation workflow from quickstart.md"""
        async with httpx.AsyncClient() as client:
            # Step 1: Check initial quota (should be 500/500)
            quota_response = await client.get(f"{self.BASE_URL}{self.QUOTA_ENDPOINT}")
            
            if quota_response.status_code == 200:
                quota_data = quota_response.json()
                initial_magic_power = quota_data["magic_power_remaining"]
                assert initial_magic_power <= 500  # May have been used in other tests
            
            # Step 2: Translate Chinese text to Shathyar
            translate_payload = {
                "text": "虚空的力量召唤着我们",
                "source_language": "chinese"
            }
            
            translate_response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json=translate_payload
            )
            
            # Validate translation response
            assert translate_response.status_code == 200
            
            translate_data = translate_response.json()
            assert translate_data["source_text"] == translate_payload["text"]
            assert len(translate_data["translated_text"]) > 0
            
            # Check if AI generated (should be true for new Chinese text)
            if translate_data.get("is_ai_generated", False):
                assert translate_data["can_edit"] is True
                assert "translation_id" in translate_data
                assert "confidence_score" in translate_data
            
            # Step 3: Verify magic power decreased by 1
            final_magic_power = translate_data["magic_power_remaining"]
            if quota_response.status_code == 200:
                expected_magic_power = initial_magic_power - 1
                assert final_magic_power == expected_magic_power
            
            # Step 4: Verify quota endpoint reflects the change
            quota_response2 = await client.get(f"{self.BASE_URL}{self.QUOTA_ENDPOINT}")
            if quota_response2.status_code == 200:
                quota_data2 = quota_response2.json()
                assert quota_data2["magic_power_remaining"] == final_magic_power
    
    async def test_chinese_translation_caching(self):
        """Test that repeated Chinese translations are cached"""
        async with httpx.AsyncClient() as client:
            translate_payload = {
                "text": "测试缓存功能",
                "source_language": "chinese"
            }
            
            # First translation request
            response1 = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json=translate_payload
            )
            
            if response1.status_code == 200:
                data1 = response1.json()
                first_magic_power = data1["magic_power_remaining"]
                
                # Second identical translation request
                response2 = await client.post(
                    f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                    json=translate_payload
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    
                    # Should return same translation
                    assert data2["translated_text"] == data1["translated_text"]
                    
                    # Magic power should be the same (cached, doesn't consume quota)
                    assert data2["magic_power_remaining"] == first_magic_power
                    assert data2["is_cached"] is True
    
    async def test_chinese_translation_input_validation(self):
        """Test input validation for Chinese translation"""
        async with httpx.AsyncClient() as client:
            # Test empty text
            response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json={"text": "", "source_language": "chinese"}
            )
            assert response.status_code == 400
            
            # Test text too long (>500 characters)
            long_text = "测试" * 251  # 502 characters
            response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json={"text": long_text, "source_language": "chinese"}
            )
            assert response.status_code == 400
            
            error_data = response.json()
            assert "古卷无法记录如此冗长的文字" in error_data["message"]
    
    async def test_chinese_translation_ai_service_integration(self):
        """Test AI service integration for Chinese translation"""
        async with httpx.AsyncClient() as client:
            translate_payload = {
                "text": "古老的魔法咒语",
                "source_language": "chinese"
            }
            
            response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json=translate_payload
            )
            
            # If AI service is available
            if response.status_code == 200:
                data = response.json()
                
                # AI-generated translation should have these properties
                if data.get("is_ai_generated", False):
                    assert "confidence_score" in data
                    assert 0 <= data["confidence_score"] <= 1
                    assert data["can_edit"] is True
                    assert "translation_id" in data
            
            # If AI service is unavailable
            elif response.status_code == 500:
                error_data = response.json()
                assert "翻译法阵暂时失效" in error_data["message"]
            elif response.status_code == 503:
                error_data = response.json()
                assert "古神的低语暂时无法解读" in error_data["message"]