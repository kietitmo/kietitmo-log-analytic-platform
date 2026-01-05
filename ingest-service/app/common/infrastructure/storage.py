"""
S3/MinIO storage operations.
"""
from typing import Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

from app.common.config import settings
from app.common.logger import get_logger
from app.common.exceptions.infrastucture import StorageError

logger = get_logger(__name__)

# S3 client configuration
s3_config = Config(
    retries={
        "max_attempts": 3,
        "mode": "standard",
    },
    connect_timeout=10,
    read_timeout=10,
)

# Create S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name=settings.S3_REGION,
    config=s3_config,
)


def generate_presigned_put(key: str, expires: Optional[int] = None) -> str:
    """
    Generate a presigned URL for PUT operation.
    
    Args:
        key: Object key in S3
        expires: Expiration time in seconds (defaults to config value)
        
    Returns:
        Presigned URL string
        
    Raises:
        StorageError: If URL generation fails
    """
    if expires is None:
        expires = settings.S3_PRESIGNED_URL_EXPIRES
    
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.S3_BUCKET,
                "Key": key,
                "ContentType": "application/octet-stream",
            },
            ExpiresIn=expires,
        )
        logger.debug(f"Generated presigned URL for key: {key}, expires_in: {expires}")
        return url
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        logger.error(f"Failed to generate presigned URL: {error_code} - {e}")
        raise StorageError(f"Failed to generate presigned URL: {error_code}") from e
    except BotoCoreError as e:
        logger.error(f"BotoCore error generating presigned URL: {e}")
        raise StorageError(f"Storage service error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating presigned URL: {e}", exc_info=True)
        raise StorageError(f"Unexpected error: {str(e)}") from e


def object_exists(key: str) -> bool:
    """
    Check if an object exists in S3.
    
    Args:
        key: Object key in S3
        
    Returns:
        True if object exists, False otherwise
        
    Raises:
        StorageError: If check operation fails
    """
    try:
        s3_client.head_object(Bucket=settings.S3_BUCKET, Key=key)
        logger.debug(f"Object exists: {key}")
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            logger.debug(f"Object not found: {key}")
            return False
        logger.error(f"Error checking object existence: {error_code} - {e}")
        raise StorageError(f"Failed to check object existence: {error_code}") from e
    except BotoCoreError as e:
        logger.error(f"BotoCore error checking object: {e}")
        raise StorageError(f"Storage service error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error checking object: {e}", exc_info=True)
        raise StorageError(f"Unexpected error: {str(e)}") from e


def get_object_size(key: str) -> Optional[int]:
    """
    Get the size of an object in S3.
    
    Args:
        key: Object key in S3
        
    Returns:
        Object size in bytes, or None if object doesn't exist
        
    Raises:
        StorageError: If operation fails
    """
    try:
        response = s3_client.head_object(Bucket=settings.S3_BUCKET, Key=key)
        size = response.get("ContentLength")
        logger.debug(f"Object size for {key}: {size} bytes")
        return size
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            return None
        logger.error(f"Error getting object size: {error_code} - {e}")
        raise StorageError(f"Failed to get object size: {error_code}") from e
    except BotoCoreError as e:
        logger.error(f"BotoCore error getting object size: {e}")
        raise StorageError(f"Storage service error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting object size: {e}", exc_info=True)
        raise StorageError(f"Unexpected error: {str(e)}") from e


def check_storage_connection() -> bool:
    """Check if storage connection is healthy."""
    try:
        # Try to list buckets as a health check
        s3_client.list_buckets()
        return True
    except Exception as e:
        logger.error(f"Storage connection check failed: {e}")
        return False

