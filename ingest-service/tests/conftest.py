"""
Pytest configuration and shared fixtures.
⚠️ IMPORTANT:
- DATABASE_URL must be set BEFORE importing app
"""

# ============================================================
# BOOTSTRAP CONFIG (RUNS BEFORE app IMPORT)
# ============================================================
import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"

# ============================================================
# STANDARD IMPORTS
# ============================================================
import pytest
from typing import Generator
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient
from faker import Faker

# ============================================================
# APP IMPORTS (SAFE NOW)
# ============================================================
from app.main import app
from app.common.database import Base, get_db
from app.jobs.models import Job, FileUpload
from app.common import database
from app.common.constants import (
    JobStatus,
    JobType,
    StorageType,
    LogFormat,
)

fake = Faker()

# ============================================================
# DATABASE FIXTURES
# ============================================================

@pytest.fixture(scope="session")
def db_engine():
    """
    Create ONE SQLite in-memory engine for the whole test session.
    StaticPool is REQUIRED so memory DB persists across connections.
    """
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    connection = db_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )

    # 🔥 OVERRIDE GLOBALS
    database.engine = db_engine
    database.SessionLocal = TestingSessionLocal

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ============================================================
# FASTAPI CLIENT (DEPENDENCY OVERRIDE)
# ============================================================

@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient with overridden get_db dependency.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================
# DOMAIN FIXTURES
# ============================================================

@pytest.fixture
def sample_job(db_session) -> Job:
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


# ============================================================
# MOCKS (INFRASTRUCTURE)
# ============================================================

@pytest.fixture
def mock_redis():
    with patch("app.common.infrastructure.queue.redis_client") as mock:
        client = MagicMock()
        client.ping.return_value = True
        client.xadd.return_value = "test-message-id"
        mock.return_value = client
        yield client


@pytest.fixture
def mock_s3():
    with patch("app.common.infrastructure.storage.s3_client") as mock:
        client = MagicMock()
        client.generate_presigned_url.return_value = "https://test-url"
        client.head_object.return_value = {"ContentLength": 1024}
        client.list_buckets.return_value = {"Buckets": []}
        yield client


@pytest.fixture
def mock_enqueue_job():
    with patch("app.common.infrastructure.queue.enqueue_job") as mock:
        mock.return_value = "test-message-id"
        yield mock


# ============================================================
# AUTH FIXTURES
# ============================================================

@pytest.fixture
def auth_token():
    from app.auth.jwt import create_access_token

    payload = {
        "sub": "test-user-001",
        "username": "testuser",
        "email": "test@test.com",
        "roles": ["user"],
        "permissions": [],
    }
    return create_access_token(payload)


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
