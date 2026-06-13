import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport, Response, Request
from services.auth_service.jwt_handler import create_access_token
import asyncio



class MockHttpxResponse:
    """Fake response that mimics httpx.Response enough for the gateway."""
    def __init__(self, status_code=200, content=b"{}", headers=None, location=None):
        self.status_code = status_code
        self.content = content
        self._headers = headers or {}
        if location:
            self._headers["location"] = location

    @property
    def headers(self):
        return self._headers


class MockAsyncClient:
    """Mock for httpx.AsyncClient used inside gateway routes."""
    def __init__(self, *args, **kwargs):
        self._calls = []
        self.mock_responses = {}

    def set_response(self, method, url, response):
        self.mock_responses[(method.upper(), str(url))] = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, **kwargs):
        self._calls.append(("POST", url, kwargs))
        return self.mock_responses.get(("POST", str(url)), MockHttpxResponse())

    async def get(self, url, **kwargs):
        self._calls.append(("GET", url, kwargs))
        return self.mock_responses.get(("GET", str(url)), MockHttpxResponse())

    async def delete(self, url, **kwargs):
        self._calls.append(("DELETE", url, kwargs))
        return self.mock_responses.get(("DELETE", str(url)), MockHttpxResponse())

    async def request(self, method, url, **kwargs):
        self._calls.append((method, url, kwargs))
        return self.mock_responses.get((method.upper(), str(url)), MockHttpxResponse())

    def last_call(self):
        return self._calls[-1] if self._calls else None


@pytest.fixture
def mock_httpx():
    client = MockAsyncClient()
    with patch("httpx.AsyncClient", return_value=client):
        yield client


@pytest.fixture
def app():
    with patch("shared.cache.get_redis", new=AsyncMock()):
        from services.api_gateway.main import app
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


class TestExtractUserContext:
    def test_no_auth_header(self, app):
        from services.api_gateway.main import extract_user_context
        request = MagicMock()
        request.headers = {}
        result = extract_user_context(request)
        assert result is None

    def test_malformed_header(self, app):
        from services.api_gateway.main import extract_user_context
        request = MagicMock()
        request.headers = {"Authorization": "InvalidFormat"}
        result = extract_user_context(request)
        assert result is None

    def test_valid_token(self, app):
        token = create_access_token(42, "user@test.com")
        from services.api_gateway.main import extract_user_context
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}
        result = extract_user_context(request)
        assert result["id"] == "42"
        assert result["email"] == "user@test.com"

    def test_expired_token(self, app):
        from services.api_gateway.main import extract_user_context
        with patch("services.api_gateway.main.decode_access_token", side_effect=Exception("expired")):
            request = MagicMock()
            request.headers = {"Authorization": "Bearer expired.token.here"}
            result = extract_user_context(request)
            assert result is None


