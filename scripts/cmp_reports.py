"""Compare report.json prompt metadata from two runs."""
import json, sys

def analyze(path, label):
    d = json.loads(open(path, encoding="utf-8").read())
    pm = d.get("prompt_metadata", {})
    cu = pm.get("context_usage", {})
    print(f"=== {label} ===")
    print(f"  status: {d.get('status')}  stop_reason: {d.get('stop_reason')}")
    print(f"  tool_steps: {d.get('tool_steps')}  attempts: {d.get('attempts')}")
    print(f"  max_new_tokens (reserved): {cu.get('reserved_output_tokens')}")
    print(f"  total_estimated_tokens: {cu.get('total_estimated_tokens')}")
    for name, sec in cu.get("sections", {}).items():
        print(f"    {name}: {sec.get('chars')}c / {sec.get('tokens')}tok")
    print(f"  prompt_chars:   {pm.get('prompt_chars')}")
    print(f"  prefix_chars:   {pm.get('prefix_chars')}")
    print(f"  memory_chars:   {pm.get('memory_chars')}")
    print(f"  history_chars:  {pm.get('history_chars')}")
    print(f"  workspace_chars:{pm.get('workspace_chars')}")
    print(f"  request_chars:  {pm.get('request_chars')}")
    print(f"  budget_reductions: {pm.get('budget_reductions')}")

analyze(sys.argv[1], sys.argv[2])
if len(sys.argv) > 3:
    analyze(sys.argv[3], sys.argv[4])
