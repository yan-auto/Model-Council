"""鉴权中间件

本地单用户场景，简单 token 校验。
请求头带 Authorization: Bearer <token> 即可。

安全加强：
- 使用恒定时间比较防止 timing attack
- 记录授权失败日志便于审计
- 异常时返回通用错误信息
"""

from __future__ import annotations

import logging
import hmac
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.config import get_settings

logger = logging.getLogger("council.auth")

# 不需要鉴权的路径
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # CORS 预检请求直接放行
        if request.method == "OPTIONS":
            return await call_next(request)

        # 公共路径放行
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        try:
            settings = get_settings()
            token = self._extract_token(request)

            # 使用恒定时间比较，防止 timing attack
            if not self._constant_time_compare(token, settings.council_auth_token):
                logger.warning(f"授权失败：来自 {request.client.host if request.client else 'unknown'} 的请求")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "未授权"},
                )

            return await call_next(request)
        except Exception as e:
            logger.error(f"身份验证异常：{str(e)}", exc_info=True)
            return JSONResponse(
                status_code=401,
                content={"detail": "未授权"},
            )

    def _extract_token(self, request: Request) -> str:
        """从请求中提取 token，支持 header 和 query param"""
        # Header: Authorization: Bearer xxx
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]

        # Query param: ?token=xxx（WebSocket 兼容）
        token = request.query_params.get("token", "")
        if token:
            return token

        return ""

    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """恒定时间比较，防止 timing attack"""
        return hmac.compare_digest(a.encode() if a else b"", b.encode() if b else b"")
