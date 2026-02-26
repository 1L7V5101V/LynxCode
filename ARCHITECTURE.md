# Nova 架构设计（定稿）

## 架构演化

- v1 (2025-12): 单文件 agent.py → 初步模块拆分
- v2 (2026-02): 分层尝试 → 循环依赖 → 部分功能推翻重做
- v3 (2026-03): 完整重写，遵循以下设计

## 新架构方向

### 三层模型

```
CLI / TUI / REPL    ← 交互层
     ↓
Runtime             ← 状态管理层（session、workspace、memory）
     ↓
Engine              ← 控制循环层（model call → tool execute → ...）
     ↓
Providers | Tools   ← 后端抽象层
```

### 关键设计原则

- 单向依赖，不允许反向引用
- Event-driven engine loop（不是同步 ask/response）
- Provider 统一接口：complete(messages) → text
- Tool 标准化：name, description, input_schema, run()
- Session 持久化用 JSON 不用 pickle
- 配置从 TOML 文件 + 环境变量合并
