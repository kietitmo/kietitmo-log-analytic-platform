# Ingest Service

Log ingestion service for uploading and processing log files. This service provides a RESTful API for file uploads, job management, and authentication with JWT tokens.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Features](#features)
- [System Flow](#system-flow)
- [Class Diagrams](#class-diagrams)
- [Sequence Diagrams](#sequence-diagrams)
- [API Documentation](#api-documentation)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Deployment](#deployment)

## Overview

The Ingest Service is a FastAPI-based microservice that handles:
- **File Upload**: Initialize and complete file uploads to S3/MinIO
- **Job Management**: Track and monitor ingestion jobs
- **Authentication**: JWT-based authentication and authorization
- **User Management**: User CRUD operations with role-based access control
- **Rate Limiting**: Protect APIs from abuse
- **Request Timeout**: Prevent long-running requests

## Architecture

### Domain-Driven Structure

The service follows a **domain-driven design** pattern where each domain is self-contained and separated:

```
app/
├── common/              # Shared infrastructure
│   ├── config.py        # Application settings
│   ├── database.py      # Database configuration
│   ├── logger.py        # Logging setup
│   ├── constants.py     # Application constants
│   ├── exceptions/      # Domain & infrastructure exceptions
│   ├── infrastructure/  # External services
│   │   ├── storage.py   # S3/MinIO operations
│   │   └── queue.py     # Redis queue operations
│   ├── middleware/      # Request middleware
│   │   ├── rate_limit.py
│   │   └── timeout.py
│   └── routers/         # Common routers
│       └── health.py
├── auth/                # Authentication & Authorization domain
│   ├── models.py        # Roles, permissions, context
│   ├── authorization.py # Permission resolution & policies
│   ├── service.py       # Authentication service
│   ├── jwt.py          # JWT token operations
│   ├── utils.py        # Password hashing
│   ├── dependencies.py # FastAPI dependencies
│   ├── schemas.py      # Request/response schemas
│   ├── exceptions.py   # Auth exceptions
│   └── router.py       # Auth API routes
├── users/               # User management domain
│   ├── models.py       # User model
│   ├── service.py      # User service
│   ├── router.py       # User API routes
│   ├── schemas/        # User schemas
│   └── exceptions.py   # User exceptions
├── jobs/                # Job management domain
│   ├── models.py       # Job, FileUpload models
│   ├── service.py      # Job service
│   ├── router.py       # Jobs API routes
│   ├── schemas.py      # Job schemas
│   └── exceptions.py   # Job exceptions
├── ingest/              # File ingestion domain
│   ├── service.py      # Upload service
│   ├── router.py       # Ingest API routes
│   ├── schemas.py      # Upload schemas
│   └── exceptions.py   # Ingest exceptions
└── main.py             # FastAPI application entry point
```

### Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Client[Client Application]
    end
    
    subgraph "API Gateway"
        API[FastAPI Application]
        Auth[Authentication Middleware]
        RateLimit[Rate Limiting]
        Timeout[Timeout Middleware]
    end
    
    subgraph "Domain Layer"
        IngestDomain[Ingest Domain<br/>router, service, schemas]
        JobsDomain[Jobs Domain<br/>router, service, models, schemas]
        AuthDomain[Auth Domain<br/>router, service, jwt, authorization]
        UsersDomain[Users Domain<br/>router, service, models, schemas]
    end
    
    subgraph "Common Infrastructure"
        Common[Common<br/>database, config, logger, middleware]
        Storage[Storage Infrastructure<br/>S3/MinIO]
        Queue[Queue Infrastructure<br/>Redis]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL)]
        Redis[(Redis Queue)]
        S3[(S3/MinIO Storage)]
    end
    
    Client --> API
    API --> Auth
    API --> RateLimit
    API --> Timeout
    API --> IngestDomain
    API --> JobsDomain
    API --> AuthDomain
    API --> UsersDomain
    
    IngestDomain --> JobsDomain
    IngestDomain --> Storage
    IngestDomain --> Queue
    JobsDomain --> DB
    AuthDomain --> UsersDomain
    
    Storage --> S3
    Queue --> Redis
    Common --> DB
    
    style API fill:#4A90E2
    style IngestDomain fill:#50C878
    style JobsDomain fill:#50C878
    style AuthDomain fill:#50C878
    style UsersDomain fill:#50C878
    style DB fill:#336791
    style Redis fill:#DC382D
    style S3 fill:#FF9900
```

## Project Structure

The service follows a **Domain-Driven Design (DDD)** pattern where each domain is self-contained:

```
app/
├── common/                    # Shared infrastructure
│   ├── config.py             # Application settings with validation
│   ├── database.py            # Database configuration & session management
│   ├── logger.py             # Structured logging setup
│   ├── constants.py           # Application constants (JobStatus, JobType, etc.)
│   ├── exceptions/            # Base exception classes
│   │   ├── domain.py         # Domain exceptions
│   │   └── infrastucture.py  # Infrastructure exceptions
│   ├── infrastructure/        # External service integrations
│   │   ├── storage.py        # S3/MinIO operations
│   │   └── queue.py          # Redis queue operations
│   ├── middleware/            # Request middleware
│   │   ├── rate_limit.py     # Rate limiting
│   │   └── timeout.py        # Request timeout
│   └── routers/              # Common routers
│       └── health.py         # Health check endpoints
│
├── auth/                      # Authentication & Authorization Domain
│   ├── models.py             # Roles, Permissions, AuthContext
│   ├── authorization.py      # Permission resolution & policies
│   ├── service.py            # Authentication service (login)
│   ├── jwt.py                # JWT token operations
│   ├── utils.py              # Password hashing utilities
│   ├── dependencies.py       # FastAPI dependencies (get_current_user, etc.)
│   ├── schemas.py            # Request/response schemas
│   ├── exceptions.py         # Auth domain exceptions
│   └── router.py             # Auth API routes
│
├── users/                     # User Management Domain
│   ├── models.py             # User database model
│   ├── service.py            # User service (CRUD operations)
│   ├── router.py             # User API routes
│   ├── schemas/              # User schemas
│   │   ├── commands.py      # Command schemas
│   │   ├── requests.py       # Request schemas
│   │   └── responses.py      # Response schemas
│   └── exceptions.py         # User domain exceptions
│
├── jobs/                      # Job Management Domain
│   ├── models.py             # Job, FileUpload database models
│   ├── service.py            # Job service (create, update, query)
│   ├── router.py             # Jobs API routes
│   ├── schemas.py            # Job request/response schemas
│   └── exceptions.py         # Job domain exceptions
│
├── ingest/                    # File Ingestion Domain
│   ├── service.py            # Upload service (init, complete)
│   ├── router.py             # Ingest API routes
│   ├── schemas.py            # Upload request/response schemas
│   └── exceptions.py         # Ingest domain exceptions
│
├── scripts/                   # Utility scripts
│   └── init_users.py         # Initialize default users
│
└── main.py                    # FastAPI application entry point
```

### Domain Organization Principles

1. **Self-contained**: Each domain has its own models, services, routers, schemas, and exceptions
2. **Isolated**: Domains don't directly import from each other (except through common)
3. **Extensible**: Easy to add new features within a domain
4. **Testable**: Each domain can be tested independently

### Import Guidelines

- ✅ Domains can import from `common/`
- ✅ Domains can import from other domains' public interfaces (schemas, exceptions)
- ❌ Domains should NOT import internal implementation details from other domains
- ✅ Use dependency injection for cross-domain dependencies

## Features

### Core Features
- ✅ File upload with presigned URLs
- ✅ Job tracking and monitoring
- ✅ JWT authentication
- ✅ Rate limiting
- ✅ Request timeout protection
- ✅ Health checks
- ✅ Structured logging
- ✅ Error handling
- ✅ Database connection pooling
- ✅ Redis queue integration

### Security Features
- JWT token-based authentication
- Password hashing with bcrypt
- Rate limiting per IP/user
- CORS support
- Request validation
- Error message sanitization

## System Flow

### File Upload Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant UploadService
    participant JobService
    participant DB
    participant S3
    participant Redis
    
    Client->>API: POST /ingest/files/init
    API->>Auth: Verify JWT token
    Auth-->>API: User authenticated
    API->>UploadService: init_upload()
    UploadService->>JobService: create_job()
    JobService->>DB: Create job record
    DB-->>JobService: Job created
    UploadService->>S3: Generate presigned URL
    S3-->>UploadService: Presigned URL
    UploadService->>DB: Create file_upload record
    UploadService-->>API: Return job_id + presigned_url
    API-->>Client: 201 Created
    
    Client->>S3: PUT file using presigned URL
    S3-->>Client: File uploaded
    
    Client->>API: POST /ingest/files/complete
    API->>Auth: Verify JWT token
    Auth-->>API: User authenticated
    API->>UploadService: complete_upload()
    UploadService->>S3: Verify file exists
    S3-->>UploadService: File verified
    UploadService->>JobService: update_job_status(QUEUED)
    UploadService->>Redis: Enqueue job
    Redis-->>UploadService: Job enqueued
    UploadService-->>API: Success
    API-->>Client: 200 OK
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AuthRouter
    participant AuthModule
    participant DB
    
    Client->>API: POST /auth/login
    API->>AuthRouter: login()
    AuthRouter->>AuthModule: verify_password()
    AuthModule-->>AuthRouter: Password verified
    AuthRouter->>AuthModule: create_access_token()
    AuthRouter->>AuthModule: create_refresh_token()
    AuthModule-->>AuthRouter: Tokens created
    AuthRouter-->>API: TokenResponse
    API-->>Client: 200 OK + tokens
    
    Note over Client: Store tokens
    
    Client->>API: GET /ingest/files/init
    Note over Client: Include: Authorization: Bearer <token>
    API->>AuthModule: get_current_user()
    AuthModule->>AuthModule: decode_token()
    AuthModule-->>API: User data
    API->>API: Process request
    API-->>Client: Response
```

### Job Processing Flow

```mermaid
flowchart TD
    Start([Job Created]) --> Created[Status: CREATED]
    Created --> InitUpload[Initialize Upload]
    InitUpload --> WaitUpload[Wait for File Upload]
    WaitUpload --> CompleteUpload[Complete Upload]
    CompleteUpload --> VerifyFile{File Exists?}
    VerifyFile -->|No| Error1[Error: File not found]
    VerifyFile -->|Yes| QueueJob[Queue Job to Redis]
    QueueJob --> Queued[Status: QUEUED]
    Queued --> WorkerPickup[Worker Picks Up Job]
    WorkerPickup --> Processing[Status: PROCESSING]
    Processing --> Process{Process Success?}
    Process -->|Yes| Completed[Status: COMPLETED]
    Process -->|No| CheckRetry{Retry Count < Max?}
    CheckRetry -->|Yes| Retry[Increment Retry Count]
    Retry --> Queued
    CheckRetry -->|No| Failed[Status: FAILED]
    Error1 --> Failed
    Completed --> End([Job Finished])
    Failed --> End
    
    style Created fill:#E3F2FD
    style Queued fill:#FFF3E0
    style Processing fill:#F3E5F5
    style Completed fill:#E8F5E9
    style Failed fill:#FFEBEE
```

## Class Diagrams

### Service Layer

```mermaid
classDiagram
    class UploadService {
        +init_upload(db, filename, size, log_format) Job, FileUpload, str
        +complete_upload(db, job_id) Job
    }
    
    class JobService {
        +create_job(db, job_type, source, status) Job
        +get_job(db, job_id) Job
        +get_job_or_raise(db, job_id) Job
        +update_job_status(db, job, status, error_message) Job
        +validate_job_state(job, expected_status) void
        +create_file_upload(db, job_id, bucket, object_key, ...) FileUpload
        +get_file_upload(db, job_id) FileUpload
    }
    
    UploadService --> JobService : uses
```

### Data Models

```mermaid
classDiagram
    class Job {
        +String job_id PK
        +String job_type
        +String source
        +String status
        +Integer progress
        +Integer retry_count
        +DateTime created_at
        +DateTime queued_at
        +DateTime started_at
        +DateTime finished_at
        +DateTime updated_at
        +Text error_message
        +FileUpload file_upload
    }
    
    class FileUpload {
        +String job_id PK, FK
        +String storage_type
        +String bucket
        +Text object_key
        +Text local_path
        +Integer file_size
        +String log_format
        +DateTime created_at
        +Job job
    }
    
    Job "1" --> "0..1" FileUpload : has
```

### Authentication Module

```mermaid
classDiagram
    class AuthModule {
        +verify_password(plain, hashed) bool
        +get_password_hash(password) str
        +create_access_token(data, expires_delta) str
        +create_refresh_token(data) str
        +decode_token(token) dict
        +get_current_user(credentials) dict
        +get_optional_user(credentials) dict
    }
    
    class CryptContext {
        +verify(plain, hashed) bool
        +hash(password) str
    }
    
    class JWT {
        +encode(payload, key, algorithm) str
        +decode(token, key, algorithms) dict
    }
    
    AuthModule --> CryptContext : uses
    AuthModule --> JWT : uses
```

### Router Layer

```mermaid
classDiagram
    class IngestRouter {
        +init_upload(request, req, db, current_user) InitUploadResponse
        +complete_upload(request, req, db, current_user) dict
    }
    
    class JobsRouter {
        +get_job(request, job_id, db, current_user) JobDetailResponse
        +list_jobs(request, status_filter, job_type, limit, offset, db, current_user) List[JobResponse]
    }
    
    class AuthRouter {
        +login(request, credentials) TokenResponse
        +refresh_token(http_request, request) TokenResponse
        +get_me(current_user) dict
        +verify_token(token) dict
    }
    
    class HealthRouter {
        +health_check() dict
        +readiness_check() dict
        +liveness_check() dict
    }
    
    IngestRouter --> UploadService : uses
    JobsRouter --> JobService : uses
    AuthRouter --> AuthModule : uses
```

## Sequence Diagrams

### Complete Upload Sequence

```mermaid
sequenceDiagram
    participant Client
    participant IngestRouter
    participant UploadService
    participant JobService
    participant StorageService
    participant QueueService
    participant DB
    participant Redis
    
    Client->>IngestRouter: POST /ingest/files/complete
    IngestRouter->>UploadService: complete_upload(job_id)
    UploadService->>JobService: get_job_or_raise(job_id)
    JobService->>DB: Query job
    DB-->>JobService: Job data
    JobService-->>UploadService: Job object
    
    UploadService->>JobService: validate_job_state(CREATED)
    JobService-->>UploadService: Validated
    
    UploadService->>JobService: get_file_upload(job_id)
    JobService->>DB: Query file_upload
    DB-->>JobService: FileUpload data
    JobService-->>UploadService: FileUpload object
    
    UploadService->>StorageService: object_exists(object_key)
    StorageService->>S3: head_object()
    S3-->>StorageService: Object exists
    StorageService-->>UploadService: True
    
    UploadService->>JobService: update_job_status(QUEUED)
    JobService->>DB: Update job
    DB-->>JobService: Updated
    JobService-->>UploadService: Updated job
    
    UploadService->>QueueService: enqueue_job(message)
    QueueService->>Redis: xadd(stream_key, message)
    Redis-->>QueueService: Message ID
    QueueService-->>UploadService: Success
    
    UploadService-->>IngestRouter: Job object
    IngestRouter-->>Client: 200 OK
```

### Authentication Sequence

```mermaid
sequenceDiagram
    participant Client
    participant AuthRouter
    participant AuthModule
    participant DemoUsers
    
    Client->>AuthRouter: POST /auth/login
    Note over Client,AuthRouter: {username, password}
    
    AuthRouter->>DemoUsers: get(username)
    DemoUsers->>DemoUsers: _get_demo_user(username)
    DemoUsers->>DemoUsers: _hash_password_bcrypt(password)
    DemoUsers-->>AuthRouter: User data with hashed_password
    
    AuthRouter->>AuthModule: verify_password_bcrypt(plain, hashed)
    AuthModule->>bcrypt: checkpw(plain, hashed)
    bcrypt-->>AuthModule: True/False
    AuthModule-->>AuthRouter: Verified
    
    alt Password Valid
        AuthRouter->>AuthModule: create_access_token(user_data)
        AuthModule->>jwt: encode(payload, secret, algorithm)
        jwt-->>AuthModule: Access token
        
        AuthRouter->>AuthModule: create_refresh_token(user_data)
        AuthModule->>jwt: encode(payload, secret, algorithm)
        jwt-->>AuthModule: Refresh token
        
        AuthModule-->>AuthRouter: Tokens
        AuthRouter-->>Client: 200 OK + tokens
    else Password Invalid
        AuthRouter-->>Client: 401 Unauthorized
    end
```

### Rate Limiting Sequence

```mermaid
sequenceDiagram
    participant Client
    participant RateLimitMiddleware
    participant SlowAPI
    participant Redis
    participant Router
    
    Client->>RateLimitMiddleware: HTTP Request
    RateLimitMiddleware->>SlowAPI: Check rate limit
    SlowAPI->>Redis: GET rate_limit_key
    Redis-->>SlowAPI: Current count
    
    alt Under Limit
        SlowAPI->>Redis: INCR rate_limit_key
        Redis-->>SlowAPI: New count
        SlowAPI-->>RateLimitMiddleware: Allowed
        RateLimitMiddleware->>Router: Forward request
        Router-->>RateLimitMiddleware: Response
        RateLimitMiddleware-->>Client: 200 OK
    else Over Limit
        SlowAPI-->>RateLimitMiddleware: Rate limit exceeded
        RateLimitMiddleware-->>Client: 429 Too Many Requests
    end
```

## API Documentation

### Authentication Endpoints

#### POST /auth/login
Login and get access/refresh tokens.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### GET /auth/me
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

### Ingest Endpoints

#### POST /ingest/files/init
Initialize a file upload and get presigned URL.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "filename": "logs.json",
  "size": 1024000,
  "log_format": "json"
}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "presigned_url": "https://s3.example.com/presigned-url",
  "expires_in": 1800
}
```

#### POST /ingest/files/complete
Complete file upload and queue job for processing.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response:**
```json
{
  "message": "Job queued successfully",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "QUEUED"
}
```

### Jobs Endpoints

#### GET /jobs/{job_id}
Get job details by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "job_type": "FILE_UPLOAD",
  "source": "api",
  "status": "QUEUED",
  "progress": 0,
  "retry_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "queued_at": "2024-01-01T00:00:05Z",
  "started_at": null,
  "finished_at": null,
  "error_message": null
}
```

#### GET /jobs
List jobs with optional filtering.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `status` (optional): Filter by job status
- `job_type` (optional): Filter by job type
- `limit` (optional, default: 100): Maximum results
- `offset` (optional, default: 0): Skip results

**Response:**
```json
[
  {
    "job_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "QUEUED",
    "progress": 0
  }
]
```

### Health Endpoints

#### GET /health
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "Log Ingest Service",
  "version": "1.0.0"
}
```

#### GET /health/ready
Readiness check (checks all dependencies).

**Response:**
```json
{
  "status": "ready",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  }
}
```

#### GET /health/live
Liveness check.

**Response:**
```json
{
  "status": "alive"
}
```

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- S3-compatible storage (MinIO or AWS S3)
- Docker and Docker Compose (optional)

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd ingest-service
```

