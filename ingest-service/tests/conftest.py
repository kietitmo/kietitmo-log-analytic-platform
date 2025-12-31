"""
Pytest configuration and shared fixtures.
"""
import pytest
from typing import Generator
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from faker import Faker

from app.database import Base, get_db
from app.main import app
from app.config import settings
from app.models import Job, FileUpload
from app.constants import JobStatus, JobType, StorageType, LogFormat

fake = Faker()


# Override settings for testing
@pytest.fixture(scope="session", autouse=True)
def setup_test_settings():
    """Override settings for testing."""
    # Use in-memory SQLite for testing
    settings.DATABASE_URL = "sqlite:///:memory:"
    settings.DEBUG = True
    settings.ENVIRONMENT = "development"
    yield
    # Cleanup if needed


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_job(db_session) -> Job:
    """Create a sample job for testing."""
    job = Job(
        job_id="test-job-id",
        job_type=JobType.FILE_UPLOAD.value,
        source="test",
        status=JobStatus.CREATED.value,
        progress=0,
        retry_count=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_file_upload(db_session, sample_job) -> FileUpload:
    """Create a sample file upload for testing."""
    upload = FileUpload(
        job_id=sample_job.job_id,
        storage_type=StorageType.S3.value,
        bucket="test-bucket",
        object_key="test-key.log",
        file_size=1024,
        log_format=LogFormat.JSON.value,
    )
    db_session.add(upload)
    db_session.commit()
    db_session.refresh(upload)
    return upload


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("app.queue.redis_client") as mock:
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis_client.xadd.return_value = "test-message-id"
        mock.return_value = mock_redis_client
        yield mock_redis_client


@pytest.fixture
def mock_s3():
    """Mock S3 client."""
    with patch("app.storage.s3_client") as mock:
        mock_s3_client = MagicMock()
        mock_s3_client.generate_presigned_url.return_value = "https://test-presigned-url.com"
        mock_s3_client.head_object.return_value = {"ContentLength": 1024}
        mock_s3_client.list_buckets.return_value = {"Buckets": []}
        yield mock_s3_client


@pytest.fixture
def mock_enqueue_job():
    """Mock enqueue_job function."""
    with patch("app.queue.enqueue_job") as mock:
        mock.return_value = "test-message-id"
        yield mock


@pytest.fixture
def auth_token():
    """Create a test authentication token."""
    from app.auth import create_test_token
    return create_test_token(user_id="test-user-001", username="testuser")


@pytest.fixture
def auth_headers(auth_token):
    """Create authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}

