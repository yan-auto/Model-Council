# Council

A local, privacy-first multi-agent AI council system for personal decision-making and brainstorming.

Have conversations with multiple AI personas, leverage persistent memory, and enable dynamic discussions—all while keeping your data local.

**Features:** Multi-agent collaboration | Persistent memory across sessions | Real-time streaming | Pluggable LLM providers | WebSocket discussions | 100% local storage

---

## 🎯 Core Features

### Multi-Agent Collaboration
- **4 Built-in Personas**: Strategist, Perspectivist, Supervisor, Social Coach
- **Custom Personas**: Define your own with YAML templates
- **Routing**: Direct messages to specific agents or broadcast to all (`@strategist`, `@all`)
- **Role Awareness**: Each agent remembers you across conversations

### Persistent Memory System
- **User Profile**: Personal background, goals, constraints
- **Cross-conversation Summaries**: Remember context from previous talks
- **Agent Memory**: Each persona tracks relevant facts about you
- **Action Tracking**: Commitments and followups persisted in database

### Discussion Mode
- **Multi-turn Discussions**: Agents take turns, build on each other
- **Consensus Detection**: Automatic agreement discovery
- **Voting System**: Structured decision-making
- **WebSocket Support**: Real-time discussion updates

### Real-Time Streaming
- **SSE Integration**: See AI responses token-by-token
- **No Buffering**: Results appear as they're generated
- **Graceful Fallback**: Works even if streaming fails

### Provider Agnostic
- **OpenAI Compatible**: Any OpenAI-compatible endpoint
- **Native Support**: Anthropic, DeepSeek, MiniMax
- **Mix & Match**: Different models for different agents
- **Easy Swapping**: Switch providers via UI

### Privacy First
- **100% Local Data**: SQLite database on your machine
- **No Cloud Sync**: Your conversations stay yours
- **Disconnect Anytime**: Close the app, take your data
- **Encrypted Credentials**: API keys encrypted at rest

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/yan-auto/Model-Council.git
cd Model-Council

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# (OpenAI API key, Anthropic API key, etc.)

# Start the system
docker-compose up -d

# Open http://localhost:8000
```

### Option 2: Manual Setup

**Backend:**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env with your API credentials

python -m src.api.main
```

**Frontend:**
```bash
cd web
npm install
npm run build
```

Then visit `http://localhost:8000`

### Option 3: Development Mode

**Terminal 1 - Backend (with hot reload):**
```bash
python -m src.api.main
```

**Terminal 2 - Frontend (with hot reload):**
```bash
cd web && npm run dev
# Frontend at http://localhost:5173
```

---

## 📋 Requirements

- **Python**: 3.11+
- **Node.js**: 18+
- **Docker** (optional, if using Docker Compose)
- **API Keys** (at least one):
  - OpenAI API key, OR
  - Anthropic API key, OR
  - Other compatible provider (DeepSeek, MiniMax, etc.)

---

## 🤖 Built-in Personas

| Persona | Name | Role | Best For |
|---------|------|------|----------|
| 🎯 **Strategist** | `strategist` | Career & business decisions | Job offers, side projects, strategy calls |
| 🔍 **Perspectivist** | `perspectivist` | News analysis & big picture | Understanding headlines, social trends |
| 📌 **Supervisor** | `supervisor` | Action tracking & accountability | Weekly reviews, progress checks |
| 💬 **Social Coach** | `social_coach` | Social & relationship advice | Communication, networking, relationships |

Each persona is **aware of your profile** and remembers details across conversations.

---

## 💬 Usage Guide

### Basic Chat

Simply type a message and press Enter. The default persona will respond.

### Mention Specific Personas

Route your message to a specific persona:

```
@strategist Should I take this job offer?
@perspectivist What does the latest news about AI mean?
@social_coach How should I handle this conflict with my colleague?
@all What do you all think about this?
```

### Commands

| Command | Effect |
|---------|--------|
| `/list` | Show all available personas |
| `/add <name>` | Add a persona to current conversation |
| `/remove <name>` | Remove a persona from current conversation |
| `/discuss <topic>` | Start a multi-agent discussion |
| `/stop` | Stop current discussion |
| `/memory` | View memory status for this conversation |
| `/save` | Manually save conversation summary to memory |
| `/model <persona> <model>` | Assign a specific model to a persona |

### Discussion Mode

Start a structured discussion with multiple personas:

```
/discuss Should I switch to freelancing full-time?
```

Personas will:
1. Each give their perspective
2. Build on each other's points
3. Reach toward consensus
4. Present final recommendation

---

## 🏗️ Architecture

