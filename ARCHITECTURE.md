# Nova 架构设计（草稿）

## 当前问题

v2 原型的主要问题：

1. **循环依赖** — engine 和 tools 互相引用
2. **配置混乱** — 硬编码路径到处有
3. **测试困难** — 没有 provider mock，跑一次花几毛钱
4. **单文件膨胀** — engine.py 300+ 行还在涨

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
