"""
Tests for health router.
"""
import pytest
from unittest.mock import patch


class TestHealthRouter:
    """Test cases for health router."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    @patch("app.common.routers.health.check_db_connection")
    @patch("app.common.routers.health.check_redis_connection")
    @patch("app.common.routers.health.check_storage_connection")
    def test_readiness_check_all_healthy(
        self,
        mock_storage,
        mock_redis,
        mock_db,
        client,
    ):
        """Test readiness check when all services are healthy."""
        mock_db.return_value = True
        mock_redis.return_value = True
        mock_storage.return_value = True
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["components"]["database"] == "healthy"
        assert data["components"]["redis"] == "healthy"
        assert data["components"]["storage"] == "healthy"

    @patch("app.common.routers.health.check_db_connection")
    @patch("app.common.routers.health.check_redis_connection")
    @patch("app.common.routers.health.check_storage_connection")
    def test_readiness_check_db_unhealthy(
        self,
        mock_storage,
        mock_redis,
        mock_db,
        client,
    ):
        """Test readiness check when database is unhealthy."""
        mock_db.return_value = False
        mock_redis.return_value = True
        mock_storage.return_value = True
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["components"]["database"] == "unhealthy"
        assert data["components"]["redis"] == "healthy"
        assert data["components"]["storage"] == "healthy"

    @patch("app.common.routers.health.check_db_connection")
    @patch("app.common.routers.health.check_redis_connection")
    @patch("app.common.routers.health.check_storage_connection")
    def test_readiness_check_redis_unhealthy(
        self,
        mock_storage,
        mock_redis,
        mock_db,
        client,
    ):
        """Test readiness check when Redis is unhealthy."""
        mock_db.return_value = True
        mock_redis.return_value = False
        mock_storage.return_value = True
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["components"]["database"] == "healthy"
        assert data["components"]["redis"] == "unhealthy"
        assert data["components"]["storage"] == "healthy"

    @patch("app.common.routers.health.check_db_connection")
    @patch("app.common.routers.health.check_redis_connection")
    @patch("app.common.routers.health.check_storage_connection")
    def test_readiness_check_storage_unhealthy(
        self,
        mock_storage,
        mock_redis,
        mock_db,
        client,
    ):
        """Test readiness check when storage is unhealthy."""
        mock_db.return_value = True
        mock_redis.return_value = True
        mock_storage.return_value = False
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["components"]["database"] == "healthy"
        assert data["components"]["redis"] == "healthy"
        assert data["components"]["storage"] == "unhealthy"
    
    def test_liveness_check(self, client):
        """Test liveness check."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

