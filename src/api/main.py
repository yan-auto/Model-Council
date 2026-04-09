"""FastAPI 主应用"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config import get_settings
from src.data.database import init_db, close_db
from src.api.middleware.auth import AuthMiddleware
from src.api.middleware.rate_limit import RateLimitMiddleware
from src.api.routes import chat, agents, discussion, providers, profile

logger = logging.getLogger("council")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库，关闭时清理"""
    settings = get_settings()
    logger.info(f"Council v{settings.app.version} 启动中...")
    await init_db()
    logger.info("数据库初始化完成")
    # 种子数据：供应商 + 角色（仅在为空时导入）
    from src.data.seed import seed_initial_data
    await seed_initial_data()
    logger.info("种子数据检查完成")
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

    # 鉴权
    app.add_middleware(AuthMiddleware)

    # 限流
    rl = settings.rate_limit
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rl.requests_per_minute, burst=rl.burst)

    # CORS（最后添加 = 最先执行，确保预检请求不被其他中间件拦截）
    # 仅允许 localhost 和配置中指定的域名，防止 CSRF 攻击
    allowed_origins = settings.cors.allowed_origins if hasattr(settings, 'cors') else [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # 路由
    app.include_router(chat.router)
    app.include_router(agents.router)
    app.include_router(providers.router)
    app.include_router(discussion.router)
    app.include_router(profile.router)

    @app.get("/")
    async def root():
        return {"name": "Council", "version": settings.app.version}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # 前端静态文件（Docker 部署时 web/dist 存在）
    static_dir = settings.app.app_static_dir
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="static-assets")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

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
