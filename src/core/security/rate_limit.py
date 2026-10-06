"""Rate limit de ventana fija con headers estándar IETF (RateLimit-Limit/Remaining/Reset).

`InMemoryRateLimitStore` sirve para una sola instancia; con varias instancias se implementa
`IRateLimitStore` sobre Redis sin cambiar el resto del código.
"""

import asyncio
import math
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_after: int  


class IRateLimitStore(ABC):
    @abstractmethod
    async def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult: ...


class InMemoryRateLimitStore(IRateLimitStore):
    _SWEEP_EVERY_SECONDS = 60

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._buckets: dict[str, tuple[float, int, int]] = {}  
        self._lock = asyncio.Lock()
        self._last_sweep = clock()

    async def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        async with self._lock:
            now = self._clock()
            self._sweep(now)
            start, count, _ = self._buckets.get(key, (now, 0, window_seconds))
            if now - start >= window_seconds:
                start, count = now, 0
            count += 1
            self._buckets[key] = (start, count, window_seconds)
            reset_after = max(1, math.ceil(start + window_seconds - now))
            return RateLimitResult(
                allowed=count <= limit,
                limit=limit,
                remaining=max(0, limit - count),
                reset_after=reset_after,
            )

    def _sweep(self, now: float) -> None:
        if now - self._last_sweep < self._SWEEP_EVERY_SECONDS:
            return
        self._last_sweep = now
        expired = [key for key, (start, _, window) in self._buckets.items() if now - start >= window]
        for key in expired:
            del self._buckets[key]


def rate_limit_headers(result: RateLimitResult) -> dict[str, str]:
    headers = {
        "RateLimit-Limit": str(result.limit),
        "RateLimit-Remaining": str(result.remaining),
        "RateLimit-Reset": str(result.reset_after),
    }
    if not result.allowed:
        headers["Retry-After"] = str(result.reset_after)
    return headers
