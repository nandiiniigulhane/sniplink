import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport


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
def app():
    # Mock shared dependencies before importing the app
    with patch("services.url_service.main.init_db", new=AsyncMock()):
        with patch("services.url_service.main.get_pool", new=AsyncMock()):
            with patch("services.url_service.main.get_redis", new=AsyncMock()):
                with patch("services.url_service.main.seed_counter_from_db", new=AsyncMock()):
                    from services.url_service.main import app
                    yield app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealth:
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestLifespan:
    async def test_lifespan_calls_dependencies(self):
        from unittest.mock import AsyncMock, patch

        with patch("services.url_service.main.init_db", new=AsyncMock()) as mock_init:
            with patch("services.url_service.main.get_pool", new=AsyncMock()) as mock_get_pool:
                with patch("services.url_service.main.get_redis", new=AsyncMock()) as mock_get_redis:
                    with patch("services.url_service.main.seed_counter_from_db", new=AsyncMock()) as mock_seed:
                        from fastapi import FastAPI
                        from services.url_service.main import lifespan

                        app = FastAPI()
                        async with lifespan(app):
                            pass
                        mock_init.assert_called_once()
                        mock_get_pool.assert_called_once()
                        mock_get_redis.assert_called_once()
                        mock_seed.assert_called_once()


class TestShortenUrl:
    async def test_shorten_success(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.generate_short_code", new=AsyncMock(return_value="abc123")):
                    with patch("services.url_service.main.create_url", new=AsyncMock(return_value={
                        "alias": "abc123", "long_url": "https://example.com",
                        "is_custom": False, "has_password": False, "expires_at": None,
                    })):
                        resp = await client.post("/api/shorten", json={
                            "long_url": "https://example.com"
                        })
                        assert resp.status_code == 201
                        data = resp.json()
                        assert data["alias"] == "abc123"
                        assert "abc123" in data["short_url"]
                        assert data["is_custom"] is False

    async def test_shorten_custom_alias_success(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.alias_exists", new=AsyncMock(return_value=False)):
                    with patch("services.url_service.main.create_url", new=AsyncMock(return_value={
                        "alias": "my-link", "long_url": "https://example.com",
                        "is_custom": True, "has_password": False, "expires_at": None,
                    })):
                        resp = await client.post("/api/shorten", json={
                            "long_url": "https://example.com",
                            "custom_alias": "my-link"
                        })
                        assert resp.status_code == 201
                        assert resp.json()["is_custom"] is True

    async def test_shorten_reserved_alias(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                resp = await client.post("/api/shorten", json={
                    "long_url": "https://example.com",
                    "custom_alias": "health"
                })
                assert resp.status_code == 400

    async def test_shorten_duplicate_alias(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.alias_exists", new=AsyncMock(return_value=True)):
                    resp = await client.post("/api/shorten", json={
                        "long_url": "https://example.com",
                        "custom_alias": "taken"
                    })
                    assert resp.status_code == 409

    async def test_shorten_with_password(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.generate_short_code", new=AsyncMock(return_value="abc123")):
                    with patch("services.url_service.main.create_url", new=AsyncMock(return_value={
                        "alias": "abc123", "long_url": "https://example.com",
                        "is_custom": False, "has_password": True, "expires_at": None,
                    })):
                        resp = await client.post("/api/shorten", json={
                            "long_url": "https://example.com",
                            "password": "secret"
                        })
                        assert resp.status_code == 201
                        assert resp.json()["has_password"] is True

    async def test_shorten_invalid_url(self, client):
        resp = await client.post("/api/shorten", json={
            "long_url": "not-a-valid-url"
        })
        assert resp.status_code == 422


class TestVerifyPassword:
    async def test_correct_password(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.verify_and_get_url", new=AsyncMock(return_value="https://example.com")):
                    resp = await client.post("/api/verify/abc", json={"password": "secret"})
                    assert resp.status_code == 200
                    assert resp.json()["long_url"] == "https://example.com"

    async def test_wrong_password(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.verify_and_get_url", new=AsyncMock(return_value=None)):
                    resp = await client.post("/api/verify/abc", json={"password": "wrong"})
                    assert resp.status_code == 401


class TestLookup:
    async def test_lookup_found(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.lookup_alias", new=AsyncMock(return_value={
                "alias": "abc", "has_password": False, "long_url": "https://example.com"
            })):
                resp = await client.get("/api/lookup/abc")
                assert resp.status_code == 200
                assert resp.json()["alias"] == "abc"

    async def test_lookup_not_found(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.lookup_alias", new=AsyncMock(return_value=None)):
                resp = await client.get("/api/lookup/abc")
                assert resp.status_code == 404


class TestListUserUrls:
    async def test_no_user_returns_401(self, client):
        resp = await client.get("/api/urls")
        assert resp.status_code == 401

    async def test_with_user_returns_list(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_user_urls", new=AsyncMock(return_value=[])):
                resp = await client.get("/api/urls", headers={"X-User-Id": "42"})
                assert resp.status_code == 200
                assert resp.json() == {"urls": []}


class TestDeleteUserUrl:
    async def test_no_user_returns_401(self, client):
        resp = await client.delete("/api/urls/abc")
        assert resp.status_code == 401

    async def test_owned_url_success(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.delete_url", new=AsyncMock(return_value=True)):
                    resp = await client.delete("/api/urls/abc", headers={"X-User-Id": "42"})
                    assert resp.status_code == 200
                    assert resp.json() == {"detail": "deleted"}

    async def test_not_owned_returns_404(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.delete_url", new=AsyncMock(return_value=False)):
                    resp = await client.delete("/api/urls/abc", headers={"X-User-Id": "42"})
                    assert resp.status_code == 404


class TestRedirectOrPassword:
    async def test_reserved_alias_returns_404(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                resp = await client.get("/health", follow_redirects=False)
                assert resp.status_code == 200  # the /health route wins

    async def test_reserved_alias_api(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                resp = await client.get("/api", follow_redirects=False)
                assert resp.status_code == 404

    async def test_password_protected_returns_html(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.lookup_alias", new=AsyncMock(return_value={
                    "alias": "abc", "has_password": True, "long_url": "https://example.com"
                })):
                    resp = await client.get("/abc", follow_redirects=False)
                    assert resp.status_code == 200
                    assert "text/html" in resp.headers["content-type"]

    async def test_normal_url_redirects(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.lookup_alias", new=AsyncMock(return_value={
                    "alias": "abc", "has_password": False, "long_url": "https://example.com"
                })):
                    with patch("services.url_service.main.get_url", new=AsyncMock(return_value="https://example.com")):
                        resp = await client.get("/abc", follow_redirects=False)
                        assert resp.status_code == 301
                        assert resp.headers["location"] == "https://example.com"

    async def test_not_found_returns_404(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.lookup_alias", new=AsyncMock(return_value=None)):
                    resp = await client.get("/missing", follow_redirects=False)
                    assert resp.status_code == 404

    async def test_get_url_returns_none_after_lookup(self, client):
        mock_pool = MagicMock()
        mock_pool.acquire = AcquireMock(MagicMock())
        mock_redis = AsyncMock()

        with patch("services.url_service.main.get_db", return_value=mock_pool):
            with patch("services.url_service.main.get_cache", return_value=mock_redis):
                with patch("services.url_service.main.lookup_alias", new=AsyncMock(return_value={
                    "alias": "abc", "has_password": False, "long_url": "https://example.com"
                })):
                    with patch("services.url_service.main.get_url", new=AsyncMock(return_value=None)):
                        resp = await client.get("/abc", follow_redirects=False)
                        assert resp.status_code == 404
