"""
Ingest router for file upload operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    InitUploadRequest,
    InitUploadResponse,
    CompleteUploadRequest,
)
from app.services.upload_service import UploadService
from app.services.job_service import JobService
from app.exceptions import (
    JobNotFoundError,
    InvalidJobStateError,
    StorageError,
    handle_service_exception,
)
from app.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/files/init",
    response_model=InitUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize file upload",
    description="Create a new upload job and generate a presigned URL for file upload",
)
@rate_limit(requests=10, period="minute")
def init_upload(
    request: Request,
    req: InitUploadRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> InitUploadResponse:
    """
    Initialize a file upload.
    
    Creates a new job and generates a presigned URL for uploading the file to S3.
    
    Args:
        req: Upload initialization request with filename, size, and log format
        db: Database session
        
    Returns:
        InitUploadResponse with job_id, presigned_url, and expiration time
        
    Raises:
        HTTPException: If upload initialization fails
    """
    try:
        job, upload, presigned_url = UploadService.init_upload(
            db=db,
            filename=req.filename,
            size=req.size,
            log_format=req.log_format,
        )
        
        logger.info(
            f"Upload initialized: job_id={job.job_id}, "
            f"filename={req.filename}, size={req.size}, user={current_user.get('username')}"
        )
        
        return InitUploadResponse(
            job_id=job.job_id,
            presigned_url=presigned_url,
            expires_in=settings.S3_PRESIGNED_URL_EXPIRES,
        )
    except StorageError as e:
        logger.error(f"Storage error initializing upload: {e}")
        raise handle_service_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error initializing upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize upload",
        )


@router.post(
    "/files/complete",
    status_code=status.HTTP_200_OK,
    summary="Complete file upload",
    description="Mark upload as complete and queue job for processing",
)
@rate_limit(requests=20, period="minute")
def complete_upload(
    request: Request,
    req: CompleteUploadRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Complete a file upload.
    
    Verifies the file exists in storage and queues the job for processing.
    
    Args:
        req: Complete upload request with job_id
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If job not found, invalid state, or file not found
    """
    try:
        job = UploadService.complete_upload(db=db, job_id=req.job_id)
        
        logger.info(f"Upload completed and queued: job_id={req.job_id}")
        
        return {
            "message": "Job queued successfully",
            "job_id": job.job_id,
            "status": job.status,
        }
    except JobNotFoundError as e:
        logger.warning(f"Job not found: {req.job_id}")
        raise handle_service_exception(e)
    except InvalidJobStateError as e:
        logger.warning(f"Invalid job state: {req.job_id} - {e}")
        raise handle_service_exception(e)
    except StorageError as e:
        logger.error(f"Storage error completing upload: {e}")
        raise handle_service_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error completing upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete upload",
        )
