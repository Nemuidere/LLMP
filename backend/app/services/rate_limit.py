"""In-memory sliding-window rate limiter for offset submissions.

Per AGENTS.md §4 we hash the IP rather than store it raw. The limiter
itself is in-process — fine for a single-instance deploy; if we ever run
multiple workers, swap for Redis without changing the call site.
"""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque

from app.config import get_settings


def hash_ip(ip: str) -> str:
    salt = get_settings().ip_hash_salt
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: float) -> None:
        self.max_events = max_events
        self.window = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self._events[key]
        cutoff = now - self.window
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= self.max_events:
            return False
        q.append(now)
        return True


# 5 submissions / 10 minutes per ip-hash. Tuned conservatively; raise
# later if it bites real users.
offset_limiter = SlidingWindowLimiter(max_events=5, window_seconds=600.0)
