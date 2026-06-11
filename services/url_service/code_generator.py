from shared.id_generator import encode_base62, COUNTER_START


async def generate_short_code(redis_client) -> str:
    """Generate a unique short code using Redis atomic counter + Base62 encoding."""
    counter = await redis_client.incr("url:counter")
    code = encode_base62(COUNTER_START - 1 + counter)
    return code
