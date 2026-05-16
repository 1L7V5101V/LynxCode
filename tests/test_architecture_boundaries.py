from pathlib import Path


def test_core_modules_stay_below_entropy_budget():
    root = Path(__file__).resolve().parents[1]
    budgets = {
        "nova/core/runtime.py": 950,
        "nova/core/runtime_events.py": 90,
        "nova/core/runtime_consumers.py": 90,
        "nova/core/artifacts.py": 130,
        "nova/core/task_state.py": 140,
        "nova/core/todo_ledger.py": 120,
        "nova/core/worker_manager.py": 220,
        "nova/core/context_manager.py": 420,
        "nova/core/context_usage.py": 120,
        "nova/core/compact.py": 180,
        "nova/core/engine.py": 470,
        "nova/core/model_errors.py": 100,
        "nova/core/permissions.py": 140,
        "nova/core/tool_policy.py": 90,
        "nova/core/plan_mode.py": 140,
        "nova/core/tool_executor.py": 181,
        "nova/core/tool_profiles.py": 80,
        "nova/core/turn_history.py": 250,
        "nova/features/skills.py": 220,
        "nova/features/skills_bundled.py": 120,
        "nova/features/skills_runtime.py": 140,
        "nova/tools/registry.py": 360,
        "nova/tools/todos.py": 80,
        "nova/tools/agents.py": 90,
    }

    for relative_path, max_lines in budgets.items():
        line_count = len((root / relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= max_lines, f"{relative_path} has {line_count} lines, budget is {max_lines}"
