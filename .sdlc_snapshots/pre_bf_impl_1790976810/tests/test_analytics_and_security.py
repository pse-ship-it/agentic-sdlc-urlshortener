"""
Tests for Analytics Engine, Sliding-Window Rate Limiting, and Security Guardrails.
"""

import pytest
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from url_shortener.database import Base, URLRecord, ClickEvent
from url_shortener.analytics import AnalyticsService
from url_shortener.ratelimit import SlidingWindowRateLimiter
from url_shortener.security import SecurityValidator


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_ip_anonymization():
    ip1 = "203.0.113.195"
    h1 = SecurityValidator.hash_ip(ip1)
    h2 = SecurityValidator.hash_ip(ip1)
    assert h1 == h2
    assert ip1 not in h1
    assert len(h1) == 16


def test_click_analytics_aggregation(test_db):
    # Setup test URL
    record = URLRecord(
        short_code="xyz123",
        original_url="https://investing.schwab.com",
        is_active=True,
        click_count=0
    )
    test_db.add(record)
    test_db.commit()

    # Record multiple clicks from distinct devices and referrers
    AnalyticsService.record_click(
        test_db, "xyz123", "198.51.100.1",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        referrer="https://t.co/promo"
    )
    AnalyticsService.record_click(
        test_db, "xyz123", "198.51.100.2",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        referrer="https://www.google.com/search?q=schwab"
    )

    analytics = AnalyticsService.get_analytics(test_db, "xyz123")
    assert analytics is not None
    assert analytics["total_clicks"] == 2
    assert analytics["unique_visitors"] == 2
    assert analytics["devices"]["mobile"] == 1
    assert analytics["devices"]["desktop"] == 1
    assert len(analytics["recent_events"]) == 2


def test_sliding_window_rate_limiter():
    limiter = SlidingWindowRateLimiter(limit_per_window=3, window_seconds=2)
    client_ip = "192.0.2.45"

    # First 3 requests must succeed
    assert limiter.is_allowed(client_ip)[0] is True
    assert limiter.is_allowed(client_ip)[0] is True
    assert limiter.is_allowed(client_ip)[0] is True

    # 4th request within window must be rejected with retry-after
    allowed, retry_after = limiter.is_allowed(client_ip)
    assert allowed is False
    assert retry_after >= 1

    # After window expiration, should be allowed again
    time.sleep(2.1)
    allowed_again, _ = limiter.is_allowed(client_ip)
    assert allowed_again is True
