from datetime import datetime, timedelta
from typing import Optional
import aiomysql
import redis.asyncio as aioredis

from shared.config import Config


async def create_url(
    db_pool: aiomysql.Pool,
    redis_client: aioredis.Redis,
    alias: str,
    long_url: str,
    is_custom: bool = False,
    user_id: Optional[int] = None,
    expires_in_days: Optional[int] = None,
) -> dict:
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO urls (alias, long_url, is_custom, user_id, expires_at) VALUES (%s, %s, %s, %s, %s)",
                (alias, long_url, is_custom, user_id, expires_at),
            )

    cache_ttl = None
    if expires_at:
        cache_ttl = int((expires_at - datetime.utcnow()).total_seconds())
    if cache_ttl and cache_ttl > 0:
        await redis_client.setex(f"url:{alias}", cache_ttl, long_url)
    else:
        await redis_client.set(f"url:{alias}", long_url)

    return {
        "alias": alias,
        "long_url": long_url,
        "is_custom": is_custom,
        "expires_at": expires_at,
    }


async def get_url(db_pool: aiomysql.Pool, redis_client: aioredis.Redis, alias: str) -> Optional[str]:
    cached = await redis_client.get(f"url:{alias}")
    if cached:
        return cached

    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT long_url, expires_at FROM urls WHERE alias = %s",
                (alias,),
            )
            row = await cur.fetchone()
            if row is None:
                return None

            if row["expires_at"] and row["expires_at"] < datetime.utcnow():
                await cur.execute("DELETE FROM urls WHERE alias = %s", (alias,))
                return None

            long_url = row["long_url"]
            if row["expires_at"]:
                ttl = int((row["expires_at"] - datetime.utcnow()).total_seconds())
                if ttl > 0:
                    await redis_client.setex(f"url:{alias}", ttl, long_url)
            else:
                await redis_client.set(f"url:{alias}", long_url)

            return long_url


async def alias_exists(db_pool: aiomysql.Pool, alias: str) -> bool:
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1 FROM urls WHERE alias = %s LIMIT 1", (alias,))
            return await cur.fetchone() is not None
