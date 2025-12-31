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
├── test_storage.py         # Tests cho storage module
├── test_queue.py           # Tests cho queue module
├── test_exceptions.py      # Tests cho exceptions
├── test_services/          # Tests cho services
│   ├── test_job_service.py
│   └── test_upload_service.py
└── test_routers/           # Tests cho routers
    ├── test_ingest_router.py
    ├── test_jobs_router.py
    └── test_health_router.py
```

## Test Fixtures

Các fixtures chính trong `conftest.py`:

- `db_engine`: SQLite in-memory database engine
- `db_session`: Database session cho tests
- `client`: FastAPI TestClient với database override
- `sample_job`: Sample job instance
- `sample_file_upload`: Sample file upload instance
- `mock_redis`: Mock Redis client
- `mock_s3`: Mock S3 client
- `mock_enqueue_job`: Mock enqueue_job function

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

