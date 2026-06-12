# NovaCode

本地终端 coding agent。跑在仓库里，接模型 provider，读代码、跑命令、改文件，把上下文沉淀成本地记忆。

## 安装

要求 Python 3.10+，一个可用的模型 provider key。

```bash
curl -fsSL https://raw.githubusercontent.com/1L7V5101V/NovaCode/main/install.sh | bash
```

或源码安装：

```bash
git clone https://github.com/1L7V5101V/NovaCode.git
cd NovaCode
pip install -e .
```

## 配置

NovaCode 启动前解析一个 provider profile，由四项组成：

| 字段 | 作用 |
| --- | --- |
| `protocol` | 请求协议，支持 `openai` 和 `anthropic` |
| `api_key` | provider key |
| `base_url` | provider endpoint |
| `model` | 模型名 |

配置合并顺序：CLI 参数 > 环境变量 > 项目 `.nova.toml` > 全局 `~/.config/nova/config.toml` > 默认值

### 方式一：项目 .nova.toml

```bash
cp .nova.toml.example .nova.toml
$EDITOR .nova.toml
```

`.nova.toml` 默认被 `.gitignore` 忽略，不要把 key 提交进 git。

最小示例：

```toml
provider = "deepseek"

[providers.deepseek]
protocol = "anthropic"
api_key = "sk-..."
base_url = "https://api.deepseek.com/anthropic"
model = "deepseek-v4-pro"
```

### 方式二：环境变量

```bash
export NOVA_PROVIDER=deepseek
export DEEPSEEK_API_KEY=sk-...
export DEEPSEEK_BASE_URL=https://api.deepseek.com/anthropic
export DEEPSEEK_MODEL=deepseek-v4-pro
nova
```

### 方式三：命令行

```bash
nova --provider openai --model gpt-5.4 --base-url https://api.openai.com/v1
nova --provider deepseek --approval ask --max-steps 80
```

完整配置见 [docs/configuration.md](docs/configuration.md)。

## 启动

```bash
nova                              # TUI
nova --repl                       # 普通终端 REPL
nova "找出测试失败的根因"         # one-shot
nova --resume latest              # 续接最近 session
```

运行参数：

```bash
nova --approval ask               # shell/写文件前询问
nova --approval auto              # 自动通过
nova --approval never             # 非交互模式
nova --sandbox best_effort        # 隔离 shell 命令
nova --no-auto-dream              # 关闭后台 memory 整合
```

## 用法

TUI 或 REPL 中输入自然语言或 slash command：

```
> /help
> /skills
> /session
> /plan 重构 provider 配置加载逻辑
> /review
> /remember 这个项目用 DeepSeek 的 Anthropic-compatible endpoint
> /dream
```

## 结构

```text
nova/
├── cli.py                 # CLI 参数、启动模式、REPL 命令
├── config/                # provider profile、TOML、env 解析
├── core/                  # runtime、engine、session、workers、context
├── features/              # memory、skills、sandbox
├── providers/             # OpenAI/Anthropic-compatible client
├── tools/                 # tool registry 和具体工具
├── tui/                   # Textual TUI
└── evaluation/            # run evidence、metrics
```

## 测试

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

## License

MIT