2. **Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run database migrations**
```bash
# Database tables are created automatically on startup
```

6. **Start the service**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

1. **Build the image**
```bash
docker build -t ingest-service .
```

2. **Run with Docker Compose**
```bash
docker-compose up -d ingest-service
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/logs` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `S3_ENDPOINT` | S3 endpoint URL | `http://localhost:9000` |
| `S3_ACCESS_KEY` | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | S3 secret key | `minioadmin` |
| `S3_BUCKET` | S3 bucket name | `log-bucket` |
| `JWT_SECRET_KEY` | JWT secret key | `your-secret-key-change-in-production` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | `30` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `RATE_LIMIT_PER_MINUTE` | Requests per minute | `60` |
| `REQUEST_TIMEOUT_SECONDS` | Request timeout | `30` |
| `ENVIRONMENT` | Environment (development/staging/production) | `development` |
| `DEBUG` | Debug mode | `false` |

### Configuration File

See `app/common/config.py` for all configuration options with validation.

**Note**: The application automatically validates production configuration on startup. See [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) for details.

### Production Configuration Validation

The application automatically validates production configuration on startup. Ensure:
- `JWT_SECRET_KEY` is set to a secure value (not default)
- `CORS_ORIGINS` does not contain `["*"]` in production
- `S3_ACCESS_KEY` and `S3_SECRET_KEY` are not default values
- `DEBUG=False` in production
- `ENVIRONMENT=production`

