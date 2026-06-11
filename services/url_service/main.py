from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import aiomysql
import redis.asyncio as aioredis

from shared.config import Config
from shared.models import ShortenRequest, ShortenResponse
from shared.database import get_pool, init_db
from shared.cache import get_redis
from services.url_service.code_generator import generate_short_code
from services.url_service.url_repository import create_url, get_url, alias_exists

RESERVED_ALIASES = {"health", "api", "auth", "shorten", "login", "register", "favicon.ico", "robots.txt"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="URL Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_db():
    return await get_pool()


async def get_cache():
    return await get_redis()

# Optional user context from gateway header
async def get_optional_user(request: Request) -> dict | None:
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return {"id": int(user_id)}
    return None


@app.post("/api/shorten", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(
    body: ShortenRequest,
    request: Request,
    db_pool: aiomysql.Pool = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_cache),
):
    # If custom alias requested, validate uniqueness
    if body.custom_alias:
        if body.custom_alias in RESERVED_ALIASES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This alias is reserved")
        if await alias_exists(db_pool, body.custom_alias):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Custom alias already taken")
        alias = body.custom_alias
        is_custom = True
    else:
        alias = await generate_short_code(redis_client)
        is_custom = False

    # Get optional user context
    user = await get_optional_user(request)
    user_id = user["id"] if user else None

    result = await create_url(
        db_pool=db_pool,
        redis_client=redis_client,
        alias=alias,
        long_url=str(body.long_url),
        is_custom=is_custom,
        user_id=user_id,
        expires_in_days=body.expires_in_days,
    )

    return ShortenResponse(
        short_url=f"{Config.BASE_URL}/{alias}",
        long_url=result["long_url"],
        alias=result["alias"],
        expires_at=result["expires_at"],
        is_custom=result["is_custom"],
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/{alias}")
async def redirect_url(alias: str, db_pool: aiomysql.Pool = Depends(get_db), redis_client: aioredis.Redis = Depends(get_cache)):
    if alias in RESERVED_ALIASES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found or expired")
    long_url = await get_url(db_pool, redis_client, alias)
    if long_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found or expired")
    return RedirectResponse(url=long_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)
