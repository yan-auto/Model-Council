"""限流中间件

简单的令牌桶限流，本地单用户足够。
"""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60, burst: int = 10):
        super().__init__(app)
        self._rpm = requests_per_minute
        self._burst = burst
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 限流只针对 API 路由
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        client_id = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self._buckets[client_id]

        # 清理过期的记录
        bucket[:] = [t for t in bucket if now - t < 60]

        if len(bucket) >= self._rpm:
            return JSONResponse(
                status_code=429,
                content={"detail": "请求太频繁，请稍后再试"},
            )

        bucket.append(now)
        return await call_next(request)
