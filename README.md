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
