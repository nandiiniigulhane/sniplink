import aiomysql
from shared.config import Config

_pool: aiomysql.Pool | None = None


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB,
            minsize=5,
            maxsize=50,
            autocommit=True,
        )
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS urls (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    alias VARCHAR(20) NOT NULL UNIQUE,
                    long_url TEXT NOT NULL,
                    is_custom BOOLEAN DEFAULT FALSE,
                    password_hash VARCHAR(255) NULL,
                    user_id BIGINT NULL,
                    expires_at DATETIME NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_alias (alias),
                    INDEX idx_expires_at (expires_at),
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            # Migration: add password_hash if column doesn't exist on existing tables
            try:
                await cur.execute(
                    "ALTER TABLE urls ADD COLUMN password_hash VARCHAR(255) NULL AFTER is_custom"
                )
            except Exception:
                pass  # Column already exists
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
