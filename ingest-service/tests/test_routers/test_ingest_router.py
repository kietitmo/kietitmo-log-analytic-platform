"""
Tests for ingest router.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.jobs.models import Job, FileUpload
from app.common.constants import JobStatus, JobType


class TestIngestRouter:
    """Test cases for ingest router."""
    
    @patch("app.ingest.router.UploadService.init_upload")
    def test_init_upload_success(self, mock_init, client, auth_headers):
        """Test successful upload initialization."""
        from app.jobs.models import Job, FileUpload
        from app.common.constants import JobStatus, JobType
        
        # Create mock return values
        mock_job = MagicMock(spec=Job)
        mock_job.job_id = "test-job-id"
        mock_job.job_type = JobType.FILE_UPLOAD.value
        mock_job.status = JobStatus.CREATED.value
        
        mock_upload = MagicMock(spec=FileUpload)
        mock_upload.job_id = "test-job-id"
        
        mock_init.return_value = (mock_job, mock_upload, "https://test-presigned-url.com")
        
        response = client.post(
            "/ingest/files/init",
            json={
                "filename": "test.log",
                "size": 1024,
                "log_format": "json",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert "presigned_url" in data
        assert "expires_in" in data
        assert data["presigned_url"] == "https://test-presigned-url.com"
    
    def test_init_upload_invalid_format(self, client, auth_headers):
        """Test upload initialization with invalid format."""
        response = client.post(
            "/ingest/files/init",
            json={
                "filename": "test.log",
                "size": 1024,
                "log_format": "invalid",
            },
            headers=auth_headers,
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_init_upload_unauthorized(self, client):
        """Test upload initialization without authentication."""
        response = client.post(
            "/ingest/files/init",
            json={
                "filename": "test.log",
                "size": 1024,
                "log_format": "json",
            },
        )
        
        assert response.status_code == 401
    
    def test_init_upload_missing_fields(self, client, auth_headers):
        """Test upload initialization with missing fields."""
        response = client.post(
            "/ingest/files/init",
            json={
                "filename": "test.log",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 422
    
    def test_init_upload_invalid_size(self, client, auth_headers):
        """Test upload initialization with invalid size."""
        response = client.post(
            "/ingest/files/init",
            json={
                "filename": "test.log",
                "size": -1,
                "log_format": "json",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 422
    
    @patch("app.ingest.router.UploadService.init_upload")
    def test_init_upload_storage_error(self, mock_init, client, auth_headers):
        """Test upload initialization with storage error."""
        from app.common.exceptions.infrastucture import StorageError
        
        mock_init.side_effect = StorageError("Storage unavailable")
        
        response = client.post(
            "/ingest/files/init",
            json={
                "filename": "test.log",
                "size": 1024,
                "log_format": "json",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 503
        assert "Storage" in response.json()["detail"]
    
    @patch("app.ingest.router.UploadService.complete_upload")
    def test_complete_upload_success(self, mock_complete, client, sample_job, auth_headers):
        """Test successful upload completion."""
        mock_complete.return_value = sample_job
        
        response = client.post(
            "/ingest/files/complete",
            json={
                "job_id": sample_job.job_id,
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Job queued successfully"
        assert "job_id" in data
    
    def test_complete_upload_missing_job_id(self, client, auth_headers):
        """Test completing upload with missing job_id."""
        response = client.post(
            "/ingest/files/complete",
            json={},
            headers=auth_headers,
        )
        
        assert response.status_code == 422
    
    @patch("app.ingest.router.UploadService.complete_upload")
    def test_complete_upload_job_not_found(self, mock_complete, client, auth_headers):
        """Test completing upload with non-existent job."""
        from app.jobs.exceptions import JobNotFoundError
        
        mock_complete.side_effect = JobNotFoundError("Job not found")
        
        response = client.post(
            "/ingest/files/complete",
            json={
                "job_id": "non-existent-id",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch("app.ingest.router.UploadService.complete_upload")
    def test_complete_upload_invalid_state(self, mock_complete, client, auth_headers):
        """Test completing upload with invalid job state."""
        from app.jobs.exceptions import InvalidJobStateError
        
        mock_complete.side_effect = InvalidJobStateError("Invalid state")
        
        response = client.post(
            "/ingest/files/complete",
            json={
                "job_id": "test-id",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 400
        assert "state" in response.json()["detail"].lower()
    
    @patch("app.ingest.router.UploadService.complete_upload")
    def test_complete_upload_storage_error(self, mock_complete, client, auth_headers):
        """Test completing upload with storage error."""
        from app.common.exceptions.infrastucture import StorageError
        
        mock_complete.side_effect = StorageError("File not found")
        
        response = client.post(
            "/ingest/files/complete",
            json={
                "job_id": "test-id",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 503

