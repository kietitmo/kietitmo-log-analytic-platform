"""
Redis queue management for job processing.
"""
import json
import redis
from typing import Optional
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from app.common.config import settings
from app.common.logger import get_logger
from app.common.exceptions.infrastucture import QueueError

logger = get_logger(__name__)

# Create Redis client with connection pooling and retry logic
redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client with proper configuration."""
    global redis_client
    if settings.ENVIRONMENT == "test":
        redis_client = None
        return redis_client

    if redis_client is None:
        try:
            redis_client = redis.Redis.from_url(
                settings.REDIS_URL,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                decode_responses=False,  # Keep binary for JSON
                retry_on_timeout=True,
                health_check_interval=30,
            )
            # Test connection
            redis_client.ping()
            logger.info("Redis client initialized successfully")
        except RedisConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise QueueError(f"Redis connection failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis: {e}")
            raise QueueError(f"Redis initialization failed: {str(e)}") from e
    
    return redis_client


def enqueue_job(message: dict) -> str:
    """
    Enqueue a job to Redis stream.
    
    Args:
        message: Job message dictionary
        
    Returns:
        Message ID from Redis stream
        
    Raises:
        QueueError: If enqueue operation fails
    """
    try:
        client = get_redis_client()
        message_id = client.xadd(
            settings.REDIS_STREAM_KEY,
            {"data": json.dumps(message)},
            maxlen=10000,  # Keep last 10000 messages
        )
        logger.info(f"Job enqueued successfully: message_id={message_id}, job_id={message.get('job_id')}")
        return message_id
    except RedisError as e:
        logger.error(f"Failed to enqueue job: {e}", exc_info=True)
        raise QueueError(f"Failed to enqueue job: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error enqueueing job: {e}", exc_info=True)
        raise QueueError(f"Unexpected error enqueueing job: {str(e)}") from e


def check_redis_connection() -> bool:
    """Check if Redis connection is healthy."""
    try:
        # Try to get existing client or create new one
        global redis_client
        if redis_client is None:
            # Try to create client without raising exception
            try:
                redis_client = redis.Redis.from_url(
                    settings.REDIS_URL,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                    decode_responses=False,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
            except Exception:
                return False
        
        redis_client.ping()
        return True
    except Exception as e:
        logger.debug(f"Redis connection check failed: {e}")
        return False

