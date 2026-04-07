"""鉴权中间件

本地单用户场景，简单 token 校验。
请求头带 Authorization: Bearer <token> 即可。
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.config import get_settings

# 不需要鉴权的路径
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # WebSocket 升级走 query param
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        settings = get_settings()
        token = self._extract_token(request)

        if token != settings.council_auth_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "未授权，请检查 token"},
            )

        return await call_next(request)

    def _extract_token(self, request: Request) -> str:
        # Header: Authorization: Bearer xxx
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]

        # Query param: ?token=xxx（WebSocket 兼容）
        token = request.query_params.get("token", "")
        if token:
            return token

        return ""