## Usage

### 1. Login and Get Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 2. Initialize File Upload

```bash
curl -X POST "http://localhost:8000/ingest/files/init" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "logs.json",
    "size": 1024000,
    "log_format": "json"
  }'
```

### 3. Upload File to S3

```bash
curl -X PUT "<presigned_url>" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @logs.json
```

### 4. Complete Upload

```bash
curl -X POST "http://localhost:8000/ingest/files/complete" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "<job_id>"
  }'
```

### 5. Check Job Status

```bash
curl -X GET "http://localhost:8000/jobs/<job_id>" \
  -H "Authorization: Bearer <access_token>"
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services/test_job_service.py

# Run with verbose output
pytest -v
```

### Test Coverage

Target: 80% code coverage

```bash
pytest --cov=app --cov-report=term-missing
```

## Deployment

### Production Checklist

See [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) for detailed checklist.

**Critical Requirements:**
- [x] ✅ Production configuration validation (auto-validates on startup)
- [x] ✅ JWT secret key validation
- [x] ✅ CORS configuration validation
- [x] ✅ S3 credentials validation
- [x] ✅ Filename sanitization
- [x] ✅ File size limits (100MB max)
- [x] ✅ Refresh token validation
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Change `JWT_SECRET_KEY` to a strong random value
- [ ] Configure proper `DATABASE_URL`
- [ ] Configure proper `REDIS_URL`
- [ ] Configure S3 credentials (not defaults)
- [ ] Set up proper CORS origins (not `["*"]`)
- [ ] Configure rate limits appropriately
- [ ] Set up monitoring and alerting
- [ ] Configure logging aggregation
- [ ] Set up health check monitoring

