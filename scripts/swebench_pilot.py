"""Quick pilot: test SWE-bench pipeline on flask instance only.

Run data saved to artifacts/swebench_runs/<instance_id>-<timestamp>/ for review.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

GIT_OPTS = ["-c", "http.proxy=http://127.0.0.1:7890"]

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "swebench_runs"


def save_run_data(instance_id: str, repo_dir: Path, agent) -> Path | None:
    """Copy .nova/runs/<run_id>/ and session to a persistent directory.

    Returns the save path, or None if nothing to save.
    """
    runs_dir = repo_dir / ".nova" / "runs"
    sessions_dir = repo_dir / ".nova" / "sessions"

    run_id = getattr(getattr(agent, "current_task_state", None), "run_id", None)
    if not run_id:
        # Fallback: copy the entire .nova/runs/ if it exists
        if not runs_dir.exists():
            return None
        # Use latest run directory by mtime
        run_dirs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not run_dirs:
            return None
        run_id = run_dirs[0].name

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    save_dir = ARTIFACTS_DIR / f"{instance_id}-{timestamp}"
    save_dir.mkdir(parents=True, exist_ok=True)

    # Copy run data
    src_run = runs_dir / run_id
    if src_run.exists():
        dst_run = save_dir / "run"
        shutil.copytree(src_run, dst_run, dirs_exist_ok=True)
        print(f"\n  [save] Run data -> {dst_run}")
        for f in dst_run.iterdir():
            print(f"    {f.name} ({f.stat().st_size} bytes)")

    # Copy session file
    if sessions_dir.exists():
        dst_sessions = save_dir / "sessions"
        shutil.copytree(sessions_dir, dst_sessions, dirs_exist_ok=True)
        print(f"  [save] Session -> {dst_sessions}")

    # Save a brief summary sidecar
    summary = {
        "instance_id": instance_id,
        "run_id": run_id,
        "saved_at": timestamp,
        "run_dir": str(src_run),
        "sessions_dir": str(sessions_dir),
    }
    (save_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    return save_dir


def main():
    # Load flask instance
    instances = json.loads(
        (PROJECT_ROOT / "artifacts" / "swebench_lite_selected.json").read_text()
    )["selected"]
    instance = next(i for i in instances if "flask" in i["repo"])
    instance_id = instance["instance_id"]
    print(f"Instance: {instance_id}")
    print(f"Repo: {instance['repo']} @ {instance['base_commit'][:12]}")

    with tempfile.TemporaryDirectory(prefix="swebench-pilot-") as tmpdir:
        work_dir = Path(tmpdir)
        repo_dir = work_dir / "flask"

        # STEP 1: Clone
        print("\n=== STEP 1: Clone ===")
        repo_dir.mkdir(exist_ok=True)
        for cmd, desc in [
            (["git", *GIT_OPTS, "init"], "git init"),
            (["git", *GIT_OPTS, "remote", "add", "origin",
              f"https://github.com/{instance['repo']}.git"], "remote add"),
            (["git", *GIT_OPTS, "fetch", "--depth", "1", "origin",
              instance["base_commit"]], "fetch commit"),
            (["git", *GIT_OPTS, "checkout", "FETCH_HEAD"], "checkout"),
        ]:
            proc = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, timeout=300)
            if proc.returncode == 0:
                print(f"  OK: {desc}")
            else:
                print(f"  FAIL: {desc}: {proc.stderr[:200]}")
                return

        # STEP 2: Apply test patch
        print("\n=== STEP 2: Apply test patch ===")
        proc = subprocess.run(
            ["git", "apply"], cwd=repo_dir,
            input=instance["test_patch"], capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            print("  OK: git apply succeeded")
        else:
            print(f"  WARN: git apply issue: {proc.stderr[:200]}")

        # STEP 3: Create venv + install
        print("\n=== STEP 3: Setup venv + deps ===")
        venv_dir = repo_dir / ".swebenv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)],
                       check=True, capture_output=True, timeout=120)
        pip_path = str(venv_dir / "Scripts" / "pip")

        # Pre-pin compatible dependency versions for each repo
        extra_pins = {
            "pallets/flask": "werkzeug<3.0",
            "psf/requests": "",
            "astropy/astropy": "",
            "django/django": "",
        }
        repo_key = instance["repo"]
        pin = extra_pins.get(repo_key, "")
        if pin:
            print(f"  Pin: {pin}")
            subprocess.run([pip_path, "install", pin], capture_output=True, timeout=120)

        proc = subprocess.run(
            [pip_path, "install", "-e", ".[dev]"],
            cwd=repo_dir, capture_output=True, text=True, timeout=300,
        )
        if proc.returncode == 0:
            print("  OK: .[dev] installed")
        else:
            print(f"  WARN: .[dev] failed: {proc.stderr[:200]}")
            proc = subprocess.run(
                [pip_path, "install", "-e", "."],
                cwd=repo_dir, capture_output=True, text=True, timeout=300,
            )
            if proc.returncode == 0:
                print("  OK: . (bare) installed")
            else:
                print(f"  FAIL: install failed: {proc.stderr[:200]}")
                return

        # Pin pytest version compatible with flask 2.3's conftest
        subprocess.run([pip_path, "install", "pytest<8"], capture_output=True, timeout=120)

        # STEP 4: Baseline test (should FAIL - test_patch adds new test that fails without the fix)
        print("\n=== STEP 4: Baseline test check ===")
        python_path = str(venv_dir / "Scripts" / "python")
        test_ids = instance["FAIL_TO_PASS"]
        if isinstance(test_ids, str):
            test_ids = json.loads(test_ids)
        test_args = test_ids
        print(f"  Running: pytest -x -q --no-header {' '.join(test_args)}")
        proc = subprocess.run(
            [python_path, "-m", "pytest", "-x", "-q", "--no-header"] + test_args,
            cwd=repo_dir, capture_output=True, text=True, timeout=120,
        )
        baseline_passed = proc.returncode == 0
        print(f"  Baseline result: {'PASS' if baseline_passed else 'FAIL (expected)'}")
        if baseline_passed:
            print("  (Test already passes without fix - not a valid SWE-bench instance)")
        else:
            stdout = proc.stdout[:500] if proc.stdout else "(empty)"
            stderr = proc.stderr[:500] if proc.stderr else "(empty)"
            print(f"  stdout: {stdout}")
            print(f"  stderr: {stderr}")

        # STEP 5: Run Nova
        print("\n=== STEP 5: Run Nova agent ===")
        from nova.core.runtime import Nova, SessionStore
        from nova.core.workspace import WorkspaceContext
        from nova.config import resolve_provider_config
        from nova.providers import OpenAIChatCompletionsModelClient

        config = resolve_provider_config("deepseek", start=PROJECT_ROOT)
        model_client = OpenAIChatCompletionsModelClient(
            model=config.model,
            base_url=config.base_url,
            api_key=config.api_key,
            temperature=0.2,
            timeout=600,
        )

        workspace = WorkspaceContext.build(repo_dir, repo_root_override=repo_dir)
        store = SessionStore(repo_dir / ".nova" / "sessions")

        agent = Nova(
            model_client=model_client, workspace=workspace,
            session_store=store, approval_policy="auto",
            max_steps=120, max_new_tokens=8192,
        )

        start = time.time()
        try:
            answer = agent.ask(instance["problem_statement"])
            dur = time.time() - start
            task_state = agent.current_task_state
            print(f"  Nova completed in {dur:.1f}s, tools={task_state.tool_steps}")
            print(f"  Answer: {answer[:200]}...")
        except Exception as e:
            print(f"  Nova failed: {e}")
            return

        # STEP 6: Save run data before tempdir is destroyed
        save_dir = save_run_data(instance_id, repo_dir, agent)

        # STEP 7: Verify
        print("\n=== STEP 6: Verify fix ===")
        proc = subprocess.run(
            [python_path, "-m", "pytest", "-x", "-q", "--no-header"] + test_args,
            cwd=repo_dir, capture_output=True, text=True, timeout=120,
        )
        resolved = proc.returncode == 0
        print(f"  RESOLVED: {resolved}")
        if not resolved:
            print(f"  stdout: {proc.stdout[:500]}")
            print(f"  stderr: {proc.stderr[:500]}")

        print(f"\n{'='*50}")
        print(f"PILOT COMPLETE: resolved={resolved}")
        if save_dir:
            print(f"Run data: {save_dir}")
        print(f"{'='*50}")
        print()
        print("To review:")
        if save_dir:
            run_path = save_dir / "run"
            print(f"  - task_state: {run_path / 'task_state.json'}")
            print(f"  - trace:      {run_path / 'trace.jsonl'}")
            print(f"  - report:     {run_path / 'report.json'}")
            print(f"  - summary:    {save_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
