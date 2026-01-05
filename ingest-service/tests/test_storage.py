"""
Tests for storage module.
"""
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError

from app.common.infrastructure.storage import (
    generate_presigned_put,
    object_exists,
    get_object_size,
    check_storage_connection,
)
from app.common.exceptions.infrastucture import StorageError


class TestStorage:
    """Test cases for storage module."""
    
    @patch("app.storage.s3_client")
    def test_generate_presigned_put_success(self, mock_s3_client):
        """Test successful presigned URL generation."""
        mock_s3_client.generate_presigned_url.return_value = "https://test-url.com"
        
        url = generate_presigned_put("test-key", expires=3600)
        
        assert url == "https://test-url.com"
        mock_s3_client.generate_presigned_url.assert_called_once()
    
    @patch("app.storage.s3_client")
    def test_generate_presigned_put_client_error(self, mock_s3_client):
        """Test presigned URL generation with client error."""
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_s3_client.generate_presigned_url.side_effect = ClientError(
            error_response,
            "GeneratePresignedUrl",
        )
        
        with pytest.raises(StorageError) as exc_info:
            generate_presigned_put("test-key")
        
        assert "AccessDenied" in str(exc_info.value)
    
    @patch("app.storage.s3_client")
    def test_generate_presigned_put_boto_error(self, mock_s3_client):
        """Test presigned URL generation with boto error."""
        mock_s3_client.generate_presigned_url.side_effect = BotoCoreError()
        
        with pytest.raises(StorageError):
            generate_presigned_put("test-key")
    
    @patch("app.storage.s3_client")
    def test_object_exists_true(self, mock_s3_client):
        """Test object exists check when object exists."""
        mock_s3_client.head_object.return_value = {}
        
        result = object_exists("test-key")
        
        assert result is True
        mock_s3_client.head_object.assert_called_once()
    
    @patch("app.storage.s3_client")
    def test_object_exists_false(self, mock_s3_client):
        """Test object exists check when object doesn't exist."""
        error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
        mock_s3_client.head_object.side_effect = ClientError(
            error_response,
            "HeadObject",
        )
        
        result = object_exists("test-key")
        
        assert result is False
    
    @patch("app.storage.s3_client")
    def test_object_exists_error(self, mock_s3_client):
        """Test object exists check with error."""
        error_response = {"Error": {"Code": "500", "Message": "Internal Error"}}
        mock_s3_client.head_object.side_effect = ClientError(
            error_response,
            "HeadObject",
        )
        
        with pytest.raises(StorageError):
            object_exists("test-key")
    
    @patch("app.storage.s3_client")
    def test_get_object_size_success(self, mock_s3_client):
        """Test getting object size successfully."""
        mock_s3_client.head_object.return_value = {"ContentLength": 1024}
        
        size = get_object_size("test-key")
        
        assert size == 1024
    
    @patch("app.storage.s3_client")
    def test_get_object_size_not_found(self, mock_s3_client):
        """Test getting object size when object doesn't exist."""
        error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
        mock_s3_client.head_object.side_effect = ClientError(
            error_response,
            "HeadObject",
        )
        
        size = get_object_size("test-key")
        
        assert size is None
    
    @patch("app.storage.s3_client")
    def test_check_storage_connection_success(self, mock_s3_client):
        """Test successful storage connection check."""
        mock_s3_client.list_buckets.return_value = {"Buckets": []}
        
        result = check_storage_connection()
        
        assert result is True
        mock_s3_client.list_buckets.assert_called_once()
    
    @patch("app.storage.s3_client")
    def test_check_storage_connection_failure(self, mock_s3_client):
        """Test storage connection check failure."""
        mock_s3_client.list_buckets.side_effect = Exception("Connection error")
        
        result = check_storage_connection()
        
        assert result is False

