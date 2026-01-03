"""简单的对话历史持久化：追加到 JSONL 文件。"""
import json
from datetime import datetime

HISTORY_FILE = "nova_history.jsonl"

def record(role, content, provider="openai"):
    entry = {
        "role": role,
        "content": content,
        "provider": provider,
        "timestamp": datetime.now().isoformat()
    }
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_recent(n=10):
    try:
        with open(HISTORY_FILE) as f:
            lines = f.readlines()
        return [json.loads(l) for l in lines[-n:]]
    except FileNotFoundError:
        return []
