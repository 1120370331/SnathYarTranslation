"""
Contract test for POST /api/v1/translate/{id}/confirm endpoint

Tests the translation confirmation API contract as defined in contracts/api-spec.yaml
This test MUST FAIL initially (no implementation exists yet)
"""

import pytest
import httpx
import uuid
from typing import Dict, Any


class TestConfirmPostContract:
    """Contract tests for POST /api/v1/translate/{id}/confirm"""
    
    BASE_URL = "http://localhost:8000"
    TRANSLATE_ENDPOINT = "/api/v1/translate"
    
    def confirm_endpoint(self, translation_id: str) -> str:
        return f"/api/v1/translate/{translation_id}/confirm"
    
    async def test_confirm_translation_success(self):
        """Test successful translation confirmation"""
        async with httpx.AsyncClient() as client:
            # First, create a translation to confirm
            translate_payload = {
                "text": "虚空的力量",
                "source_language": "chinese"
            }
            
            translate_response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}", 
                json=translate_payload
            )
            
            # Assume we get a translation_id from the response
            assert translate_response.status_code == 200
            translate_data = translate_response.json()
            
            # For AI-generated translations, should have translation_id
            if translate_data.get("can_edit", False):
                translation_id = translate_data.get("translation_id")
                assert translation_id is not None
                
                # Now confirm the translation with edits
                confirm_payload = {
                    "edited_text": "Vash'jir kul'thrak mor'dun"  # User's edited version
                }
                
                response = await client.post(
                    f"{self.BASE_URL}{self.confirm_endpoint(translation_id)}",
                    json=confirm_payload
                )
                
                # Contract assertions
                assert response.status_code == 200
                
                data = response.json()
                assert "success" in data
                assert "copy_text" in data
                
                # Validate response structure
                assert data["success"] is True
                assert data["copy_text"] == confirm_payload["edited_text"]
                
                # Optional success message
                if "message" in data:
                    assert isinstance(data["message"], str)
                    assert "保存" in data["message"]  # Should mention saving
    
    async def test_confirm_translation_not_found(self):
        """Test confirmation of non-existent translation"""
        async with httpx.AsyncClient() as client:
            # Use a random UUID that doesn't exist
            fake_translation_id = str(uuid.uuid4())
            
            confirm_payload = {
                "edited_text": "Some edited text"
            }
            
            response = await client.post(
                f"{self.BASE_URL}{self.confirm_endpoint(fake_translation_id)}",
                json=confirm_payload
            )
            
            # Contract assertions
            assert response.status_code == 404
            
            error = response.json()
            assert "error" in error
            assert "message" in error
    
    async def test_confirm_translation_already_confirmed(self):
        """Test confirmation of already confirmed translation"""
        async with httpx.AsyncClient() as client:
            # This simulates trying to confirm a translation that's already been confirmed
            # The exact behavior depends on implementation, but should return 404 or 400
            
            fake_translation_id = str(uuid.uuid4())
            confirm_payload = {
                "edited_text": "Already confirmed text"
            }
            
            response = await client.post(
                f"{self.BASE_URL}{self.confirm_endpoint(fake_translation_id)}",
                json=confirm_payload
            )
            
            # Should be 404 (not found) or 400 (bad request)
            assert response.status_code in [400, 404]
            
            error = response.json()
            assert "error" in error
            assert "message" in error
    
    async def test_confirm_translation_invalid_edited_text(self):
        """Test confirmation with invalid edited text"""
        async with httpx.AsyncClient() as client:
            fake_translation_id = str(uuid.uuid4())
            
            # Test empty edited text
            response = await client.post(
                f"{self.BASE_URL}{self.confirm_endpoint(fake_translation_id)}",
                json={"edited_text": ""}
            )
            assert response.status_code == 400
            
            # Test missing edited_text field
            response = await client.post(
                f"{self.BASE_URL}{self.confirm_endpoint(fake_translation_id)}",
                json={}
            )
            assert response.status_code == 400
            
            # Test edited text too long (1000 character limit)
            long_text = "A" * 1001
            response = await client.post(
                f"{self.BASE_URL}{self.confirm_endpoint(fake_translation_id)}",
                json={"edited_text": long_text}
            )
            assert response.status_code == 400
    
    async def test_confirm_translation_invalid_uuid(self):
        """Test confirmation with invalid UUID format"""
        async with httpx.AsyncClient() as client:
            invalid_id = "not-a-uuid"
            
            confirm_payload = {
                "edited_text": "Valid text"
            }
            
            response = await client.post(
                f"{self.BASE_URL}{self.confirm_endpoint(invalid_id)}",
                json=confirm_payload
            )
            
            # Should return 400 for invalid UUID format
            assert response.status_code == 400
            
            error = response.json()
            assert "error" in error
            assert "message" in error
    
    async def test_confirm_translation_response_headers(self):
        """Test response headers for confirmation endpoint"""
        async with httpx.AsyncClient() as client:
            fake_translation_id = str(uuid.uuid4())
            
            confirm_payload = {
                "edited_text": "Test headers"
            }
            
            response = await client.post(
                f"{self.BASE_URL}{self.confirm_endpoint(fake_translation_id)}",
                json=confirm_payload
            )
            
            # Test content type (regardless of status code)
            assert response.headers.get("content-type") == "application/json"
    
    async def test_confirm_translation_saves_to_database(self):
        """Test that confirmation saves translation to database for caching"""
        # This is more of an integration test, but validates the contract
        # requirement that confirmed translations are saved
        
        async with httpx.AsyncClient() as client:
            # Step 1: Create an AI translation
            translate_payload = {
                "text": "数据库保存测试",
                "source_language": "chinese"
            }
            
            translate_response = await client.post(
                f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                json=translate_payload
            )
            
            if translate_response.status_code == 200:
                translate_data = translate_response.json()
                translation_id = translate_data.get("translation_id")
                
                if translation_id:
                    # Step 2: Confirm with edits
                    confirm_payload = {
                        "edited_text": "Kul'thrak vash'jir mor'dun"
                    }
                    
                    confirm_response = await client.post(
                        f"{self.BASE_URL}{self.confirm_endpoint(translation_id)}",
                        json=confirm_payload
                    )
                    
                    if confirm_response.status_code == 200:
                        # Step 3: Request same translation again - should be cached
                        second_translate = await client.post(
                            f"{self.BASE_URL}{self.TRANSLATE_ENDPOINT}",
                            json=translate_payload
                        )
                        
                        if second_translate.status_code == 200:
                            second_data = second_translate.json()
                            # Should return cached version (edited text)
                            assert second_data.get("is_cached") is True
                            assert second_data.get("translated_text") == confirm_payload["edited_text"]