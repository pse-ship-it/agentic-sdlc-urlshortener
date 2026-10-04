"""
FastAPI Main Application Entrypoint for PulseURL.
Includes Lifespan DB bootstrap and Sliding-Window Rate Limiting Middleware.
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routes import router
from .ratelimit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise URL Shortener with Analytics, Sliding-Window Rate Limiting, and SSRF Security.",
    lifespan=lifespan
)

# Enable CORS for the dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health check, docs, and static files
    path = request.url.path
    if path.startswith("/docs") or path.startswith("/openapi.json") or path == "/api/v1/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "127.0.0.1"
    allowed, retry_after = limiter.is_allowed(client_ip)
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please retry in {retry_after} seconds.",
                "retry_after_seconds": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )

    response = await call_next(request)
    return response


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("url_shortener.main:app", host="127.0.0.1", port=8000, reload=True)
