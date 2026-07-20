#!/usr/bin/env python3
"""Lightweight SWE-bench Lite evaluator for Nova memory ablation experiments.

Usage:
    python scripts/swebench_evaluator.py [--instances artifacts/swebench_lite_selected.json] [--max-instances 2]

Runs Nova against selected SWE-bench instances and records pass/fail per variant.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

INSTANCES_PATH = PROJECT_ROOT / "artifacts" / "swebench_lite_selected.json"
RESULTS_DIR = PROJECT_ROOT / "artifacts" / "swebench_results"


def load_instances(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["selected"]


def git_clone_commit(repo_url: str, commit_hash: str, target_dir: Path) -> None:
    """Clone a repo at a specific commit (shallow)."""
    repo_name = repo_url.split("/")[-1]
    clone_dir = target_dir / repo_name

    # Use --depth 1 + fetch specific commit for speed
    subprocess.run(
        ["git", "init"],
        cwd=target_dir,
        check=True,
        capture_output=True,
        timeout=60,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{repo_url}.git"],
        cwd=target_dir,
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "fetch", "--depth", "1", "origin", commit_hash],
        cwd=target_dir,
        check=True,
        capture_output=True,
        timeout=120,
    )
    subprocess.run(
        ["git", "checkout", commit_hash],
        cwd=target_dir,
        check=True,
        capture_output=True,
        timeout=30,
    )
    return clone_dir


def apply_test_patch(repo_dir: Path, test_patch: str) -> None:
    """Apply the SWE-bench test patch to the repo."""
    proc = subprocess.run(
        ["git", "apply"],
        cwd=repo_dir,
        input=test_patch,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        print(f"  [WARN] git apply failed: {proc.stderr[:200]}")


def setup_venv(repo_dir: Path) -> Path:
    """Create a venv in the repo and install its dependencies."""
    venv_dir = repo_dir / ".swebenv"

    # Create venv
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
        timeout=120,
    )

    # Determine pip path
    if os.name == "nt":
        pip_path = str(venv_dir / "Scripts" / "pip")
    else:
        pip_path = str(venv_dir / "bin" / "pip")

    # Upgrade pip
    subprocess.run(
        [pip_path, "install", "--upgrade", "pip"],
        capture_output=True,
        timeout=120,
    )

    # Try to install the package in editable mode + dev/test deps
    # SWE-bench instances usually need specific versions
    for extra in ["dev", "test", "testing", "tests"]:
        proc = subprocess.run(
            [pip_path, "install", "-e", f".[{extra}]"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if proc.returncode == 0:
            break
    else:
        # Fallback: just install the package itself
        subprocess.run(
            [pip_path, "install", "-e", "."],
            cwd=repo_dir,
            capture_output=True,
            timeout=300,
        )

    return venv_dir


def run_variant(
    repo_dir: Path,
    instance: dict,
    variant: str,
) -> dict:
    """Run Nova agent against a SWE-bench instance with given memory variant.

    Returns dict with pass/fail and metrics.
    """
    from nova.core.runtime import Nova, SessionStore
    from nova.core.workspace import WorkspaceContext
    from nova.evaluation.metrics import _make_provider_client

    problem_statement = instance["problem_statement"]
    instance_id = instance["instance_id"]

    print(f"  [Nova] variant={variant} problem_statement[:100]={problem_statement[:100]}...")

    # Build Nova workspace on the repo directory
    workspace = WorkspaceContext.build(
        repo_dir,
        repo_root_override=repo_dir,
    )
    store = SessionStore(repo_dir / ".nova" / "sessions")

    # Create model client from default provider
    try:
        model_client = _make_provider_client("deepseek")
    except Exception as exc:
        print(f"  [ERROR] Failed to create model client: {exc}")
        return {"variant": variant, "error": str(exc), "resolved": False}

    agent = Nova(
        model_client=model_client,
        workspace=workspace,
        session_store=store,
        approval_policy="auto",
        max_steps=50,
    )

    # Configure memory variant
    if variant == "memory_off":
        agent.feature_flags["memory"] = False
        agent.feature_flags["relevant_memory"] = False
    elif variant == "memory_irrelevant":
        # Fill with irrelevant memory
        state = agent.memory.to_dict()
        state["episodic_notes"] = [
            {
                "text": "team mascot is blue",
                "tags": ["unrelated"],
                "source": "other.txt",
                "created_at": "2026-04-08T10:00:00+00:00",
                "note_index": 0,
            }
        ]
        state["notes"] = ["team mascot is blue"]
        state["file_summaries"] = {}
        agent.memory.state = state
        agent.session["memory"] = agent.memory.to_dict()

    start_time = time.time()
    try:
        answer = agent.ask(problem_statement)
        task_state = agent.current_task_state
    except Exception as exc:
        print(f"  [ERROR] Nova agent failed: {exc}")
        return {
            "variant": variant,
            "error": str(exc),
            "resolved": False,
            "tool_steps": 0,
            "duration_ms": (time.time() - start_time) * 1000,
        }

    duration_ms = (time.time() - start_time) * 1000

    return {
        "variant": variant,
        "resolved": None,  # Will be set by verifier
        "final_answer": answer,
        "tool_steps": int(task_state.tool_steps),
        "attempts": int(task_state.attempts),
        "stop_reason": task_state.stop_reason,
        "duration_ms": duration_ms,
    }


def run_verifier(repo_dir: Path, instance: dict, venv_dir: Path) -> bool:
    """Run pytest on FAIL_TO_PASS tests. Returns True if all pass."""
    fail_to_pass = instance["FAIL_TO_PASS"]
    if not fail_to_pass:
        return True

    # Determine python/pytest path from venv
    if os.name == "nt":
        python_path = str(venv_dir / "Scripts" / "python")
    else:
        python_path = str(venv_dir / "bin" / "python")

    # Run pytest on the specific test functions
    test_ids = fail_to_pass if isinstance(fail_to_pass, list) else json.loads(fail_to_pass)
    test_arg = " or ".join(test_ids)

    proc = subprocess.run(
        [python_path, "-m", "pytest", "-x", "-q", "--no-header", "-k", test_arg],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    passed = proc.returncode == 0
    return passed


def run_instance(instance: dict, results_dir: Path, variants: list[str]) -> dict:
    """Run a single SWE-bench instance across all variants."""
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    base_commit = instance["base_commit"]

    print(f"\n{'='*60}")
    print(f"Instance: {instance_id}")
    print(f"Repo: {repo} @ {base_commit[:12]}")
    print(f"{'='*60}")

    # 1. Create temp dir
    with tempfile.TemporaryDirectory(prefix=f"swebench-{instance_id}-") as tmpdir:
        work_dir = Path(tmpdir)
        repo_dir = work_dir / repo.split("/")[-1]

        # 2. Clone repo at base_commit (with proxy for GitHub)
        GIT_OPTS = ["-c", "http.proxy=http://127.0.0.1:7890"]
        print(f"  [git] Cloning {repo} @ {base_commit[:12]}...")
        repo_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", *GIT_OPTS, "init"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            timeout=60,
        )
        subprocess.run(
            ["git", *GIT_OPTS, "remote", "add", "origin", f"https://github.com/{repo}.git"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            timeout=30,
        )
        subprocess.run(
            ["git", *GIT_OPTS, "fetch", "--depth", "1", "origin", base_commit],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            timeout=300,
        )
        subprocess.run(
            ["git", *GIT_OPTS, "checkout", "FETCH_HEAD"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            timeout=30,
        )
        print(f"  [git] Cloned successfully")

        # 3. Apply test_patch
        print(f"  [git] Applying test patch...")
        apply_test_patch(repo_dir, instance["test_patch"])

        # 4. Install dependencies
        print(f"  [pip] Setting up venv and installing deps...")
        venv_dir = setup_venv(repo_dir)
        print(f"  [pip] Dependencies installed")

        # 5. Run verifier (baseline - should fail)
        print(f"  [test] Baseline check (expect FAIL)...")
        baseline_passed = run_verifier(repo_dir, instance, venv_dir)
        print(f"  [test] Baseline result: {'PASS (unexpected)' if baseline_passed else 'FAIL (expected)'}")

        # 6. Run each variant
        variant_results = []
        for variant in variants:
            print(f"  [variant] Running {variant}...")
            result = run_variant(repo_dir, instance, variant)
            if "error" not in result:
                # Run verifier to check if Nova fixed the issue
                resolved = run_verifier(repo_dir, instance, venv_dir)
                result["resolved"] = resolved
                print(f"  [variant] {variant}: {'RESOLVED' if resolved else 'NOT RESOLVED'} "
                      f"(tools={result['tool_steps']}, duration={result['duration_ms']:.0f}ms)")
            variant_results.append(result)

    return {
        "instance_id": instance_id,
        "repo": repo,
        "base_commit": base_commit,
        "baseline_passed": baseline_passed,
        "variants": variant_results,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SWE-bench Lite evaluator for Nova")
    parser.add_argument("--instances", type=str, default=str(INSTANCES_PATH),
                        help="Path to selected instances JSON")
    parser.add_argument("--max", type=int, default=2,
                        help="Max instances to evaluate (default: 2)")
    parser.add_argument("--variants", type=str, nargs="+",
                        default=["memory_on"],
                        help="Variants to test")
    args = parser.parse_args()

    instances = load_instances(Path(args.instances))
    if args.max:
        instances = instances[:args.max]

    results_dir = RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    for instance in instances:
        result = run_instance(instance, results_dir, args.variants)
        all_results.append(result)

        # Save intermediate results
        output = {
            "schema": "swebench-lite-evaluation-v1",
            "total": len(all_results),
            "resolved": sum(1 for r in all_results
                          for v in r.get("variants", [])
                          if v.get("resolved")),
            "results": all_results,
        }
        out_path = results_dir / "results.json"
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[+] Saved intermediate results to {out_path}")

    # Final summary
    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(all_results)} instances")
    for r in all_results:
        for v in r.get("variants", []):
            status = "✅" if v.get("resolved") else "❌" if v.get("resolved") is False else "⚠️"
            print(f"  {r['instance_id']} [{v['variant']}]: {status} "
                  f"tools={v.get('tool_steps', '?')} "
                  f"duration={v.get('duration_ms', 0)/1000:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
