import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class AsyncCMMock:
    """Mock that supports 'async with' by implementing __aenter__/__aexit__."""
    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass


class AcquireMock:
    """Mimics pool.acquire() — returns an async context manager directly."""
    def __init__(self, conn):
        self._conn = conn

    def __call__(self):
        return AsyncCMMock(self._conn)


@pytest.fixture
def mock_pool_fixture():
    cur = AsyncMock()
    conn = MagicMock()
    conn.cursor.return_value = AsyncCMMock(cur)

    pool = MagicMock()
    pool.acquire = AcquireMock(conn)

    return pool, conn, cur


class TestGetPool:
    async def test_creates_pool_on_first_call(self, mock_pool_fixture):
        pool, _, _ = mock_pool_fixture
        with patch("shared.database.aiomysql.create_pool", new=AsyncMock(return_value=pool)):
            import shared.database
            shared.database._pool = None
            result = await shared.database.get_pool()
            assert result is pool
            shared.database.aiomysql.create_pool.assert_called_once()

    async def test_returns_existing_pool(self, mock_pool_fixture):
        pool, _, _ = mock_pool_fixture
        with patch("shared.database.aiomysql.create_pool", new=AsyncMock(return_value=pool)):
            import shared.database
            shared.database._pool = pool
            result = await shared.database.get_pool()
            assert result is pool
            shared.database.aiomysql.create_pool.assert_not_called()


class TestInitDb:
    async def test_creates_tables(self, mock_pool_fixture):
        pool, conn, cur = mock_pool_fixture
        with patch("shared.database.get_pool", new=AsyncMock(return_value=pool)):
            import shared.database
            await shared.database.init_db()
            assert cur.execute.call_count >= 3

    async def test_alter_table_handles_existing_column(self, mock_pool_fixture):
        pool, conn, cur = mock_pool_fixture
        cur.execute = AsyncMock(side_effect=[None, Exception("Column exists"), None])
        conn.cursor.return_value = AsyncCMMock(cur)
        with patch("shared.database.get_pool", new=AsyncMock(return_value=pool)):
            import shared.database
            await shared.database.init_db()
            assert cur.execute.call_count == 3
