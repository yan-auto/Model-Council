# 贡献指南

感谢你对 Council 的关注！以下是贡献方式。

## 如何添加新角色

在 `config/agents/` 下新建 YAML 文件，格式如下：

```yaml
name: analyst           # 角色ID（英文，用于 @提及）
description: "一句话描述"

personality:
  tone: "语气风格"
  traits: ["特征1", "特征2"]
  constraints: "行为约束"

system_prompt: |
  你是一个...

  每次回复格式：
  1. xxx
  2. xxx
```

## 如何添加新模型供应商

1. 在 `src/adapters/` 下新建适配器文件，继承 `base.py` 中的 `BaseAdapter`
2. 实现 `chat_stream()` 方法
3. 在 `src/data/models.py` 的 `ProviderType` 中注册类型
4. 在 `src/services/model_router.py` 中添加创建逻辑

## 开发流程

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 编写测试（覆盖率 ≥ 80%）
4. 确保所有测试通过：`pytest tests/`
5. 提交 PR

## 代码规范

- Python：遵循 PEP 8，使用 type annotations
- 前端：ESLint + 组件化
- 提交信息格式：`<type>: <description>`

## 报告问题

在 GitHub Issues 中提交，请包含：

1. 复现步骤
2. 期望行为
3. 实际行为
4. 环境信息（Python 版本、操作系统等）
