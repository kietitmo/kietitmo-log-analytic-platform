"""
Tests for queue module.
"""
import pytest
from unittest.mock import patch, MagicMock
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from app.common.infrastructure.queue import enqueue_job, check_redis_connection, get_redis_client
from app.common.exceptions.infrastucture import QueueError


class TestQueue:
    """Test cases for queue module."""
    
    @patch("app.common.infrastructure.queue.get_redis_client")
    def test_enqueue_job_success(self, mock_get_client):
        """Test successful job enqueue."""
        mock_client = MagicMock()
        mock_client.xadd.return_value = b"test-message-id"
        mock_get_client.return_value = mock_client
        
        message_id = enqueue_job({"job_id": "test-job", "type": "test"})
        
        assert message_id == b"test-message-id"
        mock_client.xadd.assert_called_once()
    
    @patch("app.common.infrastructure.queue.get_redis_client")
    def test_enqueue_job_redis_error(self, mock_get_client):
        """Test job enqueue with Redis error."""
        from redis.exceptions import RedisError
        
        mock_client = MagicMock()
        mock_client.xadd.side_effect = RedisError("Redis error")
        mock_get_client.return_value = mock_client
        
        with pytest.raises(QueueError) as exc_info:
            enqueue_job({"job_id": "test-job"})
        
        assert "enqueue" in str(exc_info.value).lower()
    
    @patch("app.common.infrastructure.queue.redis.Redis.from_url")
    def test_get_redis_client_success(self, mock_redis_from_url):
        """Test successful Redis client creation."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_from_url.return_value = mock_client
        
        # Reset global client
        import app.common.infrastructure.queue
        app.common.infrastructure.queue.redis_client = None
        
        client = get_redis_client()
        
        assert client is not None
        mock_client.ping.assert_called_once()
    
    @patch("app.common.infrastructure.queue.redis.Redis.from_url")
    def test_get_redis_client_connection_error(self, mock_redis_from_url):
        """Test Redis client creation with connection error."""
        mock_redis_from_url.side_effect = RedisConnectionError("Connection failed")
        
        # Reset global client
        import app.common.infrastructure.queue
        app.common.infrastructure.queue.redis_client = None
        
        with pytest.raises(QueueError) as exc_info:
            get_redis_client()
        
        assert "connection" in str(exc_info.value).lower()
    
    @patch("app.common.infrastructure.queue.redis.Redis.from_url")
    def test_check_redis_connection_success(self, mock_redis_from_url):
        """Test successful Redis connection check."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_from_url.return_value = mock_client
        
        # Reset global client
        import app.common.infrastructure.queue
        app.common.infrastructure.queue.redis_client = None
        
        result = check_redis_connection()
        
        assert result is True
    
    @patch("app.common.infrastructure.queue.redis.Redis.from_url")
    def test_check_redis_connection_failure(self, mock_redis_from_url):
        """Test Redis connection check failure."""
        mock_redis_from_url.side_effect = Exception("Connection error")
        
        # Reset global client
        import app.common.infrastructure.queue
        app.common.infrastructure.queue.redis_client = None
        
        result = check_redis_connection()
        
        assert result is False
    
    @patch("app.common.infrastructure.queue.redis_client")
    def test_check_redis_connection_existing_client(self, mock_redis_client):
        """Test Redis connection check with existing client."""
        mock_redis_client.ping.return_value = True
        
        result = check_redis_connection()
        
        assert result is True
        mock_redis_client.ping.assert_called_once()

