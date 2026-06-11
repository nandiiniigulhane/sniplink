import time
import redis.asyncio as aioredis
from fastapi import Request

from shared.config import Config
from shared.cache import get_redis


async def check_rate_limit(request: Request, redis_client: aioredis.Redis) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:{ip}"

    current = int(time.time())
    window_start = current // 60 * 60  # Floor to minute boundary

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start - 60)  # Remove old entries
    pipe.zcard(key)  # Count current window
    pipe.zadd(key, {str(current): current})  # Add current request
    pipe.expire(key, 120)  # TTL 2 minutes
    _, count, _, _ = await pipe.execute()

    return count < Config.RATE_LIMIT_PER_MINUTE
