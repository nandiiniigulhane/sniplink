import pytest
from unittest.mock import AsyncMock, patch


class TestGetRedis:
    async def test_creates_client_on_first_call(self):
        mock_client = AsyncMock()
        with patch("shared.cache.aioredis.Redis", return_value=mock_client):
            import shared.cache
            shared.cache._client = None

            result = await shared.cache.get_redis()
            assert result is mock_client
            shared.cache.aioredis.Redis.assert_called_once()

    async def test_returns_existing_client(self):
        mock_client = AsyncMock()
        with patch("shared.cache.aioredis.Redis", return_value=mock_client):
            import shared.cache
            shared.cache._client = mock_client

            result = await shared.cache.get_redis()
            assert result is mock_client
            shared.cache.aioredis.Redis.assert_not_called()
