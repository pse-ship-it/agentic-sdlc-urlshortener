"""
Configuration settings for PulseURL Service.
"""

from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "PulseURL Enterprise Shortener"
    base_url: str = os.getenv("PULSEURL_BASE_URL", "http://localhost:8000")
    database_url: str = os.getenv("PULSEURL_DATABASE_URL", "sqlite:///./pulseurl.db")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    rate_limit_window_seconds: int = 60
    default_ttl_seconds: int = int(os.getenv("DEFAULT_TTL_SECONDS", "2592000"))  # 30 days
    short_code_length: int = 6
    enable_ssrf_protection: bool = True
    blocked_domains: list[str] = ["malware.com", "phishing-bank.com", "evil.org", "bad-actor.net"]


settings = Settings()
