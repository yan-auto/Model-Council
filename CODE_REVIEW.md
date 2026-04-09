# Council 项目代码审查和质量检查报告

**审查时间**：2026年4月9日  
**审查范围**：Python 后端 + JavaScript 前端 + 配置文件  
**问题总数**：28个（其中CRITICAL: 6, HIGH: 8, MEDIUM: 9, LOW: 5）

---

## 1. 安全问题 (CRITICAL & HIGH)

### 🔴 CRITICAL: 敏感信息可能泄露到 Docker 镜像

**文件**：[Dockerfile](Dockerfile#L32)  
**问题**：
```dockerfile
ENV COUNCIL_AUTH_TOKEN=council-local  # ❌ 默认 token 硬编码
```
- Docker 镜像中通过 `docker inspect` 可直接读取环境变量
- 所有基于此镜像的容器都共享相同 token，无法隔离
- 生产部署时应该完全依赖运行时注入

**严重性**：**CRITICAL**  
**改进方案**：
```dockerfile
# ❌ 不要硬编码
# ENV COUNCIL_AUTH_TOKEN=council-local

# ✓ 改为
# 1. 依赖 docker-compose.yml 或 k8s secrets 注入
# 2. 或者在启动脚本中从 .env 读取
```

---

### 🔴 CRITICAL: API 密钥存储在数据库明文

**文件**：[models.py](src/data/models.py#L21-L31)、[database.py](src/data/database.py#L60-L77)  
**问题**：
```python
class Provider(BaseModel):
    api_key: str = ""  # ❌ 明文存储在 SQLite
    base_url: str = ""
```

**严重性**：**CRITICAL**  
**风险**：
- 任何数据库备份泄露 = API 密钥全曝露
- SQLite 数据库未加密
- 前端可能通过 API 接口获取这些密钥

**改进方案**：
```python
# 1. 使用加密字段库（cryptography）
from cryptography.fernet import Fernet

class Provider(BaseModel):
    api_key_encrypted: str  # 存储已加密的密钥
    
    def decrypt_api_key(self, master_key: bytes) -> str:
        f = Fernet(master_key)
        return f.decrypt(self.api_key_encrypted.encode()).decode()

# 2. API 端点不要返回 api_key 字段
class ProviderResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    base_url: str
    # ❌ 不要包含 api_key
```

---

### 🔴 CRITICAL: CORS 配置过于宽松

**文件**：[main.py](src/api/main.py#L47-L53)  
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ❌ 允许所有域名
    allow_credentials=True,       # ❌ 允许跨域携带凭证
    allow_methods=["*"],          # ❌ 允许所有 HTTP 方法
    allow_headers=["*"],          # ❌ 允许所有请求头
)
```

**严重性**：**CRITICAL**  
**风险**：
- 任意网站都可以向 Council 发起请求，冒充你的身份
- 中间人攻击风险增加
- 不适合本地单用户场景

**改进方案**：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],  # 只允许前端和同源
    allow_credentials=False,  # 本地场景不需要跨域凭证
    allow_methods=["GET", "POST"],  # 只允许必要的方法
    allow_headers=["Content-Type", "Authorization"],  # 只允许必要的头
)
```

---

### 🔴 CRITICAL: 前端 Token 存储不安全

**文件**：[api.js](web/src/api.js#L5-L7)  
```javascript
function getToken() {
  return localStorage.getItem('council_token') || 'council-local';
}
```

**严重性**：**CRITICAL**  
**问题**：
- `localStorage` 容易被 XSS 攻击读取
- Token 存储没有过期时间
- 没有 HTTPS 保护下的明文传输风险

**改进方案**：
```javascript
// 1. 使用 sessionStorage 而不是 localStorage（关闭浏览器后自动清除）
function getToken() {
  return sessionStorage.getItem('council_token') || 'council-local';
}

// 2. 建议使用 HttpOnly Cookie（不能被 JS 访问）
// 但这需要后端支持，当前架构不适用
```

---

### 🔴 CRITICAL: 身份验证形同虚设

**文件**：[auth.py](src/api/middleware/auth.py)  
**问题**：
```python
if token != settings.council_auth_token:
    return JSONResponse(status_code=401, ...)
```
- 默认 token 是 `"council-local"`（见 config.py、Dockerfile）
- 没有用户隔离，所有请求都用同一个 token
- 适合本地开发，但**不适合网络访问**

**严重性**：**CRITICAL**  
**此刻风险**：如果该项目部署到网络（Docker Hub、服务器等），建议：
```python
# 本地场景可接受，但需要明确标注
class SimpleAuthMiddleware(BaseHTTPMiddleware):
    """仅用于本地开发和单用户场景的简单认证"""
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # 本地场景：跳过认证（供开发使用）
        import os
        if os.getenv("ENVIRONMENT") == "development":
            return await call_next(request)
        
        # 生产场景：强制验证
        token = self._extract_token(request)
        if not token or token != settings.council_auth_token:
            return JSONResponse(status_code=401, ...)
```

---

### 🟠 HIGH: 敏感信息可能在日志中泄露

**文件**：[main.py](src/api/main.py#L20)  
```python
logger.info(f"Council v{settings.app.version} 启动中...")
```

**问题**：
- 没有显式的日志脱敏
- API 密钥可能在错误日志中显示
- HTTP 请求头可能包含 token

**改进方案**：
```python
import logging

class SensitiveDataFilter(logging.Filter):
    """移除日志中的敏感信息"""
    def filter(self, record):
        if hasattr(record, 'msg'):
            # 隐藏 API 密钥
            record.msg = re.sub(r'api_key["\']?\s*[:=]\s*["\']?[^"\'\\s]+', 
                               'api_key=***', str(record.msg))
            # 隐藏 token
            record.msg = re.sub(r'Bearer\s+[^\s]+', 'Bearer ***', record.msg)
        return True

logging.getLogger('council').addFilter(SensitiveDataFilter())
```

---

### 🟠 HIGH: 数据库未配置访问控制

**文件**：[database.py](src/data/database.py#L23-L24)  
```python
_db = await aiosqlite.connect(str(db_path))
# 没有设置文件权限，SQLite 数据库任何进程都可读
```

**改进方案**：
```python
import os
os.chmod(db_path, 0o600)  # 只有所有者可读写
```

---

### 🟠 HIGH: 缺少请求体大小限制

**文件**：[main.py](src/api/main.py) - 没有配置  
**问题**：
- 没有限制 POST/PUT 请求体大小
- 恶意用户可能发送超大文件导致内存溢出

**改进方案**：
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            headers = dict(request.headers)
            if int(headers.get("content-length", 0)) > self.MAX_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"error": "请求体过大"}
                )
        return await call_next(request)

app.add_middleware(MaxBodySizeMiddleware)
```

---

### 🟠 HIGH: SQL 注入风险（虽然用了参数化）

**文件**：所有 repositories（未显示完整）  
**问题**：需要确认所有数据库查询都用了 aiosqlite 的参数化接口

**验证清单**：
- [ ] 所有 `execute()` 调用都使用占位符 `?`
- [ ] 用户输入不直接拼接到 SQL 语句中

---

## 2. 代码质量问题 (MEDIUM & HIGH)

### 🟠 HIGH: 错误处理不完善

**文件**：[chat.py](src/api/routes/chat.py#L85-87)  
```python
try:
    cmd = parse_command(data.content)
except ValueError as e:
    # ❌ 这里没有返回错误响应，代码会继续执行
```

**问题**：
- 异常被捕获后没有处理
- 代码会继续执行，导致未定义行为
- 用户得不到错误提示

**改进方案**：
```python
try:
    cmd = parse_command(data.content)
except ValueError as e:
    return JSONResponse(
        status_code=400,
        content={"error": f"指令解析失败: {str(e)}"}
    )
```

---

### 🟠 HIGH: 缺少类型提示

**文件**：[api.js](web/src/api.js)  
**问题**：
- 所有函数都没有 JSDoc 类型注释
- 参数类型和返回类型不明确
- IDE 无法提供智能补全

**改进方案**：
```javascript
/**
 * 获取应该用的 token
 * @returns {string} 用户 token
 */
function getToken() {
  return localStorage.getItem('council_token') || 'council-local';
}

/**
 * @typedef {Object} ConversationDTO
 * @property {string} id
 * @property {string} title
 * @property {string} status
 * @property {number} updated_at
 */

/**
 * 列出所有对话
 * @param {string} [status] - 过滤状态 'active' | 'archived'
 * @returns {Promise<ConversationDTO[]>}
 */
export async function listConversations(status) {
  // ...
}
```

---

### 🟠 HIGH: 配置加载存在 BUG

**文件**：[config.py](src/config.py#L95-103)  
```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局配置单例"""
    yaml_data = _load_yaml()
    return Settings(**yaml_data)
```

**问题**：
- `_load_yaml()` 每次被调用都重新读取文件，缓存设置无意义
- 环境变量在 `Settings` 初始化时就被读取，不支持热更新
- 如果后期修改 `.env` 文件，必须重启应用

**改进方案**：
```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局配置单例"""
    # 移到 Settings 类内部
    return Settings()

# Settings 类中加载 YAML
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 只在必要时加载 YAML（可选）
        yaml_data = _load_yaml()
        for key, value in yaml_data.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
```

---

### 🟡 MEDIUM: 缺少参数验证

**文件**：[models.py](src/data/models.py#L45-L51)  
```python
class ProviderCreate(BaseModel):
    name: str
    provider_type: ProviderType = ProviderType.OPENAI_COMPATIBLE
    api_key: str
    base_url: str = ""
```

**问题**：
- `name` 可以是空字符串
- `api_key` 可以是空字符串（不符合逻辑）
- `base_url` 没有 URL 格式校验

**改进方案**：
```python
from pydantic import Field, field_validator, HttpUrl

class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider_type: ProviderType = ProviderType.OPENAI_COMPATIBLE
    api_key: str = Field(..., min_length=1)  # 不允许空字符串
    base_url: str = Field(default="", min_length=0)
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('base_url 必须以 http:// 或 https:// 开头')
        return v
```

---

### 🟡 MEDIUM: 缺少异步资源清理

**文件**：[database.py](src/data/database.py#L46)  
```python
async def reset_db() -> None:
    """重置数据库（用于测试）"""
    global _db
    if _db is not None:
        await _db.close()
    import tempfile, os  # ❌ 在函数内动态导入
    # ...
```

**问题**：
- 创建的临时文件未被清理
- 每次测试都产生新的临时数据库，没有回收

**改进方案**：
```python
async def reset_db() -> None:
    """重置数据库（用于测试）"""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
    
    # 使用 tempfile 上下文管理器
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as tmp:
        _db = await aiosqlite.connect(tmp.name)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        await init_db()
```

---

### 🟡 MEDIUM: 前端缺少错误边界

**文件**：[App.jsx](web/src/App.jsx)  
**问题**：
- 没有 Error Boundary 组件
- 一个组件崩溃会导致整个应用白屏
- 没有全局错误处理

**改进方案**：
```javascript
// web/src/components/ErrorBoundary.jsx
import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App crashed:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 text-red-600">
          <h1>应用崩溃了</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>重新加载</button>
        </div>
      );
    }
    return this.props.children;
  }
}