### Docker Production

```bash
docker build -t ingest-service:latest .
docker run -d \
  --name ingest-service \
  -p 8000:8000 \
  --env-file .env.production \
  ingest-service:latest
```

### Health Monitoring

The service provides health check endpoints for monitoring:
- `/health` - Basic health check
- `/health/ready` - Readiness probe (checks dependencies)
- `/health/live` - Liveness probe

Configure your orchestration platform (Kubernetes, Docker Swarm, etc.) to use these endpoints.

## Component Diagram

```mermaid
graph TB
    subgraph "API Layer"
        Main[main.py<br/>FastAPI App]
        Middleware[Middleware<br/>CORS, Timeout, Rate Limit]
    end
    
    subgraph "Domain Layer - Ingest"
        IngestR[ingest/router.py<br/>File Upload API]
        UploadS[ingest/service.py<br/>Upload Logic]
        IngestSchemas[ingest/schemas.py]
    end
    
    subgraph "Domain Layer - Jobs"
        JobsR[jobs/router.py<br/>Job Management API]
        JobS[jobs/service.py<br/>Job Logic]
        JobModels[jobs/models.py<br/>Job, FileUpload]
        JobSchemas[jobs/schemas.py]
    end
    
    subgraph "Domain Layer - Auth"
        AuthR[auth/router.py<br/>Authentication API]
        AuthS[auth/service.py<br/>Auth Logic]
        AuthJWT[auth/jwt.py<br/>JWT Operations]
        AuthAuthz[auth/authorization.py<br/>Permissions & Policies]
        AuthModels[auth/models.py<br/>Roles, Permissions]
    end
    
    subgraph "Domain Layer - Users"
        UsersR[users/router.py<br/>User Management API]
        UsersS[users/service.py<br/>User Logic]
        UserModels[users/models.py<br/>User Model]
    end
    
    subgraph "Common Infrastructure"
        CommonDB[common/database.py<br/>PostgreSQL]
        CommonConfig[common/config.py<br/>Settings]
        CommonLogger[common/logger.py<br/>Logging]
        Storage[common/infrastructure/storage.py<br/>S3/MinIO]
        Queue[common/infrastructure/queue.py<br/>Redis Streams]
        HealthR[common/routers/health.py<br/>Health Checks]
    end
    
    Main --> Middleware
    Main --> IngestR
    Main --> JobsR
    Main --> AuthR
    Main --> UsersR
    Main --> HealthR
    
    IngestR --> UploadS
    JobsR --> JobS
    AuthR --> AuthS
    UsersR --> UsersS
    
    UploadS --> JobS
    UploadS --> Storage
    UploadS --> Queue
    JobS --> CommonDB
    AuthS --> AuthJWT
    AuthS --> UsersS
    
    style Main fill:#4A90E2
    style IngestR fill:#50C878
    style JobsR fill:#50C878
    style AuthR fill:#50C878
    style UsersR fill:#50C878
    style CommonDB fill:#336791
    style Queue fill:#DC382D
    style Storage fill:#FF9900
```

