import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt


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
def mock_redis():
    return AsyncMock()


@pytest.fixture
def mock_db(cur_override=None):
    cur = cur_override or AsyncMock()
    conn = MagicMock()
    conn.cursor.return_value = AsyncCMMock(cur)
    pool = MagicMock()
    pool.acquire = AcquireMock(conn)
    return pool, conn, cur


class TestBcryptWrappers:
    def test_hash_and_verify_correct(self):
        from services.url_service.url_repository import hash_url_password, verify_url_password
        hashed = hash_url_password("secret")
        assert isinstance(hashed, str)
        assert hashed != "secret"
        assert verify_url_password("secret", hashed) is True

    def test_verify_wrong_password(self):
        from services.url_service.url_repository import hash_url_password, verify_url_password
        hashed = hash_url_password("secret")
        assert verify_url_password("wrong", hashed) is False


class TestCreateUrl:
    async def test_create_without_password_or_expiry(self, mock_redis, mock_db):
        pool, conn, cur = mock_db

        from services.url_service.url_repository import create_url
        result = await create_url(pool, mock_redis, "abc123", "https://example.com")

        assert result["alias"] == "abc123"
        assert result["long_url"] == "https://example.com"
        assert result["is_custom"] is False
        assert result["has_password"] is False
        assert result["expires_at"] is None
        cur.execute.assert_called_once()
        mock_redis.set.assert_called_once_with("url:abc123", "https://example.com")

    async def test_create_with_password_no_redis_cache(self, mock_redis, mock_db):
        pool, conn, cur = mock_db

        from services.url_service.url_repository import create_url
        result = await create_url(pool, mock_redis, "abc", "https://example.com", password="secret")

        assert result["has_password"] is True
        mock_redis.set.assert_not_called()
        mock_redis.setex.assert_not_called()

    async def test_create_with_expiry(self, mock_redis, mock_db):
        pool, conn, cur = mock_db

        from services.url_service.url_repository import create_url
        with patch("services.url_service.url_repository.datetime") as mock_dt:
            now = datetime(2026, 6, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = now
            result = await create_url(pool, mock_redis, "abc", "https://example.com", expires_in_days=7)

        assert result["expires_at"] is not None
        mock_redis.setex.assert_called_once()

    async def test_create_with_user_id(self, mock_redis, mock_db):
        pool, conn, cur = mock_db

        from services.url_service.url_repository import create_url
        result = await create_url(pool, mock_redis, "abc", "https://example.com", user_id=42)

        call_args = cur.execute.call_args
        assert 42 in call_args[0][1]


class TestLookupAlias:
    async def test_found_not_expired(self, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value={
            "alias": "abc", "has_password": 0, "expires_at": None, "long_url": "https://example.com"
        })

        from services.url_service.url_repository import lookup_alias
        result = await lookup_alias(pool, "abc")

        assert result["alias"] == "abc"
        assert result["has_password"] is False

    async def test_found_with_password(self, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value={
            "alias": "abc", "has_password": 1, "expires_at": None, "long_url": "https://example.com"
        })

        from services.url_service.url_repository import lookup_alias
        result = await lookup_alias(pool, "abc")

        assert result["has_password"] is True

    async def test_not_found(self, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value=None)

        from services.url_service.url_repository import lookup_alias
        result = await lookup_alias(pool, "abc")

        assert result is None

    async def test_expired_deletes_and_returns_none(self, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value={
            "alias": "abc", "has_password": 0,
            "expires_at": datetime(2020, 1, 1), "long_url": "https://example.com"
        })

        from services.url_service.url_repository import lookup_alias
        result = await lookup_alias(pool, "abc")

        assert result is None
        # Should have executed DELETE
        delete_calls = [c for c in cur.execute.call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) > 0


class TestVerifyAndGetUrl:
    async def test_no_password_returns_url(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value={
            "long_url": "https://example.com", "password_hash": None, "expires_at": None
        })

        from services.url_service.url_repository import verify_and_get_url
        result = await verify_and_get_url(pool, mock_redis, "abc", "any")

        assert result == "https://example.com"

    async def test_correct_password_returns_url(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        hashed = bcrypt.hashpw("secret".encode(), bcrypt.gensalt()).decode()
        cur.fetchone = AsyncMock(return_value={
            "long_url": "https://example.com", "password_hash": hashed, "expires_at": None
        })

        from services.url_service.url_repository import verify_and_get_url
        result = await verify_and_get_url(pool, mock_redis, "abc", "secret")

        assert result == "https://example.com"

    async def test_wrong_password_returns_none(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        hashed = bcrypt.hashpw("secret".encode(), bcrypt.gensalt()).decode()
        cur.fetchone = AsyncMock(return_value={
            "long_url": "https://example.com", "password_hash": hashed, "expires_at": None
        })

        from services.url_service.url_repository import verify_and_get_url
        result = await verify_and_get_url(pool, mock_redis, "abc", "wrong")

        assert result is None

    async def test_not_found_returns_none(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value=None)

        from services.url_service.url_repository import verify_and_get_url
        result = await verify_and_get_url(pool, mock_redis, "abc", "any")

        assert result is None

    async def test_expired_returns_none(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value={
            "long_url": "https://example.com", "password_hash": None,
            "expires_at": datetime(2020, 1, 1)
        })

        from services.url_service.url_repository import verify_and_get_url
        result = await verify_and_get_url(pool, mock_redis, "abc", "any")

        assert result is None


class TestGetUrl:
    async def test_cache_hit(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        mock_redis.get.return_value = "https://cached.example.com"

        from services.url_service.url_repository import get_url
        result = await get_url(pool, mock_redis, "abc")

        assert result == "https://cached.example.com"
        cur.execute.assert_not_called()

    async def test_cache_miss_db_not_found(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        mock_redis.get.return_value = None
        cur.fetchone = AsyncMock(return_value=None)

        from services.url_service.url_repository import get_url
        result = await get_url(pool, mock_redis, "abc")

        assert result is None

    async def test_cache_miss_fetches_from_db(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        mock_redis.get.return_value = None
        cur.fetchone = AsyncMock(return_value={
            "long_url": "https://example.com", "password_hash": None, "expires_at": None
        })

        from services.url_service.url_repository import get_url
        result = await get_url(pool, mock_redis, "abc")

        assert result == "https://example.com"
        mock_redis.set.assert_called_once_with("url:abc", "https://example.com")

    async def test_password_protected_returns_none(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        mock_redis.get.return_value = None
        hashed = bcrypt.hashpw("secret".encode(), bcrypt.gensalt()).decode()
        cur.fetchone = AsyncMock(return_value={
            "long_url": "https://example.com", "password_hash": hashed, "expires_at": None
        })

        from services.url_service.url_repository import get_url
        result = await get_url(pool, mock_redis, "abc")

        assert result is None

    async def test_expired_returns_none_and_deletes(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        mock_redis.get.return_value = None
        cur.fetchone = AsyncMock(return_value={
            "long_url": "https://example.com", "password_hash": None,
            "expires_at": datetime(2020, 1, 1)
        })

        from services.url_service.url_repository import get_url
        result = await get_url(pool, mock_redis, "abc")

        assert result is None

    async def test_with_expiry_caches_with_ttl(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        mock_redis.get.return_value = None
        future = datetime.utcnow() + timedelta(days=30)
        cur.fetchone = AsyncMock(return_value={
            "long_url": "https://example.com", "password_hash": None,
            "expires_at": future
        })

        from services.url_service.url_repository import get_url
        result = await get_url(pool, mock_redis, "abc")

        assert result == "https://example.com"
        mock_redis.setex.assert_called_once()


class TestAliasExists:
    async def test_exists(self, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value={"1": 1})

        from services.url_service.url_repository import alias_exists
        result = await alias_exists(pool, "abc")

        assert result is True

    async def test_not_exists(self, mock_db):
        pool, conn, cur = mock_db
        cur.fetchone = AsyncMock(return_value=None)

        from services.url_service.url_repository import alias_exists
        result = await alias_exists(pool, "abc")

        assert result is False


class TestGetUserUrls:
    async def test_returns_list(self, mock_db):
        pool, conn, cur = mock_db
        cur.fetchall = AsyncMock(return_value=[
            {
                "alias": "abc", "long_url": "https://a.com", "is_custom": False,
                "password_hash": None, "expires_at": None,
                "created_at": datetime(2026, 6, 1),
            },
            {
                "alias": "def", "long_url": "https://b.com", "is_custom": True,
                "password_hash": "hash", "expires_at": datetime(2026, 7, 1),
                "created_at": datetime(2026, 6, 2),
            },
        ])

        from services.url_service.url_repository import get_user_urls
        result = await get_user_urls(pool, 42)

        assert len(result) == 2
        assert result[0]["alias"] == "abc"
        assert result[0]["has_password"] is False
        assert result[1]["alias"] == "def"
        assert result[1]["has_password"] is True
        assert result[1]["is_custom"] is True

    async def test_empty_list(self, mock_db):
        pool, conn, cur = mock_db
        cur.fetchall = AsyncMock(return_value=[])

        from services.url_service.url_repository import get_user_urls
        result = await get_user_urls(pool, 42)

        assert result == []


class TestDeleteUrl:
    async def test_delete_owned_returns_true(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        cur.rowcount = 1

        from services.url_service.url_repository import delete_url
        result = await delete_url(pool, mock_redis, "abc", 42)

        assert result is True
        mock_redis.delete.assert_called_once_with("url:abc")

    async def test_delete_not_owned_returns_false(self, mock_redis, mock_db):
        pool, conn, cur = mock_db
        cur.rowcount = 0

        from services.url_service.url_repository import delete_url
        result = await delete_url(pool, mock_redis, "abc", 42)

        assert result is False
        mock_redis.delete.assert_not_called()
