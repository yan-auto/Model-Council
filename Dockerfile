# ── 阶段1：构建前端 ──────────────────────────────
FROM node:22-alpine AS frontend-build

WORKDIR /build/web
COPY web/package.json ./
RUN npm install
COPY web/ ./
RUN npm run build

# ── 阶段2：运行时 ────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends sqlite3 && \
    rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# 后端代码
COPY src/ src/
COPY config/ config/

# 前端产物（从阶段1复制）
COPY --from=frontend-build /build/web/dist /app/web/dist

# 数据目录
RUN mkdir -p /app/data/db /app/data/vectors

# 环境变量默认值
ENV COUNCIL_AUTH_TOKEN=council-local
ENV COUNCIL_DATA_DIR=/app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "src.api.main"]
