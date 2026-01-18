# Nova - 本地终端 Coding Agent

很早期的原型。能调 OpenAI 和 Anthropic，有基本的工具调用（读文件、执行命令）。

## 用法

```bash
export OPENAI_API_KEY=sk-...
python repl.py
```

或者用 Anthropic：

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# 改 config.json 里的 provider 为 "anthropic"
python repl.py
```