```
Council/
├── src/
│   ├── api/              # FastAPI server
│   │   ├── routes/       # REST endpoints
│   │   └── middleware/   # Auth, rate limiting
│   ├── core/             # Agent orchestration
│   │   ├── agent_loader.py  # Load personas from YAML
│   │   ├── agent_router.py  # Route messages to agents
│   │   ├── orchestrator.py   # Discussion coordinator
│   │   └── event_bus.py      # Event pub/sub
│   ├── services/         # Business logic
│   │   ├── memory_service.py     # Cross-conversation memory
│   │   └── model_router.py       # LLM provider selection
│   ├── adapters/         # LLM provider integrations
│   │   ├── openai_adapter.py
│   │   └── anthropic_adapter.py
│   ├── data/             # Database & persistence
│   │   ├── database.py
│   │   ├── models.py     # Pydantic schemas
│   │   └── repositories/ # Data access layer
│   └── security/         # Encryption & secrets
├── config/
│   └── agents/           # YAML persona definitions
├── web/                  # React frontend
│   ├── src/
│   │   ├── pages/        # Page components
│   │   ├── components/   # Reusable UI
│   │   └── api.js        # Backend client
│   └── vite.config.js
├── data/
│   ├── db/               # SQLite databases
│   └── vectors/          # ChromaDB memory
├── tests/
└── docker-compose.yml
```

---

## 🔧 Configuration

### Environment Variables

Create/edit `.env`:

```env
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Auth (for this local instance)
COUNCIL_AUTH_TOKEN=council-local

# Server
COUNCIL_HOST=localhost
COUNCIL_PORT=8000

# Data directory
COUNCIL_DATA_DIR=./data

# Encryption (optional, for production)
COUNCIL_ENCRYPTION_KEY=<fernet-key>
```

### Custom Personas

Add your own persona by creating a YAML file in `config/agents/`:

```yaml
# config/agents/mentor.yaml
name: Mentor
description: A wise career counselor with 20 years of experience

personality:
  tone: wise and encouraging
  traits:
    - patient
    - strategic
    - empathetic
  constraints: "Always ask clarifying questions before giving advice"

system_prompt: |
  You are an experienced career mentor. Your role is to help people make
  informed decisions about their career path. You remember details from
  previous conversations about the user's situation.
```

Restart the server. The new persona will appear in `/list`.

---

## 🔐 Security

### Authentication
- **Local by default**: Simple token validation for localhost
- **Production deployment**: Use strong `COUNCIL_AUTH_TOKEN` and secure CORS
- **Timing attack prevention**: Constant-time token comparison

### Data Privacy
- **No cloud storage**: Your conversations stay on your machine
- **Encrypted credentials**: API keys encrypted at rest using Fernet
- **CORS restricted**: Only localhost allowed by default
- **Session storage**: Frontend tokens in sessionStorage (auto-cleared on browser close)

### Best Practices
- Store API keys in `.env`, never commit to git
- Use unique, strong `COUNCIL_AUTH_TOKEN` in production
- Enable `COUNCIL_ENCRYPTION_KEY` before deploying to production
- Monitor logs for unauthorized access attempts

---

## 📦 Installation from Source

### Prerequisites
- Python 3.11+
- Node.js 18+
- pip and npm

### Steps

```bash
# Clone
git clone https://github.com/yan-auto/Model-Council.git
cd Model-Council

# Backend setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend setup
cd web
npm install
npm run build
cd ..

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python -m src.api.main
# Visit http://localhost:8000
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src tests/

# Watch mode (requires pytest-watch)
ptw
```

---

## 📚 API Endpoints

### Chat
- `POST /api/conversations` — Create new conversation
- `GET /api/conversations` — List conversations
- `GET /api/conversations/{id}` — Get conversation + messages
- `POST /api/chat` — Send message (SSE stream)
- `DELETE /api/conversations/{id}` — Archive conversation

### Agents
- `GET /api/agents` — List available personas
- `GET /api/agents/{name}` — Get persona details

### Providers
- `GET /api/providers` — List configured LLM providers
- `POST /api/providers` — Add new provider
- `PUT /api/providers/{id}` — Update provider
- `DELETE /api/providers/{id}` — Remove provider

### Discussion
- `WS /ws/discuss` — WebSocket for real-time discussions

### Utilities
- `GET /health` — Health check
- `GET /` — Server info

---

## 🐳 Docker Deployment

### Single Container
```bash
docker build -t council:latest .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e COUNCIL_AUTH_TOKEN=<secure-token> \
  -v council_data:/app/data \
  council:latest
```

### Docker Compose (Recommended)
```bash
docker-compose up -d
# Includes: Council service, volume mounts, health checks
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style (PEP 8 for Python, ESLint for JS)
- Testing requirements
- Pull request process
- Security considerations

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙋 Support & Feedback

- **Issues**: [GitHub Issues](https://github.com/yan-auto/Model-Council/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yan-auto/Model-Council/discussions)

---

**Made for people who want to think better, faster, and with multiple perspectives.**
# Council

本地私人 AI 委员会系统。多角色、有记忆、能讨论。

## 核心特性

- **多角色协作**：内置军师（职业决策）、透视（新闻分析）、监工（行动跟踪）、读心（社交建议），支持自定义角色
- **持久记忆**：用户档案 + 跨对话摘要 + 角色记忆 + 待办承诺，角色认识你是谁
- **讨论模式**：多角色轮流发言、投票决策、共识检测
- **流式输出**：SSE 实时推送，边想边说
- **供应商解耦**：支持 OpenAI / Anthropic / DeepSeek / MiniMax，任意组合
- **本地优先**：数据全在本地 SQLite，关闭即走

## 快速开始

### 方式一：Docker（推荐）

```bash
git clone https://github.com/yourname/council.git
cd council

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 一键启动
docker-compose up -d

