import logging
from redis.asyncio import ConnectionPool, Redis
from app.config import settings


logger = logging.getLogger(__name__)


redis_pool: ConnectionPool | None = None
redis_client: Redis | None = None


def init_redis() -> None:
    global redis_pool, redis_client

    redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=20,
        socket_timeout=2.0,
        retry_on_timeout=True,
    )
    redis_client = Redis(connection_pool=redis_pool)
    logger.info("Redis connection pool successfully initialized.")


async def close_redis() -> None:
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        logger.info("Redis connection pool successfully closed.")


async def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError(
            "Redis client is not initialized. Call init_redis() first."
        )
    return redis_client