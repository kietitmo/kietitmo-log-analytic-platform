"""
Request timeout middleware.
"""
import asyncio
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Request timeout middleware.
    Automatically cancels requests that exceed the timeout.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with timeout.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/route handler
            
        Returns:
            Response
        """
        if not settings.REQUEST_TIMEOUT_ENABLED:
            return await call_next(request)
        
        # Skip timeout for health checks (they should be fast)
        if request.url.path in ["/health", "/health/live", "/health/ready"]:
            return await call_next(request)
        
        try:
            # Create a timeout task
            timeout_seconds = settings.REQUEST_TIMEOUT_SECONDS
            
            async def process_request():
                return await call_next(request)
            
            # Run with timeout
            try:
                response = await asyncio.wait_for(
                    process_request(),
                    timeout=timeout_seconds,
                )
                return response
            except asyncio.TimeoutError:
                logger.warning(
                    f"Request timeout: {request.method} {request.url.path} "
                    f"(exceeded {timeout_seconds}s)"
                )
                return JSONResponse(
                    status_code=504,
                    content={
                        "detail": f"Request timeout: exceeded {timeout_seconds} seconds",
                        "timeout": timeout_seconds,
                    },
                )
        
        except Exception as e:
            logger.error(f"Timeout middleware error: {e}", exc_info=True)
            # If there's an error in the middleware itself, let the request proceed
            return await call_next(request)

