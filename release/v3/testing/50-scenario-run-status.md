# Nova v3 50 端到端真人场景运行状态报告

> 生成日期：2026-07-19
> 当前 HEAD：`40a72c2`

---

## 概要

v3 release 包中设计了 **50 个端到端真人使用场景**（来自 `release/v3/testing/01-test-design.md`），
通过 `scripts/run_v3_human_scenario_gate.py` 从进程级 CLI/REPL 入口驱动 Nova，模拟真人操作后只读验证 `.nova` artifacts。

### 最后一次全量执行结果

| 指标 | 值 |
|---|---|
| 执行日期 | 2026-05-13 |
| 执行分支 | `v3` |
| **通过/失败** | **50 passed / 0 failed** |
| Runner 输出目录 | `/private/tmp/nova-v3-human-scenarios/20260513-170838`（macOS，当前环境不可达） |
| Summary JSON | `.../summary.json` → `{"status": "passed", "passed": 50, "failed": 0}` |
| 代码检查 | `ruff check .` → All checks passed |
| 回归测试 | `pytest tests -q` → 224 passed, 2 skipped |

---

## 按场景分组详细结果

### 真实业务场景（R01-R05）—— 5/5 ✅

| ID | 场景 | Driver | 状态 |
|---|---|---|---|
| R01 | 学生管理系统 CRUD 脚手架 | one-shot CLI / DeepSeek | ✅ passed |
| R02 | 订单价格折扣 bugfix | one-shot CLI / DeepSeek | ✅ passed |
| R03 | 发布就绪审查报告 | REPL project skill / DeepSeek | ✅ passed |
| R04 | 线上事故续接修复 | two one-shot CLI runs / DeepSeek | ✅ passed |
| R05 | 库存 CSV 导入器（审批路径） | one-shot CLI approval / DeepSeek | ✅ passed |

### 入口与交互（S06-S14）—— 9/9 ✅

| ID | 场景 | Driver | 状态 |
|---|---|---|---|
| S06 | TTY 默认进入 TUI | PTY TUI smoke | ✅ passed |
| S07 | `--repl` 进入普通 REPL + `/help` | PTY-style stdin REPL | ✅ passed |
| S08 | prompt 参数走 one-shot | one-shot CLI / DeepSeek | ✅ passed |
| S09 | piped stdin 使用 REPL | piped stdin REPL | ✅ passed |
| S10 | TUI slash suggestion | slash registry check | ✅ passed |
| S11 | `/session` 展示 runtime 状态 | PTY REPL slash command | ✅ passed |
| S12 | `/usage` 展示 provider metadata | one-shot + REPL resume | ✅ passed |
| S13 | `/model` 只改当前 runtime | PTY REPL slash command | ✅ passed |
| S14 | `/clear` 开新 session | PTY REPL slash command | ✅ passed |

### Plan Mode（S15-S20）—— 6/6 ✅

| ID | 场景 | Driver | 状态 |
|---|---|---|---|
| S15 | plan mode 只能写 active plan | REPL + resume / DeepSeek | ✅ passed |
| S16 | 未写计划不能 final | PTY REPL / DeepSeek | ✅ passed |
| S17 | 绝对路径 plan artifact 自动归一 | PTY REPL / DeepSeek | ✅ passed |
| S18 | 越界 plan path 被拒 | PTY REPL slash command | ✅ passed |
| S19 | plan mode 允许 Explore 子 agent | PTY REPL / DeepSeek | ✅ passed |
| S20 | plan mode 禁止 worker 写入 | PTY REPL slash command | ✅ passed |

### Tool Policy / Permission / Sandbox（S21-S30）—— 10/10 ✅

| ID | 场景 | Driver | 状态 |
|---|---|---|---|
| S21 | 改文件前必须先读 | one-shot CLI / DeepSeek | ✅ passed |
| S22 | 新文件可写，覆盖旧文件前必须读 | one-shot CLI / DeepSeek | ✅ passed |
| S23 | 自己刚写的文件可 patch | one-shot CLI / DeepSeek | ✅ passed |
| S24 | shell 搜索被拒绝 | one-shot CLI / DeepSeek | ✅ passed |
| S25 | pipe 输出管理允许 | one-shot CLI / DeepSeek | ✅ passed |
| S26 | 长 shell 输出落 artifact | one-shot CLI / DeepSeek | ✅ passed |
| S27 | `approval=never` 拒绝 risky tool | one-shot CLI / DeepSeek | ✅ passed |
| S28 | required sandbox fail closed | one-shot CLI / DeepSeek | ✅ passed |
| S29 | best_effort sandbox degrade | one-shot CLI / DeepSeek | ✅ passed |
| S30 | `/skills` 列本地 skill（不调模型） | PTY REPL slash command | ✅ passed |

### Skills / Subagent / Worker（S31-S38）—— 8/8 ✅

| ID | 场景 | Driver | 状态 |
|---|---|---|---|
| S31 | 内置 review skill 带参数 | PTY REPL builtin skill / DeepSeek | ✅ passed |
| S32 | 项目 skill 参数替换 | REPL slash skill / DeepSeek | ✅ passed |
| S33 | skill allowed-tools 限制写入 | PTY REPL project skill / DeepSeek | ✅ passed |
| S34 | fork skill 不污染主 history | one-shot + REPL fork skill | ✅ passed |
| S35 | prompt-only skill 不启动模型 | PTY REPL prompt-only skill | ✅ passed |
| S36 | invalid skill frontmatter 可诊断 | PTY REPL slash command | ✅ passed |
| S37 | Explore 子 agent 只读探索 | one-shot CLI / DeepSeek | ✅ passed |
| S38 | Worker write scope | one-shot CLI / DeepSeek | ✅ passed |

