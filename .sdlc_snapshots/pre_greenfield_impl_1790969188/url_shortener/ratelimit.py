"""
Sliding-Window Token Bucket Rate Limiter.
Protects endpoints against DoS, brute-force scraping, and abusive traffic.
"""

from __future__ import annotations
import time
import threading
from typing import Dict, List, Tuple
from .config import settings


class SlidingWindowRateLimiter:
    def __init__(self, limit_per_window: int = 60, window_seconds: int = 60):
        self.limit = limit_per_window
        self.window = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def is_allowed(self, client_key: str) -> Tuple[bool, int]:
        """
        Evaluates whether a client request is within the sliding window quota.
        Returns: (is_allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        window_start = now - self.window

        with self.lock:
            # Get existing timestamps and purge expired
            timestamps = self.requests.get(client_key, [])
            valid_timestamps = [t for t in timestamps if t > window_start]

            if len(valid_timestamps) >= self.limit:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + self.window - now))
                self.requests[client_key] = valid_timestamps
                return False, retry_after

            valid_timestamps.append(now)
            self.requests[client_key] = valid_timestamps
            return True, 0

    def reset(self, client_key: Optional[str] = None):
        with self.lock:
            if client_key:
                self.requests.pop(client_key, None)
            else:
                self.requests.clear()


limiter = SlidingWindowRateLimiter(
    limit_per_window=settings.rate_limit_per_minute,
    window_seconds=settings.rate_limit_window_seconds
)