// 在 App.jsx 中使用
export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        {/* ... */}
      </BrowserRouter>
    </ErrorBoundary>
  );
}
```

---

### 🟡 MEDIUM: 缺少输入长度限制

**文件**：[models.py](src/data/models.py#L117-L122)  
```python
class MessageCreate(BaseModel):
    conversation_id: str
    content: str  # ❌ 没有最大长度限制
```

**问题**：
- 用户可以发送任意大小的消息
- 可能导致 LLM API 超额费用
- 数据库存储空间浪费

**改进方案**：
```python
class MessageCreate(BaseModel):
    conversation_id: str
    content: str = Field(..., min_length=1, max_length=8000)  # 限制在 8000 字符
    image_data: str | None = Field(None, max_length=1000000)  # 1MB base64 限制
```

---

## 3. 项目结构和配置问题

### 🟡 MEDIUM: .gitignore 遗漏了关键文件

**文件**：[.gitignore](.gitignore)  
**当前内容**：
```gitignore
.env          # ✓ 好
data/db/*.db  # ✓ 好
.venv/        # ✓ 好
```

**缺失项**：
```gitignore
# 应该加入
*.pyc           # Python 编译文件（已有 __pycache__）
.DS_Store       # macOS（已有）

# 安全敏感文件
.env.local      # 本地覆盖环境变量
.env.*.local    # 各环境的本地覆盖

# IDE 设置（私人配置）
.vscode/settings.json
.idea/
*.swp
*.swo

# 生成文件
*.egg-info/     # （已有）
build/
dist/

# 前端特定
web/.env.local
web/.env.*.local
```

---

### 🟡 MEDIUM: package.json 依赖版本太宽松

**文件**：[web/package.json](web/package.json)  
```json
{
  "lucide-react": "^1.7.0",      // 允许 1.99.99
  "react": "^19.2.4",             // 允许 19.99.99
  "react-router-dom": "^7.14.0"   // 允许 7.99.99
}
```

**问题**：
- 使用 `^` 允许小版本和补丁版本变化
- 可能导致 CI/CD 在不同时间安装不同的版本
- 大版本变化时可能出现兼容性问题

**改进方案**：
```json
{
  "lucide-react": "~1.7.0",      // 只允许补丁版本变化 (1.7.x)
  "react": "~19.2.4",             // 或者使用固定版本
  "react-router-dom": "7.14.0"    // 完全固定版本用于关键依赖
}

// 或者分别管理
"dependencies": {
  "lucide-react": "1.7.0",        // 完全固定
  "react": "19.2.4"
},
"devDependencies": {
  "vite": "8.0.4",                // 开发工具用固定版本
  "eslint": "9.39.4"
}
```

---

### 🟡 MEDIUM: Docker 多阶段构建可优化

**文件**：[Dockerfile](Dockerfile)  
**当前问题**：
- 前端构建在 node:22-alpine，Node 22 可能较新
- Python 基础镜像（3.11-slim）合理
- 没有健康检查的依赖检验

**改进方案**：
```dockerfile
# ── 阶段1：构建前端 ──────────────────────────────
FROM node:20-alpine AS frontend-build
# node:22 最新但可能不稳定，用 node:20 平衡

WORKDIR /build/web
COPY web/package*.json ./  # 同时复制 package-lock.json
RUN npm ci --omit=dev     # 用 ci 代替 install 确保一致性
COPY web/ ./
RUN npm run build

# ── 阶段2：运行时 ────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends sqlite3 && \
    rm -rf /var/lib/apt/lists/*

# Python 依赖（分开 setup 和 code 便于缓存）
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# 后端代码
COPY src/ src/
COPY config/ config/

# 前端产物
COPY --from=frontend-build /build/web/dist /app/web/dist

# 数据目录
RUN mkdir -p /app/data/db /app/data/vectors && \
    chmod 700 /app/data/db  # 只有 owner 可访问

# 环境变量（不要硬编码敏感值）
# ENV COUNCIL_AUTH_TOKEN=council-local  ❌ 删除这行

# 标记为本地开发镜像
LABEL dev.council="local-development"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "src.api.main"]
```

---

### 🟡 MEDIUM: docker-compose 配置可优化

**文件**：[docker-compose.yml](docker-compose.yml)  
**改进**：
```yaml
version: '3.8'

services:
  council:
    build: .
    container_name: council
    ports:
      - "${COUNCIL_PORT:-8000}:8000"  # 可配置端口
    volumes:
      - council-data:/app/data
      - ./config:/app/config:ro      # 只读挂载正确
    environment:
      - COUNCIL_AUTH_TOKEN=${COUNCIL_AUTH_TOKEN}  # 从 .env 读取，不要硬编码
      - COUNCIL_ENV=${COUNCIL_ENV:-development}   # 标记环境
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    env_file:
      - .env
    restart: unless-stopped
    # 添加资源限制
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1024M
        reservations:
          cpus: '1'
          memory: 512M
    # 改进健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      start_period: 10s
      retries: 3
    # 添加日志配置
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  council-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data  # 显式指定本地路径
```

---

## 4. 文档和注释问题

### 🟡 MEDIUM: README 不完整

**文件**：[README.md](README.md)  
**缺失内容**：
- [ ] 系统架构图（整体设计说明）
- [ ] API 文档位置或链接
- [ ] 环境变量完整列表
- [ ] 常见问题 (FAQ) 部分
- [ ] 性能和扩展性说明
- [ ] 许可协议说明（LICENSE 文件存在但 README 没提）
- [ ] 贡献者指南链接

**改进**：
```markdown
# Council - 本地私人 AI 委员会系统

...

## 系统架构

```
┌─────────────┐
│  前端       │ (React + Vite)
└──────┬──────┘
       │ HTTP/SSE
┌──────▼──────────────────┐
│  FastAPI 后端           │
│  ├─ Auth 中间件         │
│  ├─ Rate Limit 中间件   │
│  └─ API 路由            │
└──────┬──────────────────┘
       │
┌──────▼──────────────────┐
│  Core Engine            │
│  ├─ Agent Router        │
│  ├─ Command Parser      │
│  ├─ Context Builder     │
│  └─ Orchestrator        │
└──────┬──────────────────┘
       │
┌──────▼──────────────────┐
│  Services               │
│  ├─ Memory Service      │
│  ├─ Model Router        │
│  └─ ...                 │
└──────┬──────────────────┘
       │
┌──────▼──────────────────┐
│  SQLite + ChromaDB      │
└─────────────────────────┘
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | (无) | OpenAI API 密钥 |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI 基础 URL |
| `COUNCIL_AUTH_TOKEN` | `council-local` | 本地认证 token（开发用） |
| `COUNCIL_DATA_DIR` | `./data` | 数据存储目录 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `COUNCIL_ENV` | `development` | 运行环境 |

## API 文档

API 文档位于 `/docs` (Swagger UI) 或 `/redoc` (ReDoc)

### 主要端点

- `POST /api/chat` - 发送消息
- `GET /api/conversations` - 列出对话
- `POST /api/agents` - 管理角色
- ...

## FAQ

**Q: 如何添加自定义角色？**  
A: 见 [CONTRIBUTING.md](CONTRIBUTING.md)

**Q: 如何使用其他 LLM 供应商？**  
A: 在 Web UI 中添加 Provider，或在 `config/agents/*.yaml` 中配置

## 许可证

MIT License - 见 [LICENSE](LICENSE)
```

---

### 🟡 MEDIUM: CONTRIBUTING.md 不完整

**文件**：[CONTRIBUTING.md](CONTRIBUTING.md)  
**问题**：
- 缺少开发环境设置步骤
- 代码规范部分太简洁
- 没有提交前检查清单
- 没有 Pull Request 模板

**改进**：
```markdown
# 贡献指南

感谢你对 Council 的关注！

## 开发环境设置

### 后端

```bash
# 1. 克隆仓库
git clone https://github.com/username/council.git
cd council

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖（包含开发工具）
pip install -e ".[dev]"

# 4. 验证安装
pytest tests/
```

### 前端

```bash
cd web
npm install
npm run dev  # 启动开发服务器
```

## 代码规范

### Python

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- 必须有类型提示 (`from __future__ import annotations`)
- 文件最大行数 800，函数最大 50 行
- 所有公共函数必须有 docstring

检查命令：
```bash
# 格式化
black src/

# 类型检查
mypy src/

# Linting
flake8 src/
```

### JavaScript/React

- 遵循 ESLint 配置
- 组件必须使用函数式组件和 hooks
- 必须有 PropTypes 或 TypeScript 注释

检查命令：
```bash
cd web
npm run lint  # 运行 ESLint
```

## 提交前检查清单

- [ ] 编写了测试 (覆盖率 >= 80%)
- [ ] 所有测试通过 (`pytest tests/`)
- [ ] 代码通过 linting (`make lint`)
- [ ] 更新了相关文档
- [ ] 提交信息遵循 Conventional Commits 格式

## Pull Request 模板

见 [.github/pull_request_template.md](.github/pull_request_template.md)
```

---

### 🟢 LOW: 代码注释可更详细

**文件**：多个文件  
**例如**：[context_builder.py](src/core/context_builder.py#L1-L10)  
```python
"""Context Builder —— 上下文构建器

把 system prompt + 用户档案 + 角色记忆 + 待办 + 历史摘要 + 对话历史
拼成 LLM 可用的 messages。
"""
```

这个注释很好，但函数内部缺少更多说明。建议：
```python
async def build_messages(
    agent_name: str,
    history: list[Message],
    *,
    extra_system: str = "",
) -> list[ChatMessage]:
    """
    构建发给 LLM 的完整消息列表。
    
    消息构成顺序（重要！）：
    1. system prompt（角色设定）
    2. extra_system（投票等额外指令）
    3. 用户档案（profile）
    4. 角色记忆（agent memory）
    5. 待办承诺（pending actions）
    6. 相关历史摘要（relevant summaries）
    7. 当前对话历史（conversation history）
    
    参数:
        agent_name: 角色名称
        history: 对话历史消息列表
        extra_system: 额外的 system 指令（可选）
    
    返回:
        准备发送给 LLM 的完整消息列表
    
    示例:
        >>> messages = await build_messages('strategist', history)
        >>> len(messages) > 1  # 至少有 system + 历史
    """
```

---

## 5. 依赖和版本管理问题

### 🟢 LOW: pyproject.toml 版本范围合理

**文件**：[pyproject.toml](pyproject.toml)  
**现状**：
- `fastapi>=0.115.0` ✓ 合理（最小版本约束）
- `python-dotenv>=1.0.0` ✓ 合理
- 总体来说依赖版本设置是保守的

**建议**：
- 可考虑添加上限版本 (`<0.116.0`)，但当前的做法更灵活

---

## 6. YAML 配置文件问题

### 🟢 LOW: agent YAML 文件完整且规范

**文件**：[config/agents/*.yaml](config/agents)  
**评价**：
- [strategist.yaml](config/agents/strategist.yaml) 很详细，包含完整 system prompt ✓
- [perspectivist.yaml](config/agents/perspectivist.yaml) 同样完整 ✓
- 格式规范，注释充分 ✓

---

## 7. 测试覆盖问题

### 🟢 LOW: 有基本测试框架

**文件**：[pyproject.toml](pyproject.toml#L16-L20)  
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**现状**：
- 安装了 pytest、pytest-asyncio
- 有 conftest.py 和基本的 fixtures

**建议**：
- [ ] 添加覆盖率目标（当前未见 pytest-cov 配置）
- [ ] 添加 pre-commit hooks 检查测试覆盖
- [ ] 为关键路径补充 E2E 测试

---

## 优先级改进清单

### 🔴 立即修复（本周内）

1. **API 密钥加密** (models.py) - 数据库明文存储密钥是绝对不能接受的
2. **CORS 配置** (main.py) - 当前设置存在安全漏洞
3. **Dockerfile 密钥硬编码** - 删除 ENV COUNCIL_AUTH_TOKEN 行
4. **前端 Token 存储** - 改用 sessionStorage
5. **错误处理** (chat.py) - 异常需要返回响应，否则代码会继续执行

### 🟠 本周修复（HIGH）

6. 日志脱敏 - 防止敏感信息泄露
7. 数据库权限设置 - SQLite 文件权限控制
8. 请求体大小限制 - 防止 DoS
9. 参数验证 - 加强 API 输入检查
10. 前端错误边界 - 提升用户体验

### 🟡 计划内修复（MEDIUM - 下周）

11. 配置加载 bug 修复
12. .gitignore 补全
13. README 补充文档
14. CONTRIBUTING 完善
15. package.json 版本锁定
16. Docker 优化

### 🟢 可选优化（LOW - 持续改进）

17. 代码注释细化
18. 添加 API 文档（Swagger）
19. 性能监控日志
20. 更详细的错误提示

---

## 总体评分

| 维度 | 评分 | 说明 |
|------|------|------|
| **安全性** | 🔴 4/10 | 关键的加密和认证问题需要修复 |
| **代码质量** | 🟠 6/10 | 类型提示和错误处理需改进 |
| **项目结构** | 🟡 7/10 | 整体组织合理，部分配置需优化 |
| **文档** | 🟡 6/10 | README 和 CONTRIBUTING 不够完整 |
| **测试** | 🟡 6/10 | 有基础但覆盖率需提升 |
| **依赖管理** | 🟢 8/10 | 版本设置合理，package.json 可更严格 |

**综合评分**：6.2/10 (可用但需改进，特别是安全性)

---

## 附录：快速修复脚本

### Python 依赖审计
```bash
# 查找过期依赖
pip list --outdated

# 检查安全漏洞
pip install safety
safety check

# 生成 requirements.txt（如需要）
pip freeze > requirements.txt
```

### JavaScript 依赖审计
```bash
cd web

# 检查安全漏洞
npm audit

# 自动修复
npm audit fix

# 检查过期依赖
npm outdated
```

### 本地测试清单
```bash
# 后端
pytest tests/ --cov=src --cov-report=term-missing

# 前端
cd web
npm run lint
npm run build

# 整体
docker-compose up  # 确保 Docker 构建成功
```

---

**报告生成时间**：2026-04-09  
**审查者**：GitHub Copilot  
**下一次审查**：修复所有 CRITICAL 问题后
