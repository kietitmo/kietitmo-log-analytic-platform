"""
Health check router for monitoring and diagnostics.
"""
from fastapi import APIRouter, status
from typing import Dict, Any

from app.common.database import check_db_connection
from app.common.infrastructure.queue import check_redis_connection
from app.common.infrastructure.storage import check_storage_connection
from app.common.config import settings
from app.common.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Basic health check endpoint",
)
def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if service is ready to accept traffic",
)
def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    
    Verifies that all required services (database, Redis, storage) are available.
    
    Returns:
        Readiness status with component health
    """
    db_healthy = check_db_connection()
    redis_healthy = check_redis_connection()
    storage_healthy = check_storage_connection()
    
    all_healthy = db_healthy and redis_healthy and storage_healthy
    
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "components": {
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "storage": "healthy" if storage_healthy else "unhealthy",
        },
    }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Check if service is alive",
)
def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    
    Returns:
        Liveness status
    """
    return {
        "status": "alive",
    }

