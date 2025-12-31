"""
Tests for JobService.
"""
import pytest
from datetime import datetime, timezone

from app.services.job_service import JobService
from app.models import Job, FileUpload
from app.constants import JobStatus, JobType, StorageType, LogFormat
from app.exceptions import JobNotFoundError, InvalidJobStateError


class TestJobService:
    """Test cases for JobService."""
    
    def test_create_job(self, db_session):
        """Test creating a new job."""
        job = JobService.create_job(
            db=db_session,
            job_type=JobType.FILE_UPLOAD,
            source="test",
            status=JobStatus.CREATED,
        )
        
        assert job is not None
        assert job.job_id is not None
        assert job.job_type == JobType.FILE_UPLOAD.value
        assert job.source == "test"
        assert job.status == JobStatus.CREATED.value
        assert job.progress == 0
        assert job.retry_count == 0
        assert job.created_at is not None
    
    def test_get_job(self, db_session, sample_job):
        """Test getting a job by ID."""
        job = JobService.get_job(db_session, sample_job.job_id)
        
        assert job is not None
        assert job.job_id == sample_job.job_id
        assert job.status == JobStatus.CREATED.value
    
    def test_get_job_not_found(self, db_session):
        """Test getting a non-existent job."""
        job = JobService.get_job(db_session, "non-existent-id")
        
        assert job is None
    
    def test_get_job_or_raise_success(self, db_session, sample_job):
        """Test get_job_or_raise with existing job."""
        job = JobService.get_job_or_raise(db_session, sample_job.job_id)
        
        assert job is not None
        assert job.job_id == sample_job.job_id
    
    def test_get_job_or_raise_not_found(self, db_session):
        """Test get_job_or_raise with non-existent job."""
        with pytest.raises(JobNotFoundError):
            JobService.get_job_or_raise(db_session, "non-existent-id")
    
    def test_update_job_status_to_queued(self, db_session, sample_job):
        """Test updating job status to QUEUED."""
        job = JobService.update_job_status(
            db_session,
            sample_job,
            JobStatus.QUEUED,
        )
        
        assert job.status == JobStatus.QUEUED.value
        assert job.queued_at is not None
    
    def test_update_job_status_to_processing(self, db_session, sample_job):
        """Test updating job status to PROCESSING."""
        job = JobService.update_job_status(
            db_session,
            sample_job,
            JobStatus.PROCESSING,
        )
        
        assert job.status == JobStatus.PROCESSING.value
        assert job.started_at is not None
    
    def test_update_job_status_to_completed(self, db_session, sample_job):
        """Test updating job status to COMPLETED."""
        job = JobService.update_job_status(
            db_session,
            sample_job,
            JobStatus.COMPLETED,
        )
        
        assert job.status == JobStatus.COMPLETED.value
        assert job.finished_at is not None
    
    def test_update_job_status_with_error(self, db_session, sample_job):
        """Test updating job status with error message."""
        error_msg = "Test error"
        job = JobService.update_job_status(
            db_session,
            sample_job,
            JobStatus.FAILED,
            error_message=error_msg,
        )
        
        assert job.status == JobStatus.FAILED.value
        assert job.error_message == error_msg
        assert job.finished_at is not None
    
    def test_validate_job_state_success(self, sample_job):
        """Test validating job state with correct state."""
        # Should not raise exception
        JobService.validate_job_state(sample_job, JobStatus.CREATED)
    
    def test_validate_job_state_failure(self, sample_job):
        """Test validating job state with incorrect state."""
        with pytest.raises(InvalidJobStateError) as exc_info:
            JobService.validate_job_state(sample_job, JobStatus.QUEUED)
        
        assert "expected" in str(exc_info.value).lower()
    
    def test_create_file_upload(self, db_session, sample_job):
        """Test creating file upload metadata."""
        upload = JobService.create_file_upload(
            db=db_session,
            job_id=sample_job.job_id,
            bucket="test-bucket",
            object_key="test-key.log",
            file_size=2048,
            log_format=LogFormat.JSON,
            storage_type=StorageType.S3,
        )
        
        assert upload is not None
        assert upload.job_id == sample_job.job_id
        assert upload.bucket == "test-bucket"
        assert upload.object_key == "test-key.log"
        assert upload.file_size == 2048
        assert upload.log_format == LogFormat.JSON.value
        assert upload.storage_type == StorageType.S3.value
    
    def test_get_file_upload(self, db_session, sample_file_upload):
        """Test getting file upload by job ID."""
        upload = JobService.get_file_upload(
            db_session,
            sample_file_upload.job_id,
        )
        
        assert upload is not None
        assert upload.job_id == sample_file_upload.job_id
        assert upload.object_key == sample_file_upload.object_key
    
    def test_get_file_upload_not_found(self, db_session):
        """Test getting non-existent file upload."""
        upload = JobService.get_file_upload(db_session, "non-existent-id")
        
        assert upload is None

