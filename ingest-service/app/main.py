"""
Main FastAPI application for the ingest service.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time

from app.common.config import settings
from app.common.database import init_db, engine
from app.common.logger import setup_logging, get_logger
from app.ingest.router import router as ingest_router
from app.jobs.router import router as jobs_router
from app.common.routers.health import router as health_router
from app.users.router import router as users_router
from app.auth.router import router as auth_router
from app.common.middleware.timeout import TimeoutMiddleware
from app.common.middleware.rate_limit import limiter
from slowapi.errors import RateLimitExceeded as SlowAPIRateLimitExceeded
from app.common.exceptions.domain import DomainException
from app.common.exceptions.infrastucture import InfrastructureException
from app.common.middleware.request_id import RequestIDMiddleware
from fastapi.encoders import jsonable_encoder


from prometheus_fastapi_instrumentator import Instrumentator


# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    try:
        # Validate production configuration
        if settings.is_production:
            settings.validate_production()
            logger.info("Production configuration validated")
        
        # Initialize database
        init_db()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    # Close database connections
    engine.dispose()
    logger.info("Application shutdown completed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Log ingestion service for uploading and processing log files",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Timeout middleware
if settings.REQUEST_TIMEOUT_ENABLED:
    app.add_middleware(TimeoutMiddleware)

# Request ID middleware
app.add_middleware(RequestIDMiddleware)

# Prometheus Metrics
Instrumentator().instrument(app).expose(app)


# Rate limiting - handled via decorators, but add exception handler
app.state.limiter = limiter


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"{response.status_code} ({process_time:.3f}s)",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
            }
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - {e} ({process_time:.3f}s)",
            exc_info=True,
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time": process_time,
            }
        )
        raise


@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(
        "Domain exception",
        extra={
            "path": request.url.path,
            "error_code": exc.error_code,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc),
            "error_code": exc.error_code,
        },
    )


@app.exception_handler(InfrastructureException)
async def infrastructure_exception_handler(request: Request, exc: InfrastructureException):
    """Handle infrastructure exceptions."""
    logger.error(f"Infrastructure exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc) or "Service unavailable"},
    )




@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors())},
    )



@app.exception_handler(SlowAPIRateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: SlowAPIRateLimitExceeded):
    """Handle rate limit exceptions."""
    logger.warning(f"Rate limit exceeded: {request.client.host if request.client else 'unknown'}")
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "retry_after": exc.retry_after,
        },
        headers={
            "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
            "X-RateLimit-Remaining": "0",
            "Retry-After": str(exc.retry_after) if exc.retry_after else "60",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error" if settings.is_production else str(exc)
        },
    )


# Include routers
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(jobs_router)
app.include_router(users_router)

@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }
