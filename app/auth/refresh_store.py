import hashlib
from app.redis_client import get_redis
from app.config import settings


def _token_key(user_id: int, token: str) -> str:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return f'refresh:tasktracker:{user_id}:{token_hash}'


async def store_refresh_token_in_redis(user_id: int, token: str, ttl_days: int = settings.REFRESH_TOKEN_TTL_DAYS):
    redis = await get_redis()
    print(f'store_refresh: {token}')
    key = _token_key(user_id, token)
    await redis.set(key, '1', ex = ttl_days * 24 * 3600)


async def is_refresh_token_in_redis_valid(user_id: int, token: str) -> bool:
    redis = await get_redis()
    key = _token_key(user_id, token)
    value = await redis.get(key)
    return value is not None


async def delete_refresh_token_from_redis(user_id: int, token: str):
    redis = await get_redis()
    key = _token_key(user_id, token)
    await redis.delete(key)

