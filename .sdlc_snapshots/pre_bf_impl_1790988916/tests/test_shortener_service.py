"""
Unit & Integration Tests for URL Shortener Service.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta

from url_shortener.database import Base, URLRecord
from url_shortener.shortener import ShortenerService
from url_shortener.security import SecurityValidator


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_base62_encoding():
    code_0 = ShortenerService.encode_base62(0, length=6)
    assert code_0 == "000000"

    code_100 = ShortenerService.encode_base62(100, length=6)
    assert len(code_100) == 6
    assert isinstance(code_100, str)


def test_create_short_url_success(test_db):
    record, err = ShortenerService.create_short_url(
        db=test_db,
        original_url="https://www.schwab.com/investment-products",
        custom_alias=None,
        ttl_seconds=3600
    )
    assert err is None
    assert record is not None
    assert len(record.short_code) == 6
    assert record.is_active is True
    assert record.click_count == 0


def test_custom_alias_collision(test_db):
    rec1, err1 = ShortenerService.create_short_url(
        db=test_db,
        original_url="https://www.example.com",
        custom_alias="my-custom-link"
    )
    assert err1 is None
    assert rec1.short_code == "my-custom-link"

    # Attempting duplicate alias must fail
    rec2, err2 = ShortenerService.create_short_url(
        db=test_db,
        original_url="https://www.google.com",
        custom_alias="my-custom-link"
    )
    assert rec2 is None
    assert "already in use" in err2


def test_ssrf_protection_prohibits_private_ips(test_db):
    # Direct loopback IP
    rec1, err1 = ShortenerService.create_short_url(
        db=test_db,
        original_url="http://127.0.0.1:8080/admin"
    )
    assert rec1 is None
    assert "SSRF violation" in err1

    # Private RFC 1918 range
    rec2, err2 = ShortenerService.create_short_url(
        db=test_db,
        original_url="http://192.168.1.100/internal"
    )
    assert rec2 is None
    assert "SSRF violation" in err2


def test_malicious_domain_blocked(test_db):
    rec, err = ShortenerService.create_short_url(
        db=test_db,
        original_url="https://phishing-bank.com/login"
    )
    assert rec is None
    assert "flagged as malicious" in err


def test_ttl_expiration(test_db):
    # Link with negative TTL (already expired)
    record = URLRecord(
        short_code="expired1",
        original_url="https://www.valid.com",
        created_at=datetime.now(timezone.utc) - timedelta(days=2),
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        is_active=True
    )
    test_db.add(record)
    test_db.commit()

    dest, err = ShortenerService.resolve_destination(test_db, "expired1")
    assert dest is None
    assert "expired" in err
