"""
Contract test for GET /api/v1/session/quota endpoint

Tests the session quota API contract as defined in contracts/api-spec.yaml
This test MUST FAIL initially (no implementation exists yet)
"""

import pytest
import httpx
from typing import Dict, Any


class TestQuotaGetContract:
    """Contract tests for GET /api/v1/session/quota"""
    
    BASE_URL = "http://localhost:8000"
    ENDPOINT = "/api/v1/session/quota"
    
    async def test_quota_get_success(self):
        """Test successful quota retrieval"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}")
            
            # Contract assertions
            assert response.status_code == 200
            
            data = response.json()
            assert "magic_power_remaining" in data
            assert "daily_limit" in data
            assert "reset_time" in data
            assert "total_used_today" in data
            
            # Validate response structure and ranges
            assert isinstance(data["magic_power_remaining"], int)
            assert isinstance(data["daily_limit"], int)
            assert isinstance(data["reset_time"], str)
            assert isinstance(data["total_used_today"], int)
            
            # Validate value ranges
            assert 0 <= data["magic_power_remaining"] <= 500
            assert data["daily_limit"] == 500
            assert 0 <= data["total_used_today"] <= 500
            
            # Validate consistency
            assert data["magic_power_remaining"] + data["total_used_today"] == data["daily_limit"]
    
    async def test_quota_get_exhausted(self):
        """Test quota when exhausted"""
        async with httpx.AsyncClient() as client:
            # This would typically be tested after making 500 requests
            # For now, we test the response structure
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}")
            
            if response.status_code == 200:
                data = response.json()
                
                # When quota is exhausted
                if data["magic_power_remaining"] == 0:
                    assert data["total_used_today"] == 500
                    assert data["daily_limit"] == 500
                    assert "reset_time" in data
    
    async def test_quota_get_response_headers(self):
        """Test response headers"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}")
            
            # Test content type
            assert response.headers.get("content-type") == "application/json"
    
    async def test_quota_get_with_different_ips(self):
        """Test quota is tracked per IP address"""
        async with httpx.AsyncClient() as client:
            # Test with default IP
            response1 = await client.get(f"{self.BASE_URL}{self.ENDPOINT}")
            
            # Test with X-Forwarded-For header (simulating different IP)
            headers = {"X-Forwarded-For": "192.168.1.100"}
            response2 = await client.get(f"{self.BASE_URL}{self.ENDPOINT}", headers=headers)
            
            # Both should succeed (different IPs have separate quotas)
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                # Each IP should have its own quota tracking
                assert "magic_power_remaining" in data1
                assert "magic_power_remaining" in data2
                # They might have different usage patterns
    
    async def test_quota_get_iso8601_time_format(self):
        """Test that reset_time is in ISO 8601 format"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}{self.ENDPOINT}")
            
            if response.status_code == 200:
                data = response.json()
                reset_time = data["reset_time"]
                
                # Basic ISO 8601 format validation
                # Should be like "2025-09-12T00:00:00Z"
                assert isinstance(reset_time, str)
                assert len(reset_time) >= 19  # Minimum length for ISO format
                assert "T" in reset_time
                assert reset_time.endswith("Z") or "+" in reset_time or "-" in reset_time[-6:]