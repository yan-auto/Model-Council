"""FastAPI 主应用"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.data.database import init_db, close_db
from src.api.middleware.auth import AuthMiddleware
from src.api.middleware.rate_limit import RateLimitMiddleware
from src.api.routes import chat, agents, discussion

logger = logging.getLogger("council")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库，关闭时清理"""
    settings = get_settings()
    logger.info(f"Council v{settings.app.version} 启动中...")
    await init_db()
    logger.info("数据库初始化完成")
    yield
    await close_db()
    logger.info("Council 已关闭")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Council",
        description="本地私人 AI 委员会系统",
        version=settings.app.version,
        lifespan=lifespan,
    )

    # CORS（本地开发允许全部）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 鉴权
    app.add_middleware(AuthMiddleware)

    # 限流
    rl = settings.rate_limit
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rl.requests_per_minute, burst=rl.burst)

    # 路由
    app.include_router(chat.router)
    app.include_router(agents.router)
    app.include_router(discussion.router)

    @app.get("/")
    async def root():
        return {"name": "Council", "version": settings.app.version}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()


def cli():
    """命令行入口"""
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.api.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=True,
    )


if __name__ == "__main__":
    cli()
