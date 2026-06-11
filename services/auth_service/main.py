from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import aiomysql

from shared.models import RegisterRequest, LoginRequest, TokenResponse
from shared.database import get_pool, init_db
from services.auth_service.user_repository import create_user, get_user_by_email, verify_password
from services.auth_service.jwt_handler import create_access_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Auth Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_db():
    return await get_pool()


@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db_pool: aiomysql.Pool = Depends(get_db)):
    existing = await get_user_by_email(db_pool, body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await create_user(db_pool, body.email, body.password)
    token = create_access_token(user["id"], user["email"])

    return TokenResponse(access_token=token, email=user["email"])


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, db_pool: aiomysql.Pool = Depends(get_db)):
    user = await get_user_by_email(db_pool, body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user["id"], user["email"])
    return TokenResponse(access_token=token, email=user["email"])


@app.get("/health")
async def health():
    return {"status": "ok"}
