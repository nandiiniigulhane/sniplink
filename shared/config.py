import os


class Config:
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "urlshortner")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "urlshortner")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "urlshortner")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    URL_SERVICE_HOST: str = os.getenv("URL_SERVICE_HOST", "localhost")
    URL_SERVICE_PORT: int = int(os.getenv("URL_SERVICE_PORT", "8001"))
    AUTH_SERVICE_HOST: str = os.getenv("AUTH_SERVICE_HOST", "localhost")
    AUTH_SERVICE_PORT: int = int(os.getenv("AUTH_SERVICE_PORT", "8002"))
    GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", "8000"))

    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