## Data Flow Diagram

```mermaid
flowchart LR
    Start([Client Request]) --> Auth{Authenticated?}
    Auth -->|No| Reject[401 Unauthorized]
    Auth -->|Yes| RateLimit{Rate Limit OK?}
    RateLimit -->|No| RateLimitError[429 Too Many Requests]
    RateLimit -->|Yes| Timeout{Within Timeout?}
    Timeout -->|No| TimeoutError[504 Gateway Timeout]
    Timeout -->|Yes| Router[Router Handler]
    Router --> Service[Service Layer]
    Service --> DB[(Database)]
    Service --> Storage[(S3/MinIO)]
    Service --> Queue[(Redis)]
    Service --> Response[Response]
    Response --> End([Client])
    
    style Auth fill:#FFE5B4
    style RateLimit fill:#FFE5B4
    style Timeout fill:#FFE5B4
    style Service fill:#E8F5E9
```

## State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> CREATED: Initialize Upload
    CREATED --> QUEUED: Complete Upload
    CREATED --> FAILED: Validation Error
    QUEUED --> PROCESSING: Worker Picks Up
    PROCESSING --> COMPLETED: Success
    PROCESSING --> FAILED: Error (Max Retries)
    PROCESSING --> QUEUED: Retry (Retry Count < Max)
    COMPLETED --> [*]
    FAILED --> [*]
    
    note right of CREATED
        Job created, waiting
        for file upload
    end note
    
    note right of QUEUED
        File uploaded,
        job queued for processing
    end note
    
    note right of PROCESSING
        Worker processing
        the job
    end note
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[NGINX/HAProxy]
    end
    
    subgraph "Application Tier"
        App1[Ingest Service<br/>Instance 1]
        App2[Ingest Service<br/>Instance 2]
        App3[Ingest Service<br/>Instance N]
    end
    
    subgraph "Data Tier"
        PG[(PostgreSQL<br/>Primary)]
        PGReplica[(PostgreSQL<br/>Replica)]
        Redis[(Redis<br/>Cluster)]
    end
    
    subgraph "Storage Tier"
        S3[(S3/MinIO<br/>Object Storage)]
    end
    
    subgraph "Worker Tier"
        Worker1[Worker<br/>Instance 1]
        Worker2[Worker<br/>Instance 2]
        WorkerN[Worker<br/>Instance N]
    end
    
    LB --> App1
    LB --> App2
    LB --> App3
    
    App1 --> PG
    App2 --> PG
    App3 --> PG
    
    App1 --> Redis
    App2 --> Redis
    App3 --> Redis
    
    App1 --> S3
    App2 --> S3
    App3 --> S3
    
    PG --> PGReplica
    
    Redis --> Worker1
    Redis --> Worker2
    Redis --> WorkerN
    
    Worker1 --> S3
    Worker2 --> S3
    WorkerN --> S3
    
    style LB fill:#4A90E2
    style App1 fill:#50C878
    style App2 fill:#50C878
    style App3 fill:#50C878
    style PG fill:#336791
    style Redis fill:#DC382D
    style S3 fill:#FF9900