### Todo / Memory / Context（S39-S45）—— 7/7 ✅

| ID | 场景 | Driver | 状态 |
|---|---|---|---|
| S39 | worker continuation 续接 | one-shot CLI / DeepSeek | ✅ passed |
| S40 | running worker send guard | one-shot CLI / DeepSeek | ✅ passed |
| S41 | task_stop worker | one-shot CLI / DeepSeek | ✅ passed |
| S42 | `/clear` stops worker | one-shot + REPL clear | ✅ passed |
| S43 | `/remember` 写 daily log | PTY-style stdin REPL | ✅ passed |
| S44 | `/dream` 写 memory | PTY REPL / DeepSeek | ✅ passed |
| S45 | secret-shaped memory rejected | one-shot CLI / DeepSeek | ✅ passed |

### Provider / Recovery / Safety（S46-S50）—— 5/5 ✅

| ID | 场景 | Driver | 状态 |
|---|---|---|---|
| S46 | manual compact | PTY REPL slash command | ✅ passed |
| S47 | resume workspace mismatch | one-shot + resume | ✅ passed |
| S48 | provider profiles | one-shot slash `/usage` | ✅ passed |
| S49 | provider error metadata | one-shot CLI bad endpoint | ✅ passed |
| S50 | path traversal 与 secret redaction | one-shot CLI / DeepSeek | ✅ passed |

---

## 结果文件在哪

### 最后一次全量执行输出

由于 runner 使用 `pty`（POSIX-only），该执行在 **macOS** 上完成，输出目录：

```
/private/tmp/nova-v3-human-scenarios/20260513-170838/
```

**当前 Windows 环境不可达**。该目录结构包含：

| 路径 | 内容 |
|---|---|
| `summary.json` | `{"status": "passed", "passed": 50, "failed": 0}` |
| `summary.md` | 人类可读的概要表格 |
| `logs/<ID>.command.json` | 每个场景实际执行的命令、return code、duration |
| `logs/<ID>.stdout.txt` | stdout 完整输出 |
| `logs/<ID>.stderr.txt` | stderr 完整输出 |
| `workspaces/<id>/.nova/runs/run_*/report.json` | Nova run report |
| `workspaces/<id>/.nova/runs/run_*/trace.jsonl` | 工具调用追踪 |
| `workspaces/<id>/.nova/sessions/*.events.jsonl` | session 事件流 |

### 其他相关测试结果（可在 Windows 上运行 ✅）

| 测试文件 | 类型 | 当前结果 |
|---|---|---|
| `tests/test_release_smoke.py` | 4 个确定性 E2E 冒烟测试 | ✅ 4 passed, 1 skipped（2026-07-19 验证） |
| `tests/test_real_session_acceptance.py` | Gate8 多场景验收（9 场景） | ❌ failed（summary 返回 failed） |
| `pytest tests/`（全量 28 个文件） | 289 个 test functions | ⚠️ 过去记录 224 passed, 2 skipped；当前状态待验证 |

---

## 当前能否重跑

| 条件 | 状态 | 说明 |
|---|---|---|
| Windows 原生 runner | ❌ | `scripts/run_v3_human_scenario_gate.py` 依赖 `pty`（POSIX） |
| macOS/Linux runner | ✅ | `uv run python scripts/run_v3_human_scenario_gate.py --suite full` |
| 需要 provider key | ✅ | 默认读取 `.nova.toml`（需配置） |
| 需要 `uv` | ✅ | 需要 `uv` 创建隔离 workspace |

---

## 修复过的问题（来自执行记录）

在 50 场景执行过程中发现并修复的产品缺陷：

| 场景 | 问题 | 修复 |
|---|---|---|
| S15 | plan mode 坏写入重复到 step limit | 重复调用守卫前移到 permission/policy 前 |
| S21 | prior_read_required 拒绝后补读重试仍被误判 | 允许错误调用在同路径成功 read 后重试 |
| S23 | patch 成功后模型重放同一个 write 回滚 | write_file/patch_file 成功后同参重放直接拒绝 |
| S18 | `/plan` 非法路径导致 REPL 崩溃 | 捕获 ValueError，返回用户可见 error |
| S26 | runner 找不到长 shell 输出 artifact | RunEvidence 统一读取 trace 的 full_output_artifact |

---

## 参考文档

| 文档 | 内容 |
|---|---|
| `release/v3/testing/01-test-design.md` | 50 场景详细设计 + 覆盖矩阵 |
| `release/v3/testing/02-execution-record.md` | 全量执行记录、缺陷和修复 |
| `release/v3/testing/03-runner-and-evidence.md` | Runner 用法、证据目录结构、排错指南 |
| `release/v3/testing/04-scenario-checklist.md` | 50 场景复盘检查清单 |
| `release/v3/TESTING.md` | 快速重跑入口 |
| `scripts/run_v3_human_scenario_gate.py` | 场景 runner 源码 |
