"""限流和大小限制中间件

简单的令牌桶限流，本地单用户足够。
防止 DoS 攻击通过超大请求体。
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.config import get_settings

logger = logging.getLogger("council.rate_limit")

# 最大请求体大小：10MB
MAX_REQUEST_SIZE = 10 * 1024 * 1024


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60, burst: int = 10):
        super().__init__(app)
        self._rpm = requests_per_minute
        self._burst = burst
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # CORS 预检请求跳过
        if request.method == "OPTIONS":
            return await call_next(request)

        # 检查请求体大小
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            logger.warning(f"拒绝超大请求体：{content_length} 字节（最大 {MAX_REQUEST_SIZE}）")
            return JSONResponse(
                status_code=413,
                content={"detail": f"请求体过大（最大 {MAX_REQUEST_SIZE // 1024 // 1024} MB）"},
            )

        # 限流只针对 API 路由
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        client_id = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self._buckets[client_id]

        # 清理过期的记录
        bucket[:] = [t for t in bucket if now - t < 60]

        if len(bucket) >= self._rpm:
            logger.warning(f"请求限流触发：{client_id}")
            return JSONResponse(
                status_code=429,
                content={"detail": "请求太频繁，请稍后再试"},
            )

        bucket.append(now)
        return await call_next(request)
