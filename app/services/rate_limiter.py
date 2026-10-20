"""
ScamShield AI — In-Memory Sliding Window Rate Limiter (Item 8)

Provides a lightweight, thread-safe in-memory sliding window rate limiter
to prevent request floods, automated scraping, and denial-of-service attempts
without external Redis dependencies.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Optional, Tuple


@dataclass
class RateLimitWindow:
    timestamps: List[float] = field(default_factory=list)


class SlidingWindowRateLimiter:
    """
    Sliding window in-memory rate limiter per client key (e.g. client IP).
    """

    def __init__(self, requests_per_minute: int = 60, window_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._clients: Dict[str, RateLimitWindow] = defaultdict(RateLimitWindow)
        self._last_cleanup = time.time()

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check if a request from client_ip is allowed under the current window.
        Returns:
            (allowed: bool, retry_after: int)
        """
        now = time.time()
        with self._lock:
            # Periodic background cleanup of stale clients every 5 minutes
            if now - self._last_cleanup > 300:
                self._cleanup_stale(now)
                self._last_cleanup = now

            window = self._clients[client_ip]
            cutoff = now - self.window_seconds

            # Filter out timestamps older than the window
            window.timestamps = [t for t in window.timestamps if t > cutoff]

            if len(window.timestamps) < self.requests_per_minute:
                window.timestamps.append(now)
                return True, 0
            else:
                oldest_in_window = window.timestamps[0]
                retry_after = max(1, int(oldest_in_window + self.window_seconds - now))
                return False, retry_after

    def _cleanup_stale(self, now: float) -> None:
        """Removes client records with no recent activity."""
        cutoff = now - self.window_seconds
        stale_keys = [
            ip for ip, win in self._clients.items()
            if not win.timestamps or win.timestamps[-1] <= cutoff
        ]
        for ip in stale_keys:
            del self._clients[ip]

    def reset(self) -> None:
        """Resets all tracked windows (useful for testing)."""
        with self._lock:
            self._clients.clear()


# Global default rate limiter instance (60 requests/minute)
rate_limiter = SlidingWindowRateLimiter(requests_per_minute=60, window_seconds=60)
