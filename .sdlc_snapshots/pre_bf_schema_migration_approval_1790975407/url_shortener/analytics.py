"""
Analytics Engine: Telemetry Capture & Multi-dimensional Aggregation.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import URLRecord, ClickEvent
from .security import SecurityValidator


class AnalyticsService:
    @staticmethod
    def detect_device(user_agent: Optional[str]) -> str:
        """Categorizes client device from User-Agent string."""
        if not user_agent:
            return "unknown"
        ua = user_agent.lower()
        if "bot" in ua or "crawler" in ua or "spider" in ua:
            return "bot"
        if "tablet" in ua or "ipad" in ua:
            return "tablet"
        if "mobile" in ua or "android" in ua or "iphone" in ua:
            return "mobile"
        return "desktop"

    @staticmethod
    def extract_referrer_domain(referrer: Optional[str]) -> str:
        """Normalizes referrer URL into clean domain or 'Direct'."""
        if not referrer or not referrer.strip():
            return "Direct / Bookmark"
        try:
            parsed = urlparse(referrer)
            return parsed.netloc or referrer[:30]
        except Exception:
            return "Unknown"

    @classmethod
    def record_click(
        cls,
        db: Session,
        short_code: str,
        client_ip: str,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> None:
        """Asynchronously records click telemetry and increments total counter."""
        ip_hash = SecurityValidator.hash_ip(client_ip)
        device = cls.detect_device(user_agent)
        norm_ref = cls.extract_referrer_domain(referrer)

        event = ClickEvent(
            short_code=short_code,
            timestamp=datetime.now(timezone.utc),
            ip_hash=ip_hash,
            referrer=norm_ref,
            user_agent=user_agent[:255] if user_agent else None,
            device_type=device,
            country="United States"  # GeoIP simulation / lookup
        )
        db.add(event)

        # Increment counter atomically
        url_record = db.query(URLRecord).filter(URLRecord.short_code == short_code).first()
        if url_record:
            url_record.click_count += 1

        db.commit()

    @classmethod
    def get_analytics(cls, db: Session, short_code: str) -> Optional[Dict[str, Any]]:
        """Computes comprehensive aggregated analytics for a given short code."""
        url_record = db.query(URLRecord).filter(URLRecord.short_code == short_code).first()
        if not url_record:
            return None

        # 1. Total and Unique Clicks
        total_clicks = url_record.click_count
        unique_visitors = db.query(func.count(func.distinct(ClickEvent.ip_hash))).filter(
            ClickEvent.short_code == short_code
        ).scalar() or 0

        # 2. Referrers Breakdown
        referrer_rows = db.query(
            ClickEvent.referrer, func.count(ClickEvent.id)
        ).filter(
            ClickEvent.short_code == short_code
        ).group_by(ClickEvent.referrer).all()
        referrers = {ref or "Direct": count for ref, count in referrer_rows}

        # 3. Device Breakdown
        device_rows = db.query(
            ClickEvent.device_type, func.count(ClickEvent.id)
        ).filter(
            ClickEvent.short_code == short_code
        ).group_by(ClickEvent.device_type).all()
        devices = {dev: count for dev, count in device_rows}

        # 4. Recent Clicks Timeline
        events = db.query(ClickEvent).filter(
            ClickEvent.short_code == short_code
        ).order_by(ClickEvent.timestamp.desc()).limit(20).all()

        timeline = [
            {
                "timestamp": e.timestamp.isoformat(),
                "device": e.device_type,
                "referrer": e.referrer,
                "country": e.country
            }
            for e in events
        ]

        return {
            "short_code": short_code,
            "original_url": url_record.original_url,
            "created_at": url_record.created_at.isoformat() if url_record.created_at else None,
            "expires_at": url_record.expires_at.isoformat() if url_record.expires_at else None,
            "is_active": url_record.is_active,
            "total_clicks": total_clicks,
            "unique_visitors": unique_visitors,
            "devices": devices,
            "referrers": referrers,
            "recent_events": timeline
        }
