---
name: nova-resume
description: 为 NovaCode (pico-v3) 项目撰写的技术简历，使用 STAR 原则
metadata:
  type: project
---

## NovaCode — 本地终端 Coding Agent

**项目定位**：在 git 仓库内运行的终端 AI agent，对接多种 LLM provider，通过读代码、跑命令、改文件完成开发任务，并将上下文沉淀为本地持久记忆。

**代码规模**：Python ~15,000 行，单仓库零外部运行时依赖（仅依赖 pydantic、textual、tomli 三个包）。

**技术栈**：Python 3.10+，Textual TUI，OpenAI/Anthropic-compatible HTTP API，bubblewrap 沙箱，pytest 测试套件。

---

### Star 1：多层记忆系统 — 工作记忆 + 文件持久记忆 + 离线整合

**情景**：Agent 每轮对话都需要感知上下文，但把全部 session 历史塞进 prompt 会快速撑满上下文窗口；重启后 session 记忆全部丢失。

**任务**：设计一套能跨 session 存活、自动淘汰过期信息的记忆体系。

**行动**：

1. 实现了 `LayeredMemory`（`nova/features/memory.py`），分两层：
   - **工作记忆**：当前任务摘要、最近 8 个文件路径、6 个文件短摘要、12 条跨轮笔记。每轮工具调用后通过 `update_memory_after_tool()` 增量更新，只从 read_file/write_file/patch_file 结果中提纯高价值信息。
   - **持久记忆**：按 topic（project-conventions / key-decisions / dependency-facts / user-preferences）分类写入 `.nova/memory/topics/` 目录，通过 `MEMORY.md` 索引文件组织。
2. 用文件修改时间（mtime）做 freshness 追踪：session 恢复时自动比对 checkpoint 中的 key_files freshness 与当前磁盘状态，标记过期路径并从工作记忆中淘汰。
3. 实现了 `/dream` 命令——启动一个独立的轻量 agent（`run_dream()`），读取 `logs/` 目录下的 daily log，调用 LLM 归纳出新的 topic 条目并更新索引。两次 dream 之间最少间隔 24 小时或 5 个新 session。
4. 用文件锁（`.consolidate-lock`）防止并发 consolidation，锁超时 1 小时。

**结果**：Agent 重启后能正确识别哪些文件被外部修改过、只加载未过期的摘要；持久记忆占 prompt 不超过 10000 字符；单次 dream 最多处理 30 个 session，不撑爆模型上下文。

---

### Star 2：Provider 抽象层 — 双协议 + 自动重试 + Prompt Cache 复用

**情景**：需要同时支持 OpenAI-compatible 和 Anthropic-compatible 两类 API，且响应结构、鉴权方式、重试逻辑、prompt cache 语义各不相同。

**任务**：抹平差异，对 runtime 暴露统一的 `complete(prompt, max_tokens)` 接口。

**行动**：

1. 在 `nova/providers/clients.py` 中分别实现 `OpenAICompatibleModelClient` 和 `AnthropicCompatibleModelClient`，均对外暴露相同的 `complete()` 签名。
2. OpenAI client 同时处理普通 JSON 响应和 SSE 流式响应（`_extract_openai_response_from_sse()`），从 `/responses` 和 `/messages` 两种端点中提取文本和 usage 元数据。
3. 重试逻辑（`_request_with_retries()`）按 HTTP 状态码分类：408/429/5xx 自动重试，401/403 直接抛出，最多重试 2 次，间隔按 `Retry-After` 头或指数退避（0.5s × attempt）。
4. OpenAI client 支持 `prompt_cache_key` 参数：将稳定前缀的 hash 传给 provider 的 `/responses` 接口，复用前缀缓存。`supports_prompt_cache` 由 endpoint 域名自动判定（openai.com / right.codes）。
5. 配置按 5 层优先级合并（CLI > 环境变量 > 项目 .nova.toml > 全局 ~/.config/nova/config.toml > 代码默认），通过 `resolve_provider_config()` 统一处理。

**结果**：切换 provider 只需改一个 `--provider` 参数；provider 错误（认证失败/限流/服务端错误）被分类后出现在 trace 和 report 中，不吞没也不暴露原始 key。

---

### Star 3：沙箱化 Shell 执行 — bubblewrap 隔离 + 命令白名单 + 环境变量过滤

**情景**：Agent 执行 shell 命令存在安全风险——不可信 prompt 可能注入恶意命令，子进程可能意外读取父 shell 的敏感环境变量。

**任务**：为 `run_shell` 工具提供可选的沙箱隔离层。

**行动**：

1. 在 `nova/features/sandbox/runner.py` 中实现 `SandboxRunner`，支持三种模式：`off`（直接 shell）、`best_effort`（有沙箱就用，没有就 fallback）、`required`（没有沙箱就报错）。
2. 沙箱后端使用 bubblewrap（`bwrap`）：`_bubblewrap_argv()` 构造 bwrap 参数，只绑定必要的系统目录（`/usr`、`/lib`、`/tmp`），工作目录映射为读写，其余路径只读。
3. 用 `SandboxChecker` 检测 bwrap 是否可用；通过 `command_matcher.py` 中的 `command_is_excluded()` 检查命令是否匹配排除列表（如 `npm install`、`pip install` 等网络命令）。
4. `shell_env()` 方法只传递白名单变量（HOME、PATH、PWD、SHELL、TERM、TMPDIR 等 15 个），不继承父进程全部环境变量；API key 等敏感变量在 `ShellEnvBuilder` 中被显式过滤。

