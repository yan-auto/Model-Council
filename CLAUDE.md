# Council

本地私人 AI 委员会系统。多角色、有记忆、能讨论。

## 架构

七层，从上到下：

```
Client          React Web UI · SSE流式 · WebSocket实时讨论
API Gateway     FastAPI · 鉴权 · 限流 · Command Parser
Core Engine     Agent Router · Orchestrator · Context Builder · Event Bus
Services        Memory · RAG · Model路由 · Tool执行
Data            SQLite · ChromaDB · 文件系统
Adapters        OpenAI · Anthropic · MiniMax · DeepSeek · 任意兼容接口
Plugin System   角色插件 · 工具插件 · 记忆策略插件
```

每层独立，通过接口调用，不直接依赖具体实现。

## 设计原则

- **模块化**：任何一层可单独升级，不影响其他层
- **事件驱动**：模块通过 Event Bus 通信，不直接调用
- **本地优先**：数据全在本地，断网也能用
- **指令系统**：`@角色名` 路由，`/discuss` 开讨论，`/stop` 停，指令不走 LLM
- **可插拔**：角色插件写 YAML，工具插件和记忆策略插件各走各的接口

## 讨论模式

核心功能。角色之间互相看到对方说了什么，基于对方的回答再回应。三种控制：固定轮次自动停、用户 `/stop`、模型判断共识达成自动停。

## 目录结构

```
Council/
├── config/
│   ├── agents/            # 角色定义（YAML）
│   └── settings.yaml      # 系统配置
├── src/
│   ├── api/               # API Gateway
│   ├── core/              # Core Engine（路由、编排、事件总线）
│   ├── services/          # Memory · RAG · Model路由
│   ├── data/              # 数据访问层
│   ├── adapters/          # 模型适配器
│   └── plugins/           # 插件系统
├── web/                   # React 前端
├── tests/
└── data/                  # 本地数据
    ├── db/                # SQLite
    ├── vectors/           # ChromaDB
    └── knowledge/         # 知识库
```

## 技术栈

- 后端：Python + FastAPI
- 前端：React
- 数据：SQLite + ChromaDB
- 通信：SSE（流式）+ WebSocket（讨论）

## 内置角色

- **推进者**：创业决策伙伴，硬核理性，对话结束给一个行动
- **透视**：新闻解读，唯物史观和阶级分析，一句话说穿本质

## 规范

- 凭证放 `.env`，不提交仓库
- 角色定义走 YAML，不改动核心引擎
- 不确定的地方先问，别猜
