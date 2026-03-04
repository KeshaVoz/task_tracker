from redis.asyncio import Redis
from app.config import settings


redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=0,
    decode_responses=True,
    max_connections=10
)


async def get_redis():
    return redis