# 访问 http://localhost:8000
```

### 方式二：手动安装

```bash
# 1. 后端
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 2. 前端
cd web && npm install && npm run build && cd ..

# 3. 配置
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 4. 启动
python -m src.api.main
# 访问 http://localhost:8000
```

### 开发模式

```bash
# 终端 1 - 后端（热重载）
python -m src.api.main

# 终端 2 - 前端（热重载）
cd web && npm run dev
# 前端访问 http://localhost:5173
```

## 四大角色

| 角色 | 英文名 | 职责 |
|------|--------|------|
| 军师 | strategist | 职业决策、接单评估、项目推进 |
| 透视 | perspectivist | 新闻解读、阶级分析、媒体素养 |
| 监工 | supervisor | 周复盘、行动跟踪、模式检测、问责 |
| 读心 | social_coach | 社交认知、关系维护、沟通建议 |

每个角色都注入你的个人档案和历史记忆，知道你是谁、在做什么。

## 使用指南

### 基本对话

直��输入消息，按 Enter 发送。

### @ 提及角色

- `@strategist 我想创业` → 路由到军师
- `@perspectivist 这条新闻说明了什么` → 路由到透视
- `@all 大家怎么看` → 所有活跃角色依次回复

### 指令

| 指令 | 功能 |
|------|------|
| `/discuss <话题>` | 开启讨论模式 |
| `/stop` | 停止当前讨论 |
| `/add <角色>` | 添加角色到当前对话 |
| `/remove <角色>` | 移除角色 |
| `/list` | 列出所有可用角色 |
| `/model <角色> <模型>` | 给指定角色换模型 |
| `/memory` | 查看记忆状态 |
| `/save` | 手动保存当前对话记忆 |

### 讨论模式

1. 输入 `/discuss <话题>` 或点击侧边栏"讨论模式"
2. 选择参与角色（至少 2 个）
3. 等待角色轮流发言
4. 最后一轮自动进入投票，查看多数意见

### 记忆系统

Council 的记忆系统让你的 AI 角色越用越了解你：

- **用户档案**：在设置面板填写姓名、背景、目标、约束
- **角色记忆**：每个角色独立记住关于你的信息
- **对话摘要**：每次对话自动提取关键决策和行动项
- **待办承诺**：自动检测对话中的行动项，跨对话跟踪

## 添加新角色

在 `config/agents/` 下新建 YAML 文件：

```yaml
name: analyst
description: "数据分析员，擅长数字和趋势"

personality:
  tone: "客观、精确、严谨"
  traits: ["分析", "数据", "趋势"]
  constraints: "每个结论必须有数据支撑"

system_prompt: |
  你是一个数据分析专家...
```

## 添加新模型供应商

在设置面板中添加供应商（支持 OpenAI 兼容、Anthropic、MiniMax）。

或通过 API：

```bash
curl -X POST http://localhost:8000/api/providers \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的供应商",
    "provider_type": "openai_compatible",
    "api_key": "your-key",
    "base_url": "https://api.example.com/v1"
  }'
```

## 技术架构

```
Client          React Web UI · SSE流式 · WebSocket实时讨论
API Gateway     FastAPI · 鉴权 · 限流 · Command Parser
Core Engine     Agent Router · Orchestrator · Context Builder · Event Bus
Services        Memory · Model路由
Data            SQLite · 仓储模式
Adapters        OpenAI · Anthropic · DeepSeek · MiniMax
Plugin System   角色插件(YAML) · 工具插件 · 记忆策略插件
```

## 数据库备份

```bash
# 手动备份
python -m src.data.backup

# 列出备份
python -m src.data.backup list

# 从备份恢复
python -m src.data.backup restore council_20260408_030000.db
```

备份默认保留最近 7 份，可用 crontab 或 Windows 计划任务设置定时备份。

## 配置说明

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `OPENAI_BASE_URL` | OpenAI 基础 URL | `https://api.openai.com/v1` |
| `ANTHROPIC_API_KEY` | Anthropic API Key | - |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `DEEPSEEK_BASE_URL` | DeepSeek 基础 URL | `https://api.deepseek.com/v1` |
| `COUNCIL_AUTH_TOKEN` | 本地认证 token | `council-local` |

## 开源协议

MIT License - 详见 [LICENSE](LICENSE) 文件。
