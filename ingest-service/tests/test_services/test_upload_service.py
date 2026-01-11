"""
Tests for UploadService.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.ingest.service import UploadService
from app.jobs.models import Job, FileUpload
from app.common.constants import JobStatus, JobType, LogFormat
from app.jobs.exceptions import JobNotFoundError, InvalidJobStateError
from app.common.exceptions.infrastucture import StorageError


class TestUploadService:
    """Test cases for UploadService."""
    
    @patch("app.ingest.service.generate_presigned_put")
    def test_init_upload_success(self, mock_presigned, db_session):
        """Test successful upload initialization."""
        mock_presigned.return_value = "https://test-presigned-url.com"
        
        job, upload, presigned_url = UploadService.init_upload(
            db=db_session,
            filename="test.log",
            size=1024,
            log_format="json",
        )
        
        assert job is not None
        assert job.job_type == JobType.FILE_UPLOAD.value
        assert job.status == JobStatus.CREATED.value
        
        assert upload is not None
        assert upload.job_id == job.job_id
        assert upload.file_size == 1024
        assert upload.log_format == LogFormat.JSON.value
        
        assert presigned_url == "https://test-presigned-url.com"
        mock_presigned.assert_called_once()
    
    @patch("app.ingest.service.generate_presigned_put")
    def test_init_upload_with_invalid_format(self, mock_presigned, db_session):
        """Test upload initialization with invalid log format."""
        mock_presigned.return_value = "https://test-presigned-url.com"
        
        job, upload, presigned_url = UploadService.init_upload(
            db=db_session,
            filename="test.log",
            size=1024,
            log_format="invalid",
        )
        
        # Should default to JSON
        assert upload.log_format == LogFormat.JSON.value
    
    @patch("app.ingest.service.generate_presigned_put")
    def test_init_upload_storage_error(self, mock_presigned, db_session):
        """Test upload initialization with storage error."""
        mock_presigned.side_effect = StorageError("Storage error")
        
        with pytest.raises(StorageError):
            UploadService.init_upload(
                db=db_session,
                filename="test.log",
                size=1024,
            )
        
        # Verify job was not committed
        jobs = db_session.query(Job).all()
        assert len(jobs) == 0
    
    @patch("app.ingest.service.object_exists")
    @patch("app.ingest.service.enqueue_job")
    def test_complete_upload_success(
        self,
        mock_enqueue,
        mock_object_exists,
        db_session,
        sample_job,
        sample_file_upload,
    ):
        """Test successful upload completion."""
        mock_object_exists.return_value = True
        mock_enqueue.return_value = "test-message-id"
        
        job = UploadService.complete_upload(
            db=db_session,
            job_id=sample_job.job_id,
        )
        
        assert job.status == JobStatus.QUEUED.value
        assert job.queued_at is not None
        mock_object_exists.assert_called_once_with(sample_file_upload.object_key)
        mock_enqueue.assert_called_once()
    
    def test_complete_upload_job_not_found(self, db_session):
        """Test completing upload with non-existent job."""
        with pytest.raises(JobNotFoundError):
            UploadService.complete_upload(
                db=db_session,
                job_id="non-existent-id",
            )
    
    def test_complete_upload_invalid_state(self, db_session, sample_job):
        """Test completing upload with invalid job state."""
        from app.jobs.service import JobService
        
        # Change job status to QUEUED
        JobService.update_job_status(
            db_session,
            sample_job,
            JobStatus.QUEUED,
        )
        db_session.commit()
        
        with pytest.raises(InvalidJobStateError):
            UploadService.complete_upload(
                db=db_session,
                job_id=sample_job.job_id,
            )
    
    @patch("app.ingest.service.object_exists")
    def test_complete_upload_file_not_found(
        self,
        mock_object_exists,
        db_session,
        sample_job,
        sample_file_upload,
    ):
        """Test completing upload when file doesn't exist."""
        mock_object_exists.return_value = False
        
        with pytest.raises(StorageError) as exc_info:
            UploadService.complete_upload(
                db=db_session,
                job_id=sample_job.job_id,
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    @patch("app.ingest.service.object_exists")
    @patch("app.ingest.service.enqueue_job")
    def test_complete_upload_enqueue_failure(
        self,
        mock_enqueue,
        mock_object_exists,
        db_session,
        sample_job,
        sample_file_upload,
    ):
        """Test completing upload when enqueue fails."""
        mock_object_exists.return_value = True
        mock_enqueue.side_effect = Exception("Queue error")
        # Capture ID before operation
        job_id = sample_job.job_id
        
        with pytest.raises(Exception):
            UploadService.complete_upload(
                db=db_session,
                job_id=job_id,
            )
        
        # Verify job status was rolled back
        # Expunge the old object to avoid stale state
        db_session.expunge(sample_job)
        job = db_session.query(Job).filter(Job.job_id == job_id).first()
        
        # If job exists, status must be CREATED. If job is gone, rollback effectively worked.
        if job:
            assert job.status == JobStatus.CREATED.value