```

## Architecture Decisions

### Why FastAPI?
- High performance (async support)
- Automatic API documentation
- Type hints and validation
- Modern Python features

### Why SQLAlchemy 2.0?
- Modern async support
- Better type safety
- Improved performance
- Active development

### Why Redis Streams?
- Reliable message delivery
- Consumer groups support
- Persistence
- High performance

### Why JWT?
- Stateless authentication
- Scalable
- Standard protocol
- Refresh token support

### Why Domain-Driven Design?
- **Separation of concerns**: Each domain is self-contained
- **Scalability**: Easy to add new domains without affecting others
- **Maintainability**: Clear boundaries and responsibilities
- **Testability**: Each domain can be tested independently
- **Team collaboration**: Different teams can work on different domains

## Troubleshooting

### Common Issues

**Database connection errors**
- Check `DATABASE_URL` is correct
- Verify PostgreSQL is running
- Check network connectivity

**Redis connection errors**
- Check `REDIS_URL` is correct
- Verify Redis is running
- Check network connectivity

**S3 errors**
- Verify S3 credentials
- Check bucket exists
- Verify network connectivity to S3 endpoint

**Authentication errors**
- Verify JWT_SECRET_KEY is set
- Check token expiration
- Verify token format

## License

[Your License Here]

## Contributing

[Contributing Guidelines]

## Support

[Support Information]

