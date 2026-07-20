"""Pick one SWE-bench Lite instance per repo for a small ablation run."""
import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

from datasets import load_dataset

ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")

# Pick one instance per repo (the one with fewest FAIL_TO_PASS tests)
selected = {}
for d in ds:
    repo = d["repo"]
    if repo not in selected:
        selected[repo] = d
    elif len(d["FAIL_TO_PASS"]) < len(selected[repo]["FAIL_TO_PASS"]):
        selected[repo] = d

for repo in sorted(selected):
    inst = selected[repo]
    print(f"{repo}: {inst['instance_id']} ({len(inst['FAIL_TO_PASS'])} tests to pass)")

print(f"\nTotal: {len(selected)} instances")

# Save selected instances
import json
output = {
    "selected": [
        {
            "instance_id": inst["instance_id"],
            "repo": inst["repo"],
            "base_commit": inst["base_commit"],
            "problem_statement": inst["problem_statement"],
            "test_patch": inst["test_patch"],
            "FAIL_TO_PASS": inst["FAIL_TO_PASS"],
            "PASS_TO_PASS": inst["PASS_TO_PASS"],
            "version": inst["version"],
        }
        for inst in selected.values()
    ]
}
with open("artifacts/swebench_lite_selected.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print("Saved to artifacts/swebench_lite_selected.json")