class TestProxyShorten:
    async def test_under_rate_limit(self, client, mock_httpx):
        mock_httpx.set_response("POST", "http://localhost:8001/api/shorten",
                                MockHttpxResponse(201, b'{"alias":"abc123"}'))
        with patch("services.api_gateway.main.check_rate_limit", new=AsyncMock(return_value=True)):
            resp = await client.post("/api/shorten", json={"long_url": "https://example.com"})
            assert resp.status_code == 201

    async def test_over_rate_limit(self, client):
        with patch("services.api_gateway.main.check_rate_limit", new=AsyncMock(return_value=False)):
            resp = await client.post("/api/shorten", json={"long_url": "https://example.com"})
            assert resp.status_code == 429

    async def test_with_auth_forwards_user_id(self, client, mock_httpx):
        token = create_access_token(42, "user@test.com")
        mock_httpx.set_response("POST", "http://localhost:8001/api/shorten",
                                MockHttpxResponse(201, b'{"alias":"abc123"}'))

        with patch("services.api_gateway.main.check_rate_limit", new=AsyncMock(return_value=True)):
            resp = await client.post(
                "/api/shorten",
                json={"long_url": "https://example.com"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 201
            _, _, kwargs = mock_httpx.last_call()
            assert kwargs["headers"]["X-User-Id"] == "42"


class TestProxyVerify:
    async def test_proxy_verify(self, client, mock_httpx):
        mock_httpx.set_response("POST", "http://localhost:8001/api/verify/abc",
                                MockHttpxResponse(200, b'{"long_url":"https://example.com"}'))
        resp = await client.post("/api/verify/abc", json={"password": "secret"})
        assert resp.status_code == 200


class TestProxyLookup:
    async def test_proxy_lookup(self, client, mock_httpx):
        mock_httpx.set_response("GET", "http://localhost:8001/api/lookup/abc",
                                MockHttpxResponse(200, b'{"alias":"abc","has_password":false}'))
        resp = await client.get("/api/lookup/abc")
        assert resp.status_code == 200


class TestProxyListUrls:
    async def test_no_auth_returns_401(self, client):
        resp = await client.get("/api/urls")
        assert resp.status_code == 401

    async def test_with_auth_proxies(self, client, mock_httpx):
        token = create_access_token(42, "user@test.com")
        mock_httpx.set_response("GET", "http://localhost:8001/api/urls",
                                MockHttpxResponse(200, b'{"urls":[]}'))
        resp = await client.get("/api/urls", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200


class TestProxyDeleteUrl:
    async def test_no_auth_returns_401(self, client):
        resp = await client.delete("/api/urls/abc")
        assert resp.status_code == 401

    async def test_with_auth_proxies(self, client, mock_httpx):
        token = create_access_token(42, "user@test.com")
        mock_httpx.set_response("DELETE", "http://localhost:8001/api/urls/abc",
                                MockHttpxResponse(200, b'{"detail":"deleted"}'))
        resp = await client.delete("/api/urls/abc", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200


class TestProxyAuth:
    async def test_auth_proxy_get(self, client, mock_httpx):
        mock_httpx.set_response("GET", "http://localhost:8002/api/auth/health",
                                MockHttpxResponse(200, b'{"status":"ok"}'))
        resp = await client.get("/api/auth/health")
        assert resp.status_code == 200

    async def test_auth_proxy_post(self, client, mock_httpx):
        mock_httpx.set_response("POST", "http://localhost:8002/api/auth/login",
                                MockHttpxResponse(201, b'{"access_token":"x"}'))
        resp = await client.post("/api/auth/login", json={"email": "a@b.com", "password": "secret"})
        assert resp.status_code == 201


class TestProxyRedirect:
    async def test_reserved_alias(self, client):
        resp = await client.get("/health", follow_redirects=False)
        assert resp.status_code == 200

    async def test_reserved_alias_api(self, client):
        resp = await client.get("/api", follow_redirects=False)
        assert resp.status_code == 404

    async def test_redirect_response(self, client, mock_httpx):
        mock_httpx.set_response("GET", "http://localhost:8001/abc",
                                MockHttpxResponse(200, location="https://example.com",
                                                  headers={"content-type": "application/json"}))
        resp = await client.get("/abc", follow_redirects=False)
        assert resp.status_code == 301
        assert resp.headers["location"] == "https://example.com"

    async def test_password_page_html_response(self, client, mock_httpx):
        mock_httpx.set_response("GET", "http://localhost:8001/abc",
                                MockHttpxResponse(200, content=b"<html>...</html>",
                                                  headers={"content-type": "text/html"}))
        resp = await client.get("/abc", follow_redirects=False)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    async def test_not_found(self, client, mock_httpx):
        mock_httpx.set_response("GET", "http://localhost:8001/abc",
                                MockHttpxResponse(404))
        resp = await client.get("/abc", follow_redirects=False)
        assert resp.status_code == 404

    async def test_no_location_returns_404(self, client, mock_httpx):
        # URL service returns 200 but with json content and no location header
        mock_httpx.set_response("GET", "http://localhost:8001/abc",
                                MockHttpxResponse(200, content=b'{}', headers={"content-type": "application/json"}))
        resp = await client.get("/abc", follow_redirects=False)
        assert resp.status_code == 404
