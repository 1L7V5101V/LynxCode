# Nova 新架构设计方案

## 分层结构

```
nova/
├── cli.py              # CLI 入口、参数解析
├── config/             # TOML 配置加载 + 环境变量
├── core/               # 核心运行时
│   ├── engine.py       # 控制循环
│   ├── runtime.py      # 状态 + 组合
│   ├── context.py      # 上下文管理
│   ├── session.py      # 持久化
│   ├── workspace.py    # 工作区
│   └── permissions.py  # 权限
├── providers/          # 模型后端
│   ├── base.py         # 抽象接口
│   └── clients.py      # OpenAI / Anthropic
├── tools/              # 工具系统
│   ├── base.py         # 抽象
│   ├── registry.py     # 注册中心
│   └── *.py            # 具体工具
├── tui/                # Textual TUI
└── features/           # 高阶特性
    ├── memory.py
    ├── skills.py
    └── sandbox/
```

## 关键接口

### Provider
```python
class ModelClient:
    def complete(self, messages: list[dict]) -> str: ...
```

### Tool
```python
class Tool:
    name: str
    description: str
    input_schema: dict
    def run(self, **kwargs) -> str: ...
```

### Engine
```python
class Engine:
    def run_turn(self, user_message: str) -> Generator[Event]: ...
```

## 数据流

```
用户输入 → Engine.run_turn()
         → ContextManager.build_prompt()
         → ModelClient.complete()
         → 解析 tool call / text
         → 执行 tool / 返回
         → 记录到 SessionStore
         → 返回给用户
```
