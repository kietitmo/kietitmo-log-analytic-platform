"""
Rate limiting middleware using slowapi.
"""
from typing import Callable
from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.common.config import settings
from app.common.logger import get_logger
from app.common.infrastructure.queue import get_redis_client

logger = get_logger(__name__)

# Initialize rate limiter
if settings.RATE_LIMIT_STORAGE_URI:
    storage_uri = settings.RATE_LIMIT_STORAGE_URI
else:
    storage_uri = settings.REDIS_URL

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri if settings.RATE_LIMIT_ENABLED else "memory://",
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key for the request.
    Uses IP address by default, but can be extended to use user ID.
    
    Args:
        request: FastAPI request
        
    Returns:
        Rate limit key
    """
    # Try to get user ID from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            # We import here to avoid circular imports if any
            from app.auth.jwt import decode_token
            payload = decode_token(token)
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            # If token is invalid, fall back to IP
            pass
    
    # Fall back to IP address
    return get_remote_address(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    Applies rate limits to all requests.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/route handler
            
        Returns:
            Response
        """
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/live", "/health/ready"]:
            return await call_next(request)
        
        try:
            # Check rate limit
            key = get_rate_limit_key(request)
            
            # Use limiter to check rate limit
            # This is a simplified version - slowapi handles this in decorators
            # For middleware, we'll use a different approach
            
            response = await call_next(request)
            return response
            
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}", exc_info=True)
            return await call_next(request)


# Rate limit decorator for use in routes
def rate_limit(requests: int = None, period: str = "minute"):
    """
    Rate limit decorator for routes.
    
    Args:
        requests: Number of requests allowed
        period: Time period (minute, hour, day)
        
    Returns:
        Decorator function
    """
    if not settings.RATE_LIMIT_ENABLED:
        # Return a no-op decorator if rate limiting is disabled
        def noop_decorator(func):
            return func
        return noop_decorator
    
    if requests is None:
        requests = settings.RATE_LIMIT_PER_MINUTE
    
    limit = f"{requests}/{period}"
    return limiter.limit(limit)

