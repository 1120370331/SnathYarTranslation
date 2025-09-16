"""
Contract test for GET /api/v1/dictionary/search endpoint

Tests the dictionary search API contract as defined in contracts/api-spec.yaml
This test MUST FAIL initially (no implementation exists yet)
"""

import pytest
import httpx
from typing import Dict, Any


class TestDictionaryGetContract:
    """Contract tests for GET /api/v1/dictionary/search"""
    
    BASE_URL = "http://localhost:8000"
    ENDPOINT = "/api/v1/dictionary/search"
    
    async def test_dictionary_search_chinese_success(self):
        """Test successful Chinese text dictionary search"""
        async with httpx.AsyncClient() as client:
            params = {
                "text": "力量",
                "language": "chinese"
            }
            
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", params=params)
            
            # Contract assertions
            assert response.status_code == 200
            
            data = response.json()
            assert "results" in data
            assert "total_count" in data
            
            # Validate response structure
            assert isinstance(data["results"], list)
            assert isinstance(data["total_count"], int)
            
            if data["results"]:
                entry = data["results"][0]
                assert "origin_cn" in entry
                assert "shathyar" in entry
                # origin_en is optional
                assert isinstance(entry["origin_cn"], str)
                assert isinstance(entry["shathyar"], str)
    
    async def test_dictionary_search_shathyar_success(self):
        """Test successful Shathyar text dictionary search"""
        async with httpx.AsyncClient() as client:
            params = {
                "text": "Keth",
                "language": "shathyar"
            }
            
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", params=params)
            
            # Contract assertions
            assert response.status_code == 200
            
            data = response.json()
            assert "results" in data
            assert "total_count" in data
            
            # Validate response structure
            assert isinstance(data["results"], list)
            assert isinstance(data["total_count"], int)
    
    async def test_dictionary_search_not_found(self):
        """Test dictionary search with no results"""
        async with httpx.AsyncClient() as client:
            params = {
                "text": "不存在的词汇",
                "language": "chinese"
            }
            
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", params=params)
            
            # Contract assertions for not found case
            assert response.status_code == 404
            
            error = response.json()
            assert "error" in error
            assert "message" in error
            assert error["error"] == "dictionary_entry_not_found"
            assert "破译失败" in error["message"]
    
    async def test_dictionary_search_missing_parameters(self):
        """Test validation errors for missing parameters"""
        async with httpx.AsyncClient() as client:
            # Test missing text parameter
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", params={
                "language": "chinese"
            })
            assert response.status_code == 400
            
            # Test missing language parameter  
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", params={
                "text": "测试"
            })
            assert response.status_code == 400
            
            # Test both missing
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}")
            assert response.status_code == 400
    
    async def test_dictionary_search_invalid_language(self):
        """Test validation error for invalid language parameter"""
        async with httpx.AsyncClient() as client:
            params = {
                "text": "测试",
                "language": "invalid_language"
            }
            
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", params=params)
            
            assert response.status_code == 400
            
            error = response.json()
            assert "error" in error
            assert "message" in error
    
    async def test_dictionary_search_text_too_long(self):
        """Test validation error for text exceeding 500 characters"""
        async with httpx.AsyncClient() as client:
            long_text = "测试" * 251  # 502 characters
            
            params = {
                "text": long_text,
                "language": "chinese"
            }
            
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", params=params)
            
            assert response.status_code == 400
            
            error = response.json()
            assert "error" in error
            assert "message" in error
    
    async def test_dictionary_search_response_headers(self):
        """Test response headers"""
        async with httpx.AsyncClient() as client:
            params = {
                "text": "测试",
                "language": "chinese"
            }
            
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", params=params)
            
            # Test content type (regardless of status code)
            assert response.headers.get("content-type") == "application/json"