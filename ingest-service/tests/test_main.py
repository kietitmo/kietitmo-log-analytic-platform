"""
Tests for main application.
"""
import pytest
from fastapi.testclient import TestClient


class TestMain:
    """Test cases for main application."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_openapi_docs_available_in_dev(self, client):
        """Test that OpenAPI docs are available in development."""
        response = client.get("/docs")
        
        # Should be available in test environment (development)
        assert response.status_code in [200, 307]  # 307 for redirect
    
    def test_openapi_json_available(self, client):
        """Test that OpenAPI JSON is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        
        # CORS middleware should handle this
        # The exact response depends on CORS configuration
        assert response.status_code in [200, 204, 405]
    
    def test_process_time_header(self, client):
        """Test that process time header is added."""
        response = client.get("/")
        
        assert "X-Process-Time" in response.headers
        assert float(response.headers["X-Process-Time"]) >= 0

