"""
URL Shortener Business Logic & Base62 Encoding Engine.
"""

from __future__ import annotations
import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from .config import settings
from .database import URLRecord
from .security import SecurityValidator

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(BASE62_ALPHABET)
ALIAS_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")


class ShortenerService:
    @staticmethod
    def encode_base62(num: int, length: int = 6) -> str:
        """Converts an integer to a fixed-length Base62 string."""
        if num == 0:
            return BASE62_ALPHABET[0] * length
        digits = []
        while num > 0:
            digits.append(BASE62_ALPHABET[num % BASE])
            num //= BASE
        result = "".join(reversed(digits))
        if len(result) < length:
            result = result.rjust(length, BASE62_ALPHABET[0])
        return result[:length]

    @classmethod
    def generate_code_from_url(cls, url: str, attempt: int = 0) -> str:
        """Generates a deterministic 6-character Base62 code from a URL with salt probing."""
        salted = f"{url}:{attempt}".encode("utf-8")
        digest = hashlib.sha256(salted).digest()
        # Take first 6 bytes as integer
        num = int.from_bytes(digest[:6], byteorder="big")
        return cls.encode_base62(num, length=settings.short_code_length)

    @classmethod
    def create_short_url(
        cls,
        db: Session,
        original_url: str,
        custom_alias: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> Tuple[Optional[URLRecord], Optional[str]]:
        """
        Creates a new shortened URL with validation, collision resolution, and TTL expiration.
        """
        # 1. Security & format validation
        is_safe, reason = SecurityValidator.validate_url(original_url)
        if not is_safe:
            return None, f"Security rejection: {reason}"

        # 2. Custom alias handling
        if custom_alias:
            alias = custom_alias.strip()
            if not ALIAS_REGEX.match(alias):
                return None, "Invalid custom alias. Must be 3-32 alphanumeric characters, dashes, or underscores."

            existing = db.query(URLRecord).filter(
                (URLRecord.short_code == alias) | (URLRecord.custom_alias == alias)
            ).first()
            if existing:
                return None, f"Alias '{alias}' is already in use."

            short_code = alias
        else:
            # 3. Collision-resistant generation
            short_code = None
            for attempt in range(5):
                candidate = cls.generate_code_from_url(original_url, attempt)
                existing = db.query(URLRecord).filter(URLRecord.short_code == candidate).first()
                if not existing:
                    short_code = candidate
                    break
                elif existing.original_url == original_url and existing.is_active:
                    # Idempotent return of existing active link
                    return existing, None

            if not short_code:
                return None, "Failed to resolve code collision after maximum attempts."

        # 4. TTL expiration calculation
        expires_at = None
        ttl = ttl_seconds if ttl_seconds is not None else settings.default_ttl_seconds
        if ttl > 0:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        record = URLRecord(
            short_code=short_code,
            original_url=original_url,
            custom_alias=custom_alias,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True,
            click_count=0
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record, None

    @classmethod
    def resolve_destination(cls, db: Session, short_code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolves short code to destination URL, checking active status and TTL.
        """
        record = db.query(URLRecord).filter(URLRecord.short_code == short_code).first()
        if not record:
            return None, "Short URL not found."

        if not record.is_active:
            return None, "Short URL has been deactivated."

        if record.expires_at and record.expires_at < datetime.utcnow():
            record.is_active = False
            db.commit()
            return None, "Short URL has expired."

        return record.original_url, None
