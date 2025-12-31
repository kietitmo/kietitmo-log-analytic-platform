"""
Jobs router for job status and management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Job
from app.schemas import JobResponse, JobDetailResponse
from app.services.job_service import JobService
from app.exceptions import JobNotFoundError, handle_service_exception
from app.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    responses={
        404: {"description": "Job not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job by ID",
    description="Retrieve detailed information about a specific job",
)
@rate_limit(requests=30, period="minute")
def get_job(
    request: Request,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> JobDetailResponse:
    """
    Get a job by ID.
    
    Args:
        job_id: Job ID
        db: Database session
        
    Returns:
        JobDetailResponse with job information
        
    Raises:
        HTTPException: If job not found
    """
    try:
        job = JobService.get_job_or_raise(db, job_id)
        
        return JobDetailResponse(
            job_id=job.job_id,
            job_type=job.job_type,
            source=job.source,
            status=job.status,
            progress=job.progress,
            retry_count=job.retry_count,
            created_at=job.created_at,
            queued_at=job.queued_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_message=job.error_message,
        )
    except JobNotFoundError as e:
        logger.warning(f"Job not found: {job_id}")
        raise handle_service_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error getting job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job",
        )


@router.get(
    "",
    response_model=List[JobResponse],
    summary="List jobs",
    description="Retrieve a list of jobs with optional filtering",
)
@rate_limit(requests=30, period="minute")
def list_jobs(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> List[JobResponse]:
    """
    List jobs with optional filtering.
    
    Args:
        status_filter: Optional status filter
        job_type: Optional job type filter
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        
    Returns:
        List of job responses
    """
    try:
        query = db.query(Job)
        
        if status_filter:
            query = query.filter(Job.status == status_filter)
        
        if job_type:
            query = query.filter(Job.job_type == job_type)
        
        jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            JobResponse(
                job_id=job.job_id,
                status=job.status,
                progress=job.progress,
            )
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Unexpected error listing jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs",
        )
