import pytest
from unittest.mock import AsyncMock, MagicMock, patch



class AsyncCMMock:
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
def mock_db_pool():
    cur = AsyncMock()
    conn = MagicMock()
    conn.cursor.return_value = AsyncCMMock(cur)
    pool = MagicMock()
    pool.acquire = AcquireMock(conn)
    return pool, conn, cur


class TestHashPassword:
    def test_returns_string(self):
        from services.auth_service.user_repository import hash_password
        result = hash_password("secret")
        assert isinstance(result, str)
        assert result != "secret"

    def test_produces_different_hash(self):
        from services.auth_service.user_repository import hash_password
        h1 = hash_password("secret")
        h2 = hash_password("secret")
        assert h1 != h2  # bcrypt uses random salt


class TestVerifyPassword:
    def test_correct_password(self):
        from services.auth_service.user_repository import hash_password, verify_password
        hashed = hash_password("secret")
        assert verify_password("secret", hashed) is True

    def test_wrong_password(self):
        from services.auth_service.user_repository import hash_password, verify_password
        hashed = hash_password("secret")
        assert verify_password("wrong", hashed) is False


class TestCreateUser:
    async def test_creates_user(self, mock_db_pool):
        pool, conn, cur = mock_db_pool
        cur.lastrowid = 42

        from services.auth_service.user_repository import create_user
        result = await create_user(pool, "test@example.com", "password123")

        assert result["id"] == 42
        assert result["email"] == "test@example.com"
        cur.execute.assert_called_once()


class TestGetUserByEmail:
    async def test_user_found(self, mock_db_pool):
        pool, conn, cur = mock_db_pool
        cur.fetchone = AsyncMock(return_value={
            "id": 42, "email": "test@example.com", "password_hash": "hash"
        })

        from services.auth_service.user_repository import get_user_by_email
        result = await get_user_by_email(pool, "test@example.com")

        assert result["id"] == 42
        assert result["email"] == "test@example.com"

    async def test_user_not_found(self, mock_db_pool):
        pool, conn, cur = mock_db_pool
        cur.fetchone = AsyncMock(return_value=None)

        from services.auth_service.user_repository import get_user_by_email
        result = await get_user_by_email(pool, "nonexistent@example.com")

        assert result is None
