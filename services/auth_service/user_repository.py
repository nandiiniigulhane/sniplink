import bcrypt
import aiomysql


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


async def create_user(db_pool: aiomysql.Pool, email: str, password: str) -> dict:
    password_hash = hash_password(password)
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                (email, password_hash),
            )
            user_id = cur.lastrowid
    return {"id": user_id, "email": email}


async def get_user_by_email(db_pool: aiomysql.Pool, email: str) -> dict | None:
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT id, email, password_hash FROM users WHERE email = %s",
                (email,),
            )
            return await cur.fetchone()
