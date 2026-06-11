import aiomysql
import redis.asyncio as aioredis
from shared.id_generator import encode_base62, decode_base62, COUNTER_START


async def seed_counter_from_db(db_pool: aiomysql.Pool, redis_client: aioredis.Redis):
    """Seed the Redis counter to a value higher than the max existing alias ID."""
    existing = await redis_client.get("url:counter")
    if existing and int(existing) > 0:
        return

    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Find the max non-custom alias and decode it to get the next counter value
            await cur.execute(
                "SELECT alias FROM urls WHERE is_custom = FALSE ORDER BY id DESC LIMIT 1"
            )
            row = await cur.fetchone()
            if row:
                try:
                    num = decode_base62(row["alias"])
                    counter_value = num - COUNTER_START + 1
                    if counter_value > 0:
                        await redis_client.set("url:counter", counter_value)
                        return
                except Exception:
                    pass

    await redis_client.set("url:counter", 0)


async def generate_short_code(redis_client, db_pool, max_retries=3):
    """Generate a unique short code using Redis atomic counter + Base62 encoding.
    Falls back to DB check on collision.
    """
    for _ in range(max_retries):
        counter = await redis_client.incr("url:counter")
        code = encode_base62(COUNTER_START - 1 + counter)

        # Verify uniqueness in DB (belt-and-suspenders for stale volumes)
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1 FROM urls WHERE alias = %s LIMIT 1", (code,))
                if not await cur.fetchone():
                    return code

    # Fallback: random 7-char suffix
    import secrets
    for _ in range(10):
        suffix = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(7))
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1 FROM urls WHERE alias = %s LIMIT 1", (suffix,))
                if not await cur.fetchone():
                    return suffix

    raise RuntimeError("Failed to generate unique short code after multiple attempts")
