import os
from shared.config import Config


def test_mysql_host_default():
    assert Config.MYSQL_HOST == "localhost"


def test_mysql_port_default():
    assert Config.MYSQL_PORT == 3306


def test_mysql_user_default():
    assert Config.MYSQL_USER == "urlshortner"


def test_mysql_password_default():
    assert Config.MYSQL_PASSWORD == "urlshortner"


def test_mysql_db_default():
    assert Config.MYSQL_DB == "urlshortner"


def test_redis_host_default():
    assert Config.REDIS_HOST == "localhost"


def test_redis_port_default():
    assert Config.REDIS_PORT == 6379


def test_redis_db_default():
    assert Config.REDIS_DB == 0


def test_jwt_secret_default(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    import importlib
    import shared.config
    importlib.reload(shared.config)
    from shared.config import Config as FreshConfig
    assert FreshConfig.JWT_SECRET == "super-secret-key-change-in-prod"


def test_jwt_algorithm():
    assert Config.JWT_ALGORITHM == "HS256"


def test_jwt_expire_minutes():
    assert Config.JWT_EXPIRE_MINUTES == 10080


def test_rate_limit_default():
    assert Config.RATE_LIMIT_PER_MINUTE == 30


def test_base_url_default():
    assert Config.BASE_URL == "http://localhost:8000"


def test_url_service_defaults():
    assert Config.URL_SERVICE_HOST == "localhost"
    assert Config.URL_SERVICE_PORT == 8001


def test_auth_service_defaults():
    assert Config.AUTH_SERVICE_HOST == "localhost"
    assert Config.AUTH_SERVICE_PORT == 8002


def test_gateway_port_default():
    assert Config.GATEWAY_PORT == 8000


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("MYSQL_HOST", "db.example.com")
    monkeypatch.setenv("MYSQL_PORT", "3307")
    monkeypatch.setenv("MYSQL_USER", "admin")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("MYSQL_DB", "mydb")
    monkeypatch.setenv("REDIS_HOST", "cache.example.com")
    monkeypatch.setenv("REDIS_PORT", "6380")
    monkeypatch.setenv("REDIS_DB", "1")
    monkeypatch.setenv("JWT_SECRET", "prod-secret")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "10")
    monkeypatch.setenv("BASE_URL", "https://short.example.com")

    # Re-import to pick up new env vars (the module caches class attrs)
    import importlib
    import shared.config
    importlib.reload(shared.config)
    from shared.config import Config as FreshConfig

    assert FreshConfig.MYSQL_HOST == "db.example.com"
    assert FreshConfig.MYSQL_PORT == 3307
    assert FreshConfig.MYSQL_USER == "admin"
    assert FreshConfig.MYSQL_PASSWORD == "secret"
    assert FreshConfig.MYSQL_DB == "mydb"
    assert FreshConfig.REDIS_HOST == "cache.example.com"
    assert FreshConfig.REDIS_PORT == 6380
    assert FreshConfig.REDIS_DB == 1
    assert FreshConfig.JWT_SECRET == "prod-secret"
    assert FreshConfig.RATE_LIMIT_PER_MINUTE == 10
    assert FreshConfig.BASE_URL == "https://short.example.com"
