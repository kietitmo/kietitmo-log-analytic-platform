"""
Tests for jobs router.
"""
import pytest

from app.models import Job
from app.constants import JobStatus, JobType


class TestJobsRouter:
    """Test cases for jobs router."""
    
    def test_get_job_success(self, client, sample_job, auth_headers):
        """Test getting a job by ID."""
        response = client.get(
            f"/jobs/{sample_job.job_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == sample_job.job_id
        assert data["status"] == sample_job.status
        assert data["progress"] == sample_job.progress
        assert "job_type" in data
        assert "source" in data
        assert "created_at" in data
    
    def test_get_job_unauthorized(self, client, sample_job):
        """Test getting a job without authentication."""
        response = client.get(f"/jobs/{sample_job.job_id}")
        
        assert response.status_code == 403
    
    def test_get_job_not_found(self, client, auth_headers):
        """Test getting a non-existent job."""
        response = client.get(
            "/jobs/non-existent-id",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_jobs_empty(self, client, auth_headers):
        """Test listing jobs when none exist."""
        response = client.get("/jobs", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_jobs_with_data(self, client, db_session, auth_headers):
        """Test listing jobs with data."""
        # Create multiple jobs
        jobs = []
        for i in range(5):
            job = Job(
                job_id=f"job-{i}",
                job_type=JobType.FILE_UPLOAD.value,
                source="test",
                status=JobStatus.CREATED.value,
                progress=0,
            )
            db_session.add(job)
            jobs.append(job)
        db_session.commit()
        
        response = client.get("/jobs", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert all("job_id" in item for item in data)
        assert all("status" in item for item in data)
        assert all("progress" in item for item in data)
    
    def test_list_jobs_with_limit(self, client, db_session, auth_headers):
        """Test listing jobs with limit."""
        # Create 10 jobs
        for i in range(10):
            job = Job(
                job_id=f"job-{i}",
                job_type=JobType.FILE_UPLOAD.value,
                source="test",
                status=JobStatus.CREATED.value,
                progress=0,
            )
            db_session.add(job)
        db_session.commit()
        
        response = client.get("/jobs?limit=5", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_list_jobs_with_offset(self, client, db_session, auth_headers):
        """Test listing jobs with offset."""
        # Create 5 jobs
        for i in range(5):
            job = Job(
                job_id=f"job-{i}",
                job_type=JobType.FILE_UPLOAD.value,
                source="test",
                status=JobStatus.CREATED.value,
                progress=0,
            )
            db_session.add(job)
        db_session.commit()
        
        response = client.get("/jobs?limit=2&offset=2", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_list_jobs_with_status_filter(self, client, db_session, auth_headers):
        """Test listing jobs with status filter."""
        # Create jobs with different statuses
        for status in [JobStatus.CREATED, JobStatus.QUEUED, JobStatus.PROCESSING]:
            job = Job(
                job_id=f"job-{status.value}",
                job_type=JobType.FILE_UPLOAD.value,
                source="test",
                status=status.value,
                progress=0,
            )
            db_session.add(job)
        db_session.commit()
        
        response = client.get("/jobs?status=CREATED", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == JobStatus.CREATED.value
    
    def test_list_jobs_with_job_type_filter(self, client, db_session, auth_headers):
        """Test listing jobs with job type filter."""
        # Create jobs with different types
        for job_type in [JobType.FILE_UPLOAD, JobType.STREAM_INGEST]:
            job = Job(
                job_id=f"job-{job_type.value}",
                job_type=job_type.value,
                source="test",
                status=JobStatus.CREATED.value,
                progress=0,
            )
            db_session.add(job)
        db_session.commit()
        
        response = client.get("/jobs?job_type=FILE_UPLOAD", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["job_id"] == "job-FILE_UPLOAD"
    
    def test_list_jobs_invalid_limit(self, client, auth_headers):
        """Test listing jobs with invalid limit."""
        response = client.get("/jobs?limit=0", headers=auth_headers)
        
        assert response.status_code == 422
    
    def test_list_jobs_invalid_offset(self, client, auth_headers):
        """Test listing jobs with invalid offset."""
        response = client.get("/jobs?offset=-1", headers=auth_headers)
        
        assert response.status_code == 422

