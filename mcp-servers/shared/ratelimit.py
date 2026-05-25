"""Per-correlation-id rate limiter.

A sliding-window limiter that caps how many tool calls a single correlation
id may make per minute. This protects the downstream REST services from a
runaway agent loop reusing the same correlation id. The limiter is in-process
and thread/async-safe for a single server instance.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

DEFAULT_MAX_CALLS = 100
DEFAULT_WINDOW_SECONDS = 60.0


class RateLimitExceeded(Exception):
    """Raised when a correlation id exceeds its allotted call budget."""

    def __init__(self, correlation_id: str, max_calls: int, window_seconds: float):
        self.correlation_id = correlation_id
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        super().__init__(
            f"correlation id '{correlation_id}' exceeded {max_calls} "
            f"calls per {int(window_seconds)}s"
        )


class RateLimiter:
    """Sliding-window rate limiter keyed by correlation id."""

    def __init__(
        self,
        max_calls: int = DEFAULT_MAX_CALLS,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
    ) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _now(self) -> float:
        return time.monotonic()

    def check(self, correlation_id: str) -> None:
        """Record a call for ``correlation_id`` or raise ``RateLimitExceeded``.

        Calls older than the window are evicted first. If recording the new
        call would breach the ceiling, the call is rejected and not recorded.
        """
        now = self._now()
        cutoff = now - self.window_seconds
        with self._lock:
            window = self._calls[correlation_id]
            while window and window[0] <= cutoff:
                window.popleft()
            if len(window) >= self.max_calls:
                raise RateLimitExceeded(
                    correlation_id, self.max_calls, self.window_seconds
                )
            window.append(now)

    def reset(self, correlation_id: str | None = None) -> None:
        """Clear recorded calls for one id, or all ids when none is given."""
        with self._lock:
            if correlation_id is None:
                self._calls.clear()
            else:
                self._calls.pop(correlation_id, None)


# Shared limiter instance used by all tool servers in a process.
shared_rate_limiter = RateLimiter()
