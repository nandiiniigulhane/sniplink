import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request


class MockPipeline:
    """Mimics aioredis pipeline with chained methods returning self."""
    def zremrangebyscore(self, *args):
        return self

    def zcard(self, *args):
        return self

    def zadd(self, *args, **kwargs):
        return self

    def expire(self, *args):
        return self

    async def execute(self):
        return self._results

    def set_results(self, results):
        self._results = results


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    pipe = MockPipeline()
    redis.pipeline = MagicMock(return_value=pipe)
    return redis, pipe


class TestCheckRateLimit:
    async def test_under_limit_returns_true(self, mock_redis):
        redis, pipe = mock_redis
        pipe.set_results([0, 5, 1, 1])

        request = MagicMock(spec=Request)
        request.client.host = "192.168.1.1"

        from services.api_gateway.rate_limiter import check_rate_limit
        result = await check_rate_limit(request, redis)

        assert result is True

    async def test_at_limit_returns_false(self, mock_redis):
        redis, pipe = mock_redis
        pipe.set_results([0, 30, 1, 1])

        request = MagicMock(spec=Request)
        request.client.host = "192.168.1.1"

        from services.api_gateway.rate_limiter import check_rate_limit
        result = await check_rate_limit(request, redis)

        assert result is False

    async def test_over_limit_returns_false(self, mock_redis):
        redis, pipe = mock_redis
        pipe.set_results([0, 35, 1, 1])

        request = MagicMock(spec=Request)
        request.client.host = "192.168.1.1"

        from services.api_gateway.rate_limiter import check_rate_limit
        result = await check_rate_limit(request, redis)

        assert result is False

    async def test_no_client_ip_uses_unknown(self, mock_redis):
        redis, pipe = mock_redis
        pipe.set_results([0, 1, 1, 1])

        request = MagicMock(spec=Request)
        request.client = None

        from services.api_gateway.rate_limiter import check_rate_limit
        result = await check_rate_limit(request, redis)

        assert result is True
