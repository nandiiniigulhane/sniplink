# URL Shortner

A high-performance URL shortening service built for scale — handles **100M daily users** with low-latency redirects, custom aliases, and expiration dates.

> Built with [Command Code](https://commandcode.ai) — the coding agent that learns your style.

## Architecture

```
┌─────────────┐
│   Browser   │  http://localhost:5173
└──────┬──────┘
       │
┌──────▼──────┐
│ API Gateway │  :8000  Rate limiting · JWT extraction · Service routing
└──┬──────┬──┘
   │      │
┌──▼───┐ ┌▼──────┐
│ URL  │ │ Auth  │  :8001 / :8002
│ Svc  │ │ Svc   │
└──┬───┘ └──┬────┘
   │        │
┌──▼──┐ ┌──▼──┐
│Redis│ │MySQL│
└─────┘ └─────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI |
| Frontend | React 19 · TypeScript · Vite |
| Cache | Redis 7 |
| Database | MySQL 8 |
| Auth | JWT (HS256) · bcrypt |
| Container | Docker Compose |

## Quick Start

```bash
# Clone and start everything
docker compose up --build

# Open in browser
open http://localhost:5173
```

That's it. MySQL, Redis, all three backend services, and the frontend boot together.

## API Endpoints

All requests go through the gateway at `:8000`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/shorten` | Create a short URL |
| `GET`  | `/{alias}` | Redirect to long URL (301) |
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Sign in, get JWT |

### Shorten a URL

```bash
curl -X POST http://localhost:8000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "https://example.com/very/long/url",
    "custom_alias": "my-link",
    "expires_in_days": 30
  }'
```

**Response:**
```json
{
  "short_url": "http://localhost:8000/my-link",
  "long_url": "https://example.com/very/long/url",
  "alias": "my-link",
  "expires_at": "2026-07-11T00:00:00",
  "is_custom": true
}
```

No account needed — anonymous shortening works out of the box. Add a `Bearer` token in the `Authorization` header to associate URLs with your account.

## Design Decisions

### ID Generation at 100M DAU
Redis atomic `INCR` counter starting at 62⁵ (≈916M), encoded to Base62. First short code is `100000` (6 characters). The namespace provides:
- **6-character codes**: ~56.8 billion total — ~568 days at 100M URLs/day
- **7-character codes**: ~3.5 trillion total — decades of capacity

No collisions. No extra infra. The counter naturally rolls from 6 to 7 characters as traffic grows.

### Redirect Latency
Write-through caching to Redis on URL creation. Every redirect hits Redis first (sub-millisecond). Cache miss falls back to MySQL, then populates Redis. Expired URLs auto-evict from both Redis (TTL) and MySQL (checked on read).

### Rate Limiting
Sliding window per IP using Redis sorted sets. Default: 30 requests/minute. Configurable via `RATE_LIMIT_PER_MINUTE`.

### Consistency
MySQL's `UNIQUE` constraint on aliases guarantees no duplicates, even with concurrent inserts. Redis counter is atomic (`INCR`), so generated codes are collision-free without coordination.

### SOLID Principles
- **S**: Each service has one responsibility. `shared/` modules each do one thing (config, ID generation, DB, cache, models).
- **O**: Repository pattern — swap storage layer without touching routes.
- **L**: Pydantic models with validation are substitutable in any context.
- **I**: Gateway, URL, and Auth services expose focused interfaces.
- **D**: All services depend on abstract `Config` and interfaces (`get_pool`, `get_redis`), not concrete implementations.

## Project Structure

```
UrlShortner/
├── shared/                     # Cross-service library
│   ├── config.py               # Env-based configuration
│   ├── id_generator.py         # Base62 encoder/decoder
│   ├── database.py             # MySQL pool + schema init
│   ├── cache.py                # Redis client singleton
│   └── models.py               # Pydantic request/response schemas
├── services/
│   ├── api_gateway/            # Rate limiter · JWT extractor · HTTP proxy
│   ├── url_service/            # Shorten · Redirect · Expiration logic
│   └── auth_service/           # Register · Login · JWT generation
├── frontend/                   # React 19 + TypeScript + Vite
├── docker-compose.yml          # MySQL · Redis · 3 backends · frontend
├── Dockerfile                  # Python service image
└── requirements.txt            # Python dependencies
```

## Configuration

Copy `.env` and override as needed:

| Variable | Default | Description |
|---|---|---|
| `MYSQL_HOST` | `localhost` | MySQL host |
| `REDIS_HOST` | `localhost` | Redis host |
| `JWT_SECRET` | `super-secret-key-...` | Change in production |
| `RATE_LIMIT_PER_MINUTE` | `30` | Max shorten requests per IP per minute |
| `BASE_URL` | `http://localhost:8000` | Public-facing base URL for short links |

## Running Locally Without Docker

```bash
# Start MySQL and Redis
brew install mysql redis
brew services start mysql redis

# Create DB
mysql -u root -e "CREATE DATABASE urlshortner; CREATE USER 'urlshortner'@'localhost' IDENTIFIED BY 'urlshortner'; GRANT ALL ON urlshortner.* TO 'urlshortner'@'localhost';"

# Install Python deps
python3.10 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start services (in separate terminals)
PYTHONPATH=. uvicorn services.url_service.main:app --port 8001 --reload
PYTHONPATH=. uvicorn services.auth_service.main:app --port 8002 --reload
PYTHONPATH=. uvicorn services.api_gateway.main:app --port 8000 --reload

# Start frontend
cd frontend && npm install && npm run dev
```

---

Made with [Command Code](https://commandcode.ai) — the AI coding agent that builds like you think.
