# Testing Guide

Hướng dẫn chạy tests cho ingest-service.

## Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

## Chạy Tests

### Chạy tất cả tests

```bash
pytest
```

### Chạy với coverage report

```bash
pytest --cov=app --cov-report=html
```

Coverage report sẽ được tạo trong thư mục `htmlcov/`.

### Chạy tests cụ thể

```bash
# Chạy tests cho một module
pytest tests/test_services/

# Chạy tests cho một file
pytest tests/test_services/test_job_service.py

# Chạy một test cụ thể
pytest tests/test_services/test_job_service.py::TestJobService::test_create_job
```

### Chạy với verbose output

```bash
pytest -v
```

### Chạy với markers

```bash
# Chạy chỉ unit tests
pytest -m unit

# Chạy chỉ integration tests
pytest -m integration

# Bỏ qua slow tests
pytest -m "not slow"
```

## Cấu trúc Tests

```
tests/
├── conftest.py              # Pytest fixtures và configuration
├── test_main.py            # Tests cho main application
├── test_database.py        # Tests cho database module
├── test_storage.py         # Tests cho storage infrastructure
├── test_queue.py           # Tests cho queue infrastructure
├── test_exceptions.py      # Tests cho exceptions
├── test_auth.py            # Tests cho auth module
├── test_services/          # Tests cho domain services
│   ├── test_job_service.py      # jobs domain
│   └── test_upload_service.py  # ingest domain
└── test_routers/           # Tests cho domain routers
    ├── test_ingest_router.py   # ingest domain
    ├── test_jobs_router.py     # jobs domain
    ├── test_auth_router.py     # auth domain
    └── test_health_router.py   # common routers
```

**Lưu ý**: Tests được tổ chức theo domain structure để dễ quản lý và maintain.

## Test Fixtures

Các fixtures chính trong `conftest.py`:

- `db_engine`: SQLite in-memory database engine
- `db_session`: Database session cho tests
- `client`: FastAPI TestClient với database override
- `sample_job`: Sample job instance (jobs domain)
- `sample_file_upload`: Sample file upload instance (jobs domain)
- `mock_redis`: Mock Redis client (common/infrastructure/queue)
- `mock_s3`: Mock S3 client (common/infrastructure/storage)
- `mock_enqueue_job`: Mock enqueue_job function
- `auth_token`: Test JWT token (auth domain)
- `auth_headers`: Authentication headers cho requests

## Coverage Requirements

Project yêu cầu tối thiểu 80% code coverage. Coverage report được tạo tự động khi chạy tests với `--cov` flag.

## Best Practices

1. **Isolation**: Mỗi test nên độc lập và không phụ thuộc vào tests khác
2. **Fixtures**: Sử dụng fixtures để setup/teardown test data
3. **Mocking**: Mock external dependencies (Redis, S3, etc.)
4. **Assertions**: Sử dụng assertions rõ ràng và descriptive
5. **Naming**: Test names nên mô tả rõ ràng test case

## Continuous Integration

Tests sẽ được chạy tự động trong CI/CD pipeline. Đảm bảo tất cả tests pass trước khi merge code.

