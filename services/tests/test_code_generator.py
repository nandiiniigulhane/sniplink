import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from shared.id_generator import encode_base62, COUNTER_START, decode_base62


class AsyncCMMock:
    """Mock that supports 'async with'."""
    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass


class AcquireMock:
    def __init__(self, conn):
        self._conn = conn

    def __call__(self):
        return AsyncCMMock(self._conn)


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def mock_db_pool():
    cur = AsyncMock()
    cur.fetchone = AsyncMock(return_value=None)
    conn = MagicMock()
    conn.cursor.return_value = AsyncCMMock(cur)
    pool = MagicMock()
    pool.acquire = AcquireMock(conn)
    return pool, conn, cur


class TestSeedCounterFromDb:
    async def test_counter_exists_and_positive_returns_early(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        mock_redis.get.return_value = "100"

        from services.url_service.code_generator import seed_counter_from_db
        await seed_counter_from_db(pool, mock_redis)

        # Should NOT query DB
        cur.execute.assert_not_called()
        mock_redis.set.assert_not_called()

    async def test_counter_missing_seeds_from_db(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        mock_redis.get.return_value = None
        cur.fetchone.return_value = {"alias": encode_base62(COUNTER_START + 50)}

        from services.url_service.code_generator import seed_counter_from_db
        await seed_counter_from_db(pool, mock_redis)

        cur.execute.assert_called_once()
        mock_redis.set.assert_called_once_with("url:counter", 51)

    async def test_counter_zero_seeds_from_db(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        mock_redis.get.return_value = "0"
        cur.fetchone.return_value = {"alias": encode_base62(COUNTER_START + 10)}

        from services.url_service.code_generator import seed_counter_from_db
        await seed_counter_from_db(pool, mock_redis)

        cur.execute.assert_called_once()
        mock_redis.set.assert_called_once()

    async def test_empty_db_sets_counter_to_zero(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        mock_redis.get.return_value = None
        cur.fetchone.return_value = None

        from services.url_service.code_generator import seed_counter_from_db
        await seed_counter_from_db(pool, mock_redis)

        mock_redis.set.assert_called_once_with("url:counter", 0)

    async def test_decode_error_falls_back_to_zero(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        mock_redis.get.return_value = None
        cur.fetchone.return_value = {"alias": "@@@invalid@@@"}

        from services.url_service.code_generator import seed_counter_from_db
        await seed_counter_from_db(pool, mock_redis)

        mock_redis.set.assert_called_once_with("url:counter", 0)


class TestGenerateShortCode:
    async def test_normal_generation_no_collision(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        cur.fetchone.return_value = None  # No DB collision
        mock_redis.incr.return_value = 1

        from services.url_service.code_generator import generate_short_code
        code = await generate_short_code(mock_redis, pool)

        assert len(code) >= 6
        mock_redis.incr.assert_called_once_with("url:counter")

    async def test_collision_then_success(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        # First attempt: DB returns row (collision), second attempt: no row
        cur.fetchone = AsyncMock(side_effect=[{"1": 1}, None])
        mock_redis.incr.return_value = 5

        from services.url_service.code_generator import generate_short_code
        code = await generate_short_code(mock_redis, pool)

        assert len(code) >= 6
        assert mock_redis.incr.call_count == 2

    async def test_all_retries_exhausted_falls_back_to_random(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        # All main retries collide
        cur.fetchone = AsyncMock(side_effect=[
            {"1": 1}, {"1": 1}, {"1": 1},  # 3 retries, all collide
            None,  # First random falls through
        ])
        mock_redis.incr.return_value = 1

        from services.url_service.code_generator import generate_short_code
        code = await generate_short_code(mock_redis, pool)

        assert len(code) == 7
        assert mock_redis.incr.call_count == 3

    async def test_all_attempts_exhausted_raises(self, mock_redis, mock_db_pool):
        pool, conn, cur = mock_db_pool
        cur.fetchone = AsyncMock(return_value={"1": 1})
        mock_redis.incr.return_value = 1

        from services.url_service.code_generator import generate_short_code
        with pytest.raises(RuntimeError, match="Failed to generate"):
            await generate_short_code(mock_redis, pool)
