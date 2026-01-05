"""
Job service for managing job operations.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.jobs.models import Job, FileUpload
from app.common.constants import JobStatus, JobType, StorageType, LogFormat
from app.jobs.exceptions import JobNotFoundError, InvalidJobStateError
from app.common.logger import get_logger

logger = get_logger(__name__)


class JobService:
    """Service for job management operations."""
    
    @staticmethod
    def create_job(
        db: Session,
        job_type: JobType,
        source: str = "api",
        status: JobStatus = JobStatus.CREATED,
    ) -> Job:
        """
        Create a new job.
        
        Args:
            db: Database session
            job_type: Type of job
            source: Source of the job
            status: Initial job status
            
        Returns:
            Created job instance
        """
        job = Job(
            job_type=job_type.value,
            source=source,
            status=status.value,
        )
        db.add(job)
        db.flush()
        logger.info(f"Created job: job_id={job.job_id}, type={job_type.value}")
        return job
    
    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Job instance or None if not found
        """
        return db.query(Job).filter(Job.job_id == job_id).first()
    
    @staticmethod
    def get_job_or_raise(db: Session, job_id: str) -> Job:
        """
        Get a job by ID or raise exception if not found.
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Job instance
            
        Raises:
            JobNotFoundError: If job not found
        """
        job = JobService.get_job(db, job_id)
        if not job:
            raise JobNotFoundError(f"Job not found: {job_id}")
        return job
    
    @staticmethod
    def update_job_status(
        db: Session,
        job: Job,
        status: JobStatus,
        error_message: Optional[str] = None,
    ) -> Job:
        """
        Update job status with appropriate timestamp.
        
        Args:
            db: Database session
            job: Job instance
            status: New status
            error_message: Optional error message
            
        Returns:
            Updated job instance
        """
        job.status = status.value
        if error_message:
            job.error_message = error_message
        
        now = datetime.now(timezone.utc)
        
        if status == JobStatus.QUEUED:
            job.queued_at = now
        elif status == JobStatus.PROCESSING:
            job.started_at = now
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.finished_at = now
        
        db.flush()
        logger.info(f"Updated job status: job_id={job.job_id}, status={status.value}")
        return job
    
    @staticmethod
    def validate_job_state(job: Job, expected_status: JobStatus) -> None:
        """
        Validate that job is in expected state.
        
        Args:
            job: Job instance
            expected_status: Expected job status
            
        Raises:
            InvalidJobStateError: If job is not in expected state
        """
        current_status = JobStatus(job.status)
        if current_status != expected_status:
            raise InvalidJobStateError(
                f"Job {job.job_id} is in state {current_status.value}, "
                f"expected {expected_status.value}"
            )
    
    @staticmethod
    def create_file_upload(
        db: Session,
        job_id: str,
        bucket: str,
        object_key: str,
        file_size: int,
        log_format: LogFormat = LogFormat.JSON,
        storage_type: StorageType = StorageType.S3,
        local_path: Optional[str] = None,
    ) -> FileUpload:
        """
        Create file upload metadata.
        
        Args:
            db: Database session
            job_id: Associated job ID
            bucket: Storage bucket name
            object_key: Object key in storage
            file_size: File size in bytes
            log_format: Log format type
            storage_type: Storage type
            local_path: Optional local file path
            
        Returns:
            Created file upload instance
        """
        upload = FileUpload(
            job_id=job_id,
            storage_type=storage_type.value,
            bucket=bucket,
            object_key=object_key,
            file_size=file_size,
            log_format=log_format.value,
            local_path=local_path,
        )
        db.add(upload)
        db.flush()
        logger.info(f"Created file upload: job_id={job_id}, object_key={object_key}")
        return upload
    
    @staticmethod
    def get_file_upload(db: Session, job_id: str) -> Optional[FileUpload]:
        """
        Get file upload by job ID.
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            File upload instance or None if not found
        """
        return db.query(FileUpload).filter(FileUpload.job_id == job_id).first()

