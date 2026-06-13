import pytest
from unittest.mock import AsyncMock, MagicMock
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


def make_pool_with_cursor(cur):
    conn = MagicMock()
    conn.cursor.return_value = AsyncCMMock(cur)
    pool = MagicMock()
    pool.acquire = AcquireMock(conn)
    return pool


@pytest.fixture
def app():
    from services.auth_service.main import app
    from services.auth_service.jwt_handler import create_access_token
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
    async def test_lifespan_runs_init_db(self):
        from unittest.mock import AsyncMock, patch
        with patch("services.auth_service.main.init_db", new=AsyncMock()) as mock_init:
            with patch("services.auth_service.main.get_pool", new=AsyncMock()) as mock_pool:
                from fastapi import FastAPI
                from services.auth_service.main import lifespan

                app = FastAPI()
                async with lifespan(app):
                    pass
                mock_init.assert_called_once()

    async def test_get_db_calls_get_pool(self):
        from unittest.mock import AsyncMock, patch
        mock_pool = AsyncMock()
        with patch("services.auth_service.main.get_pool", new=mock_pool):
            from services.auth_service.main import get_db
            result = await get_db()
            assert result is mock_pool.return_value


class TestRegister:
    async def test_success(self, app, client):
        from services.auth_service.main import get_db

        cur = AsyncMock()
        cur.lastrowid = 1
        cur.fetchone = AsyncMock(return_value=None)
        pool = make_pool_with_cursor(cur)

        app.dependency_overrides[get_db] = lambda: pool

        resp = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "test@example.com"

    async def test_duplicate_email(self, client):
        from services.auth_service.main import app as auth_app

        cur = AsyncMock()
        cur.fetchone = AsyncMock(return_value={
            "id": 1, "email": "test@example.com", "password_hash": "hash"
        })
        pool = make_pool_with_cursor(cur)

        from services.auth_service.main import get_db
        auth_app.dependency_overrides[get_db] = lambda: pool

        resp = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert resp.status_code == 409

    async def test_invalid_email(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "notanemail",
            "password": "password123"
        })
        assert resp.status_code == 422

    async def test_short_password(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "short"
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_success(self, client):
        from services.auth_service.main import app as auth_app
        from services.auth_service.main import get_db
        from services.auth_service.user_repository import hash_password

        hashed = hash_password("password123")
        cur = AsyncMock()
        cur.fetchone = AsyncMock(return_value={
            "id": 1, "email": "test@example.com", "password_hash": hashed
        })
        pool = make_pool_with_cursor(cur)

        auth_app.dependency_overrides[get_db] = lambda: pool

        resp = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "test@example.com"

    async def test_wrong_password(self, client):
        from services.auth_service.main import app as auth_app
        from services.auth_service.main import get_db
        from services.auth_service.user_repository import hash_password

        hashed = hash_password("correct_password")
        cur = AsyncMock()
        cur.fetchone = AsyncMock(return_value={
            "id": 1, "email": "test@example.com", "password_hash": hashed
        })
        pool = make_pool_with_cursor(cur)

        auth_app.dependency_overrides[get_db] = lambda: pool

        resp = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrong_password"
        })
        assert resp.status_code == 401

    async def test_user_not_found(self, client):
        from services.auth_service.main import app as auth_app
        from services.auth_service.main import get_db

        cur = AsyncMock()
        cur.fetchone = AsyncMock(return_value=None)
        pool = make_pool_with_cursor(cur)

        auth_app.dependency_overrides[get_db] = lambda: pool

        resp = await client.post("/api/auth/login", json={
            "email": "unknown@example.com",
            "password": "password123"
        })
        assert resp.status_code == 401

    async def test_invalid_email_format(self, client):
        # LoginRequest has no email validator, so invalid emails pass
        # to the DB lookup and get 401 user-not-found
        from services.auth_service.main import app as auth_app
        from services.auth_service.main import get_db

        cur = AsyncMock()
        cur.fetchone = AsyncMock(return_value=None)
        pool = make_pool_with_cursor(cur)

        auth_app.dependency_overrides[get_db] = lambda: pool

        resp = await client.post("/api/auth/login", json={
            "email": "notanemail",
            "password": "password123"
        })
        assert resp.status_code == 401
