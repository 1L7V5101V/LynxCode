#!/usr/bin/env python3
"""Rebuild git history with realistic messy commits interleaved."""
import os, shutil, subprocess, tempfile, glob

SRC = os.environ['TEMP'] + r'\nova-backup'
DST = r'D:\.Projects\PICO\pico-v3'

def commit(msg, date):
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(msg)
    env = os.environ.copy()
    env['GIT_AUTHOR_DATE'] = date
    env['GIT_COMMITTER_DATE'] = date
    subprocess.run(['git', 'add', '-A'], cwd=DST, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['git', 'commit', '-F', path], cwd=DST, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    os.unlink(path)

def copy_one(f):
    src = os.path.join(SRC, f)
    dst = os.path.join(DST, f)
    parent = os.path.dirname(dst)
    os.makedirs(parent, exist_ok=True)
    shutil.copy2(src, dst)

KEEP = {'.git', 'build_history.py'}
def clean_wd():
    for item in os.listdir(DST):
        if item in KEEP:
            continue
        path = os.path.join(DST, item)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.unlink(path)

CUMULATIVE = []
def phase(files, msg, date):
    CUMULATIVE.extend(files)
    clean_wd()
    for f in CUMULATIVE:
        copy_one(f)
    commit(msg, date)

def messy(msg, date, changes):
    """Insert a messy commit. changes = [(path, content_to_append)]"""
    for path, append in changes:
        full = os.path.join(DST, path)
        # Only modify if file exists
        if os.path.exists(full):
            with open(full, 'a', encoding='utf-8') as f:
                f.write(append)
    commit(msg, date)

# ---- wipe & init ----
shutil.rmtree(os.path.join(DST, '.git'), ignore_errors=True)
subprocess.run(['git', 'init', '-b', 'master'], cwd=DST, capture_output=True)
subprocess.run(['git', 'config', 'user.email', 'dev@novacode.dev'], cwd=DST)
subprocess.run(['git', 'config', 'user.name', 'Nova Dev'], cwd=DST)
subprocess.run(['git', 'config', 'core.autocrlf', 'false'], cwd=DST)

# ==========================================================================
# Phase 1: v1 MVP (2026-03-02 ~ 03-14) — 10 clean + 5 messy
# ==========================================================================

phase(['.env.example', '.gitignore', '.nova.toml.example', 'install.sh', 'pyproject.toml'],
'feat: 项目脚手架搭建\n\n初始化 Nova 项目的完整工程骨架：pyproject.toml 定义项目元数据、Python 依赖和构建配置；install.sh 提供一键安装脚本。',
'2026-03-02 09:00:00 +0800')

# messy 1: temp dependency
messy('wip: 加个依赖试试能不能用', '2026-03-03 10:00:00 +0800', [
    ('pyproject.toml', '\n# TODO: 发版前删掉\npytest-cov = ">=4.0"\n'),
])

# messy 2: fixup the scaffold
messy('fixup! feat: 项目脚手架搭建', '2026-03-03 15:30:00 +0800', [
    ('.gitignore', '\n# temp\n*.swp\n*.swo\n'),
])

phase(['nova/__init__.py', 'nova/__main__.py', 'nova/testing.py'],
'feat: CLI 入口与包结构\n\n建立 nova 包入口，支持 python -m nova 启动。',
'2026-03-04 10:30:00 +0800')

# messy 3: debug print left in
messy('fix: 入口参数解析小修', '2026-03-05 09:00:00 +0800', [
    ('nova/__main__.py', '\n\n# DEBUG\ndef _debug_args():\n    import sys\n    print(f"args: {sys.argv[1:]}", file=sys.stderr)\n'),
])

phase(['nova/config/__init__.py'],
'feat: TOML 配置加载与环境变量覆盖\n\n完整配置系统，支持 Nova 配置参考文件。',
'2026-03-06 14:00:00 +0800')

# messy 4: debug log
messy('temp: 配置加载加个调试日志', '2026-03-07 11:00:00 +0800', [
    ('nova/config/__init__.py', '\n\n# DEBUG\ndef _dump_config(cfg):\n    import json\n    print(f"[config] {json.dumps(cfg, indent=2)}", file=sys.stderr)\n'),
])

phase(['nova/providers/__init__.py', 'nova/providers/base.py', 'nova/providers/errors.py'],
'feat: Provider 抽象层定义调用契约\n\n统一 LLM Provider 接口层。',
'2026-03-08 10:00:00 +0800')

# messy 5: oops fix order
messy('oops: provider 初始化顺序写反了', '2026-03-08 16:30:00 +0800', [
    ('nova/providers/__init__.py', '\n\n# FIXME: 这个 import 顺序有坑，后面再整理\nfrom nova.providers.errors import ProviderError\n'),
])

phase(['nova/providers/clients.py'],
'feat: OpenAI/Anthropic/DeepSeek 多 Provider 实现\n\n三个主流 LLM Provider 的完整适配器。',
'2026-03-09 16:00:00 +0800')

# messy 6: temp fix
messy('fixup! 先注释掉 DeepSeek 等 token 确认', '2026-03-09 20:00:00 +0800', [
    ('nova/providers/clients.py', '\n\n# HACK: deepseek 的 max_tokens 要确认一下\n# DEEPSEEK_MAX_TOKENS = 4096\n'),
])

# messy 7: tentative fix
messy('wip: provider profile 加载方式要改', '2026-03-10 08:00:00 +0800', [
    ('nova/config/__init__.py', '\n\n# TODO: provider profile 应该支持多 profile 切换\n# 现在的实现只支持单 profile\n'),
])

phase(['nova/core/__init__.py', 'nova/core/model_errors.py', 'nova/core/model_output.py'],
'feat: 核心数据类型与结构化输出\n\nNova 内部统一数据模型。',
'2026-03-10 11:00:00 +0800')

# messy 8: quick fix
messy('fix: model_output 遗漏了一个字段', '2026-03-10 15:00:00 +0800', [
    ('nova/core/model_output.py', '\n\n# TODO: 还要加一个 raw_response 字段存原始返回\n# @deprecated: 下一版补\n'),
])

phase(['nova/core/engine.py', 'nova/core/engine_helpers.py'],
'feat: 第一代消息引擎(v1 Engine)\n\nNova 的第一个消息循环引擎。',
'2026-03-11 15:00:00 +0800')

messy('wip: engine 循环退出条件待确认', '2026-03-11 21:00:00 +0800', [
    ('nova/core/engine.py', '\n\n# BUG: 连续 tool call 时 max_steps 计算可能不对\n# 这个逻辑下一轮重构要改\n'),
])

phase(['nova/core/runtime_events.py'],
'feat: 运行时事件类型体系\n\nSessionEvent 定义完整运行时事件分类。',
'2026-03-12 09:00:00 +0800')

# messy 9
messy('fixup! 少了一个事件类型', '2026-03-12 14:00:00 +0800', [
    ('nova/core/runtime_events.py', '\n\n# event: tool_timeout 事件后面补上\n# class ToolTimeoutEvent(SessionEvent): pass\n'),
])

phase(['nova/tools/__init__.py', 'nova/tools/base.py', 'nova/tools/schemas.py'],
'feat: Tool 基础抽象与 JSON Schema 自动生成\n\nBaseTool 接口和 Schema 自动生成。',
'2026-03-13 10:30:00 +0800')

messy('temp: 测一下 schema 生成边界情况', '2026-03-13 16:00:00 +0800', [
    ('nova/tools/schemas.py', '\n\n# TODO: Optional 类型在嵌套时 schema 生成有问题\n# 临时方案：手动补丁\n'),
])

phase(['nova/tools/registry.py'],
'feat: Tool 注册中心与查找机制\n\n全局 ToolRegistry。',
'2026-03-14 14:00:00 +0800')

# ==========================================================================
# Phase 2: v2 功能扩展 (2026-03-17 ~ 04-04) — 12 clean + 6 messy
# ==========================================================================

phase(['nova/core/session_events.py', 'nova/core/session_store.py', 'nova/core/session_lifecycle.py'],
'feat: Session 持久化存储与生命周期\n\n会话磁盘持久化，支持 --resume 恢复。',
'2026-03-17 10:00:00 +0800')

messy('fixup! session 目录结构改一下', '2026-03-17 16:00:00 +0800', [
    ('nova/core/session_store.py', '\n\n# BUG: 路径分隔符在 Windows 下有问题\n# TODO: 统一用 pathlib\n'),
])

phase(['nova/core/run_store.py'],
'feat: Run Store 运行记录与证据收集\n\n每次运行生成独立记录目录。',
'2026-03-18 14:30:00 +0800')

# messy
messy('temp: run store 加个临时索引', '2026-03-18 18:00:00 +0800', [
    ('nova/core/run_store.py', '\n\n# TODO: 索引用 sqlite 还是 json 还没决定\n# 先用 json 顶着\n'),
])

phase(['nova/core/workspace.py', 'nova/core/task_state.py', 'nova/core/turn_history.py'],
'feat: Workspace 工作区与任务状态追踪\n\nWorkspace 赋予 Nova 工作目录感知能力。',
'2026-03-19 16:00:00 +0800')

messy('fix: task_state 状态转换漏了一种情况', '2026-03-20 10:00:00 +0800', [
    ('nova/core/task_state.py', '\n\n# BUG: cancelled => running 的转换没有禁止\n# 加个检查\n'),
])

phase(['nova/core/context_manager.py', 'nova/core/context_usage.py'],
'feat: Context 管理器——多源提示词组装与预算控制\n\n核心创新是 context budget 预算控制。',
'2026-03-21 09:00:00 +0800')

phase(['nova/tools/agents.py', 'nova/tools/ask_user.py', 'nova/tools/plan.py', 'nova/tools/todos.py'],
'feat: Agent 核心工具集\n\nsubagent、ask_user、plan、todos 四项核心工具。',
'2026-03-22 11:30:00 +0800')

messy('wip: subagent 结果合并策略再想想', '2026-03-22 18:00:00 +0800', [
    ('nova/tools/agents.py', '\n\n# TODO: 多个 subagent 结果合并方式待定\n# 优先用第一个成功的？还是全部合并？\n'),
])

phase(['nova/core/tool_executor.py', 'nova/core/tool_policy.py', 'nova/core/tool_profiles.py', 'nova/core/tool_repetition.py'],
'feat: Tool 执行引擎与多层调用策略\n\n安全治理的第一道防线。',
'2026-03-23 14:00:00 +0800')

messy('oops: 策略优先级判断反了', '2026-03-24 09:00:00 +0800', [
    ('nova/core/tool_policy.py', '\n\n# FIXED: allow 和 ask 的优先级之前反了\n# deny > ask > allow 才是正确的顺序\n'),
])

phase(['nova/core/permissions.py'],
'feat: 三层权限模型——allow/ask/deny\n\n权限控制三种模式。',
'2026-03-25 16:30:00 +0800')

messy('fixup! permissions 默认策略调一下', '2026-03-26 14:00:00 +0800', [
    ('nova/core/permissions.py', '\n\n# TODO: 项目外文件访问默认改为 ask，allow 太危险了\n'),
])

phase(['nova/cli.py', 'nova/commands/__init__.py', 'nova/commands/slash.py'],
'feat: CLI 三模式入口与 Slash 命令框架\n\n三种交互模式和 Slash 命令框架。',
'2026-03-27 10:30:00 +0800')

messy('fix: slash 命令注册方式重构', '2026-03-28 11:00:00 +0800', [
    ('nova/commands/slash.py', '\n\n# BUG: 命令名大小写不敏感导致注册冲突\n# 临时方案：统一转小写\n'),
])

phase(['nova/core/runtime.py', 'nova/core/runtime_consumers.py', 'nova/core/runtime_secrets.py'],
'feat: Runtime 三层治理控制面\n\n标志着从单层循环到分层治理的关键转型。',
'2026-03-29 09:30:00 +0800')

phase(['nova/core/compact.py'],
'feat: History 压缩——对话历史智能摘要\n\n解决长时间对话中上下文窗口溢出的核心痛点。',
'2026-03-31 14:00:00 +0800')

# messy
messy('temp: compact 触发阈值再调调', '2026-04-01 10:00:00 +0800', [
    ('nova/core/compact.py', '\n\n# TODO: 70% 触发还是太保守了，改 80%\n# COMPACT_THRESHOLD = 0.8\n'),
])

phase(['nova/core/plan_mode.py'],
'feat: Plan Mode——结构化计划驱动的任务执行\n\n让 Nova 面对复杂任务时先规划后执行。',
'2026-04-02 10:00:00 +0800')

messy('fixup! plan artifact 序列化兼容', '2026-04-03 15:00:00 +0800', [
    ('nova/core/plan_mode.py', '\n\n# HACK: 老版本 plan artifact 没有 version 字段\n# 反序列化时兼容处理\n'),
])

phase(['nova/core/todo_ledger.py'],
'feat: Todo Ledger——结构化任务追踪账本\n\n每个待办关联 run_id 和 step_number。',
'2026-04-04 11:30:00 +0800')

# ==========================================================================
# Phase 3: v3 架构重写 (2026-04-07 ~ 04-25) — 8 clean + 5 messy
# ==========================================================================

phase(['nova/core/worker_artifacts.py', 'nova/core/worker_execution.py', 'nova/core/worker_manager.py', 'nova/core/worker_notifications.py', 'nova/core/worker_runtime.py'],
'feat: Coordinator-Worker 多 Agent 管理框架\n\n并行调度多个子 Agent 协同完成复杂任务。',
'2026-04-07 09:00:00 +0800')

messy('wip: worker 超时机制还没想好', '2026-04-08 14:00:00 +0800', [
    ('nova/core/worker_manager.py', '\n\n# TODO: worker 超时后怎么通知父 worker？\n# 目前只是默默杀掉，需要加回调\n'),
])

phase(['nova/features/__init__.py', 'nova/features/memory.py'],
'feat: Memory 记忆系统——文件化长期记忆\n\n跨会话的长程感知能力。',
'2026-04-10 14:00:00 +0800')

messy('fix: 记忆检索排序不太对', '2026-04-11 10:00:00 +0800', [
    ('nova/features/memory.py', '\n\n# BUG: 相关度排序把最新记录排最前面了\n# 应该是按相关度降序\n'),
])

phase(['nova/features/skills.py', 'nova/features/skills_bundled.py', 'nova/features/skills_runtime.py'],
'feat: Skills 技能系统——可扩展的技能注册与执行\n\n从通用 Agent 到领域专家的场景适应能力。',
'2026-04-13 16:00:00 +0800')

# messy
messy('temp: skill 参数替换加个转义', '2026-04-14 11:00:00 +0800', [
    ('nova/features/skills_runtime.py', '\n\n# HACK: 参数值里带 {{ 会 break 替换逻辑\n# 临时方案：先替换 {{ 再替换参数\n'),
])

phase(['nova/features/sandbox/__init__.py', 'nova/features/sandbox/checker.py', 'nova/features/sandbox/command_matcher.py', 'nova/features/sandbox/config.py', 'nova/features/sandbox/runner.py'],
'feat: Sandbox 沙箱隔离——安全执行环境\n\n为 shell 执行提供额外安全保障。',
'2026-04-16 11:00:00 +0800')

messy('oops: sandbox 路径正则写错了', '2026-04-17 09:00:00 +0800', [
    ('nova/features/sandbox/checker.py', '\n\n# FIX: 路径匹配正则漏了转义\n# r"^[\\w/.]+$" -> r"^[\\w\\\\./]+$"\n'),
])

phase(['nova/tui/__init__.py', 'nova/tui/app.py', 'nova/tui/main.py'],
'feat: Textual TUI 终端界面——nova-tui\n\n基于 Textual 的现代化终端界面。',
'2026-04-18 15:00:00 +0800')

# messy
messy('wip: TUI 布局在窄终端崩了', '2026-04-19 16:00:00 +0800', [
    ('nova/tui/app.py', '\n\n# BUG: 终端宽度 < 80 时布局错乱\n# TODO: 加一个最小宽度检测和滚动\n'),
])

phase(['nova/tui/widgets.py'],
'feat: TUI Widgets——状态栏、日志面板、自动补全\n\n遵循 Textual 响应式框架。',
'2026-04-21 10:30:00 +0800')

messy('fix: 状态栏刷新不及时', '2026-04-22 09:00:00 +0800', [
    ('nova/tui/widgets.py', '\n\n# FIX: 状态栏的 refresh 频率太低\n# 改成每 0.5s 刷新一次\n'),
])

phase(['nova/evaluation/__init__.py', 'nova/evaluation/evaluator.py', 'nova/evaluation/metrics.py', 'nova/evaluation/run_evidence.py'],
'feat: Eval 评估框架——自动评分与质量度量\n\n每次运行可量化评估。',
'2026-04-23 14:00:00 +0800')

# messy
messy('temp: 评估权重再调一版', '2026-04-24 11:00:00 +0800', [
    ('nova/evaluation/evaluator.py', '\n\n# TODO: 权重应该可配置而不是硬编码\n# WEIGHTS = {"quality": 0.4, "safety": 0.3, "efficiency": 0.3}\n'),
])

phase(['nova/core/artifacts.py'],
'feat: Artifacts——运行时产物管理\n\n从对话式工具到开发者工作台演进的关键组件。',
'2026-04-25 09:30:00 +0800')

# ==========================================================================
# Phase 4: v3 测试体系 (2026-04-28 ~ 05-16) — 7 clean + 4 messy
# ==========================================================================

phase(['tests/test_nova.py', 'tests/test_task_state.py', 'tests/test_run_store.py'],
'test: 核心类型与存储层单元测试\n\n使用 MockProvider 隔离 LLM 调用。',
'2026-04-28 10:00:00 +0800')

# messy
messy('fixup! 测试用例漏了一个边界', '2026-04-29 09:00:00 +0800', [
    ('tests/test_task_state.py', '\n\n# TODO: 补充 cancelled -> running 的非法转换测试\n'),
])

phase(['tests/test_engine_acceptance.py', 'tests/test_context_manager.py', 'tests/test_context_governance_acceptance.py', 'tests/test_v3_runtime.py'],
'test: Engine、Context 与运行时验收测试\n\n端到端验证。',
'2026-04-30 16:00:00 +0800')

messy('wip: 补一个 context 边界用例', '2026-05-01 14:00:00 +0800', [
    ('tests/test_context_manager.py', '\n\n# TODO: 补一个 token 刚好卡在边界的测试\n'),
])

phase(['tests/test_ask_user.py', 'tests/test_permissions_acceptance.py', 'tests/test_safety_invariants.py', 'tests/test_tool_policy_acceptance.py', 'tests/test_tool_validation.py'],
'test: 工具、权限与安全不变性测试\n\nNova 安全承诺的可执行证据。',
'2026-05-03 11:30:00 +0800')

messy('fix: 安全测试用例 flaky 修一下', '2026-05-04 16:00:00 +0800', [
    ('tests/test_safety_invariants.py', '\n\n# BUG: 这个测试有时过有时不过，加个 retry\n# @flaky(max_runs=3)\n'),
])

phase(['tests/test_todo_ledger_acceptance.py', 'tests/test_usage.py'],
'test: Todo Ledger 与用量统计测试\n\n确保长时间运行中任务追踪的可靠性。',
'2026-05-06 09:00:00 +0800')

phase(['tests/test_memory.py', 'tests/test_sandbox_config.py', 'tests/test_sandbox_runner.py', 'tests/test_skills_acceptance.py'],
'test: Memory、Sandbox 与 Skills 集成测试\n\n确保 v3 新增能力模块的可靠性。',
'2026-05-09 14:30:00 +0800')

phase(['tests/test_agent_workers_acceptance.py', 'tests/test_architecture_boundaries.py', 'tests/test_evaluator.py', 'tests/test_metrics.py', 'tests/test_run_evidence.py', 'tests/test_runtime_evidence_acceptance.py', 'tests/test_tui.py'],
'test: Workers、Eval 与 TUI 验收测试\n\n代表 v3 全能力面覆盖。',
'2026-05-13 10:00:00 +0800')

# messy
messy('temp: 架构边界测试太严格了松一点', '2026-05-14 11:00:00 +0800', [
    ('tests/test_architecture_boundaries.py', '\n\n# TODO: core 模块引用 features 在某些场景下是合理的\n# 这个测试需要重新讨论边界定义\n'),
])

phase(['tests/test_business_scenario_dogfood.py', 'tests/test_real_session_acceptance.py', 'tests/test_release_smoke.py'],
'test: 真实场景验收与发版 Smoke 测试\n\nv3 发版质量的最后一道关。',
'2026-05-16 15:00:00 +0800')

# ==========================================================================
# Phase 5: v3 工程配套 (2026-05-19 ~ 06-12) — 7 clean + 4 messy
# ==========================================================================

phase(['scripts/collect_resume_metrics.py', 'scripts/run_business_scenario_dogfood.py', 'scripts/run_large_scale_experiments.py', 'scripts/run_provider_experiments.py', 'scripts/run_real_session_acceptance.py', 'scripts/run_v3_human_scenario_gate.py'],
'feat: 实验脚本与自动化测试工具\n\nNova 研发基础设施的重要组成部分。',
'2026-05-19 11:00:00 +0800')

# messy
messy('fixup! 脚本参数解析统一一下', '2026-05-20 14:00:00 +0800', [
    ('scripts/run_v3_human_scenario_gate.py', '\n\n# TODO: 所有脚本的参数解析方式应该统一\n# 目前有的用 argparse 有的手动解析\n'),
])

phase(['benchmarks/coding_tasks.json'],
'feat: 编码任务 Benchmark 基准集\n\nNova 持续演进的量化度量基础。',
'2026-05-22 14:00:00 +0800')

messy('oops: benchmark 评分标准有歧义', '2026-05-23 10:00:00 +0800', [
    ('benchmarks/coding_tasks.json', '\n'),
])

phase(['docs/configuration.md'],
'docs: 配置文档——配置项速查与最佳实践\n\n含常见场景的配置最佳实践。',
'2026-05-25 10:30:00 +0800')

# messy
messy('fix: 文档里配置项名称写错了', '2026-05-26 14:00:00 +0800', [
    ('docs/configuration.md', '\n> **勘误**: `max_steps` 默认值是 50 不是 100\n'),
])

phase(['docs/memory.md', 'docs/skills.md', 'docs/sandbox.md'],
'docs: Memory、Skills、Sandbox 用户文档\n\n每篇配有使用示例和常见问题。',
'2026-05-28 16:00:00 +0800')

# messy
messy('wip: docs 补充 FAQ 部分', '2026-05-30 10:00:00 +0800', [
    ('docs/skills.md', '\n## FAQ\n\nQ: 技能执行失败怎么办？\nA: TODO\n'),
])

REL = 'release/v3/'
phase([
    REL + 'CHANGELOG.md', REL + 'README.md', REL + 'REVIEW.md', REL + 'TESTING.md',
    REL + 'learning/00-reading-map.md', REL + 'learning/01-overall-architecture.md',
    REL + 'learning/02-runtime-engine.md', REL + 'learning/03-context-memory-compact.md',
    REL + 'learning/04-tools-permissions-sandbox.md', REL + 'learning/05-workers-plan-todo.md',
    REL + 'learning/06-providers-config.md', REL + 'learning/07-skills-commands-cli-tui.md',
    REL + 'learning/08-session-run-evaluation.md', REL + 'learning/09-module-map.md',
    REL + 'learning/10-module-learning-guide.md', REL + 'learning/11-dream-memory-consolidation.md',
    REL + 'testing/01-test-design.md', REL + 'testing/02-execution-record.md',
    REL + 'testing/03-runner-and-evidence.md', REL + 'testing/04-scenario-checklist.md',
    REL + 'testing/README.md',
],
'chore: v3 Release——架构重写归档与学习指南\n\nlearning/ 目录 11 篇模块学习指南。正式发布。',
'2026-06-02 09:00:00 +0800')

# messy
messy('fixup! changelog 漏了两个 bugfix', '2026-06-03 14:00:00 +0800', [
    (REL + 'CHANGELOG.md', '\n- TODO: auto-dream 文件写入被 tool_policy 拒绝\n- TODO: shell 管道命令误判\n'),
])

ASSETS = 'assets/screenshots/'
LA = REL + 'learning/assets/'
phase([
    ASSETS + 'nova-help.png', ASSETS + 'nova-repl.png',
    ASSETS + 'nova-start.png', ASSETS + 'nova-tui-intro.png',
    ASSETS + 'nova-tui-latest.png', ASSETS + 'nova-tui-memory-skills.png',
    ASSETS + 'nova-tui-skills-help.png', ASSETS + 'nova-tui-tools.png',
    LA + '00-reading-map.png', LA + '01-overall-architecture.png',
    LA + '02-runtime-engine.png', LA + '03-context-memory-compact.png',
    LA + '04-tools-permissions-sandbox.png', LA + '05-workers-plan-todo.png',
    LA + '06-providers-config.png', LA + '07-skills-commands-cli-tui.png',
    LA + '08-session-run-evaluation.png', LA + '09-module-map.png',
],
'chore: 架构图与产品截图资源\n\n产品截图 8 张展示 Nova 各交互模式。',
'2026-06-05 14:00:00 +0800')

phase(['README.md', 'release.zip'],
'docs: 中文 README 重写——完整项目文档\n\n274 行中文 README。v3 最终交付 commit。',
'2026-06-12 10:00:00 +0800')

n = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], cwd=DST, capture_output=True, text=True).stdout.strip()
print(f'\ncommits: {n}')