**结果**：沙箱模式在 CI 和无沙箱环境都能跑；命令注入在 best_effort 模式下有沙箱保护，无沙箱时也有环境变量最小化保护。

---

### Star 4：Engine 控制循环 — 多步 Tool-Use + 错误恢复 + Checkpoint

**情景**：Agent 需要自动执行多轮"模型生成→执行工具→结果反馈→再次调用模型"的循环，过程中可能遇到模型返回格式错误、provider 超时、step 超限。

**任务**：实现一个健壮的控制循环，能处理这些异常并保留恢复点。

**行动**：

1. `Engine.run_turn()` 是一个生成器（yield events），产生 `turn_started`、`model_requested`、`model_parsed`、`final` 等事件，TUI 和 REPL 共用同一套事件流。
2. 循环内做三件事：
   - 模型调用异常时调用 `should_retry_model_error()` 按错误码和重试次数决定是否重试
   - 模型返回 `<tool>` 标签时执行工具，结果写入 history 后继续下一轮
   - 模型返回 `<final>` 时结束，写入 run report
3. 每轮开始前通过 `evaluate_resume_state()` 检查 checkpoint 有效性（schema 版本、file freshness、runtime identity），发现变动时创建新 checkpoint。
4. 用 `TaskState` 追踪本轮状态（attempts、tool_steps、changed_paths、status、stop_reason），每轮写盘，支持 `compact_history()` 做上下文压缩。

**结果**：模型格式错误自动重试最多 2 次；step 超限时输出进展总结并明确提示用户 `/resume`；checkpoint 在 workspace 变化时自动失效，不重复使用过期缓存。

---

### Star 5：Evaluation 框架 — 可复现 Benchmark + 自动评分 + Provider 实验

**情景**：修改 agent 行为后需要客观衡量代码生成质量，不能只靠人工观察。

**任务**：建立一套自动化 benchmark 系统。

**行动**：

1. 在 `nova/evaluation/` 中实现 `Evaluator`——从 `benchmarks/coding_tasks.json` 读取任务定义（prompt、fixture_repo、allowed_tools、step_budget、expected_artifact、verifier）。
2. 每个测试在临时目录 checkout fixture repo，注入 `ScriptedModelClient` 或真实 provider client，运行 agent 后通过 verifier 函数（检查文件内容/结构）自动评分。
3. `metrics.py` 聚合多轮结果：统计 tool_steps、attempts、pass/fail 比率，写入 `artifacts/` 目录的 JSON 文件，并生成 markdown 报告。
4. 配套了 5 个实验脚本：`run_provider_experiments.py`（跨 provider 对比）、`run_large_scale_experiments.py`（批量）、`run_business_scenario_dogfood.py`（业务场景）、`run_real_session_acceptance.py`（真实会话）、`run_v3_human_scenario_gate.py`（人工验收门禁）。
5. `ScriptedModelClient`（`nova/testing.py`）用预定义输出序列模拟模型调用，用于回归测试：不依赖 provider 可用性，结果完全确定。

**结果**：benchmark 覆盖 10+ 编码任务类别；provider 对比实验可在同一组任务上切换 OpenAI/Anthropic/DeepSeek 并对比通过率和耗时。

---

### 其他关键组件

- **Tool Registry**（`nova/tools/registry.py`）：15 个工具显式注册，每个工具有 pydantic schema、risk 标记、执行函数。支持按 profile（default/readonly/plan）动态开启/关闭工具集。
- **TUI**（`nova/tui/`）：使用 Textual 框架实现，含 ChatLog、InputBar、StatusBar、ToolCard 等组件；通过事件驱动方式消费 Engine.run_turn() 的事件流。
- **Worker Manager**（`nova/core/worker_manager.py`）：异步 sub-agent 管理，支持子任务状态追踪和跨 agent 通知。
- **Session Store**（`nova/core/session_store.py`）：session 序列化到 `.nova/sessions/`，支持按 id 或 "latest" 恢复。
- **Skills**（`nova/features/skills.py`）：从 `.nova/skills/` 目录发现 slash command，用户可自注册可复用工作流。
- **测试套件**：30+ pytest 文件，覆盖 engine 控制流、context 组装、memory 生命周期、sandbox 隔离、tool 校验、权限审批、session 恢复、benchmark evaluator、TUI 等模块。

---

### 客观数据

- 外部依赖：3 个（pydantic、textual、tomli）
- provider 协议：2 种（OpenAI-compatible、Anthropic-compatible）
- 沙箱模式：3 级（off / best_effort / required）
- 测试文件：30+，覆盖率涵盖核心组件
- benchmark 任务：10+ 编码类别，支持 fixture repo + verifier 自动评分
- 配置优先级：5 层合并
- session checkpoint：支持 5 种 resume 状态（none / full-valid / partial-stale / schema-mismatch / workspace-mismatch）
