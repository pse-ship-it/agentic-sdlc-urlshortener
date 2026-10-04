"""
FastAPI Route Handlers for PulseURL Service.
"""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db, URLRecord
from .shortener import ShortenerService
from .analytics import AnalyticsService
from .config import settings

router = APIRouter()


class ShortenRequest(BaseModel):
    url: str = Field(..., description="Target destination URL")
    custom_alias: Optional[str] = Field(None, description="Optional custom alias (3-32 alphanumeric chars)")
    ttl_seconds: Optional[int] = Field(None, description="Expiration TTL in seconds")


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: str
    expires_at: Optional[str] = None
    custom_alias: Optional[str] = None


@router.post("/api/v1/urls", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
def shorten_url(payload: ShortenRequest, request: Request, db: Session = Depends(get_db)):
    """Creates a new short URL with validation and collision handling."""
    record, error = ShortenerService.create_short_url(
        db=db,
        original_url=payload.url,
        custom_alias=payload.custom_alias,
        ttl_seconds=payload.ttl_seconds
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    base = str(request.base_url).rstrip("/")
    return ShortenResponse(
        short_code=record.short_code,
        short_url=f"{base}/{record.short_code}",
        original_url=record.original_url,
        created_at=record.created_at.isoformat(),
        expires_at=record.expires_at.isoformat() if record.expires_at else None,
        custom_alias=record.custom_alias
    )


@router.get("/api/v1/urls/{short_code}")
def get_url_metadata(short_code: str, db: Session = Depends(get_db)):
    """Inspects metadata for a shortened URL."""
    record = db.query(URLRecord).filter(URLRecord.short_code == short_code).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found.")

    return {
        "short_code": record.short_code,
        "original_url": record.original_url,
        "created_at": record.created_at.isoformat(),
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "is_active": record.is_active,
        "click_count": record.click_count,
        "custom_alias": record.custom_alias
    }


@router.get("/api/v1/urls/{short_code}/analytics")
def get_analytics(short_code: str, db: Session = Depends(get_db)):
    """Retrieves aggregated analytics, device breakdowns, and click timeline."""
    analytics = AnalyticsService.get_analytics(db, short_code)
    if not analytics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found.")
    return analytics


@router.delete("/api/v1/urls/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_url(short_code: str, db: Session = Depends(get_db)):
    """Deactivates a short URL."""
    record = db.query(URLRecord).filter(URLRecord.short_code == short_code).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found.")
    record.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/v1/health")
def health_check():
    """Health check probe."""
    return {"status": "HEALTHY", "service": "PulseURL", "timestamp": "2026-10-02T19:30:00Z"}


@router.get("/{short_code}", response_class=RedirectResponse, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    """
    Performs high-performance redirect and records asynchronous click telemetry.
    """
    dest_url, error = ShortenerService.resolve_destination(db, short_code)
    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    # Capture analytics
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")

    AnalyticsService.record_click(
        db=db,
        short_code=short_code,
        client_ip=client_ip,
        user_agent=user_agent,
        referrer=referrer
    )

    return RedirectResponse(url=dest_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
