"""Session 持久化——简陋 pickle 实现。"""
import os
import pickle
import uuid
from datetime import datetime

SESSION_DIR = ".nova_sessions"

def _session_path(session_id):
    os.makedirs(SESSION_DIR, exist_ok=True)
    return os.path.join(SESSION_DIR, f"{session_id}.pkl")

def new_session():
    session_id = str(uuid.uuid4())[:8]
    session = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "history": [],
        "metadata": {},
    }
    save_session(session)
    return session

def save_session(session):
    path = _session_path(session["id"])
    with open(path, "wb") as f:
        pickle.dump(session, f)

def load_session(session_id):
    path = _session_path(session_id)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)

def list_sessions():
    if not os.path.isdir(SESSION_DIR):
        return []
    return [f.replace(".pkl", "") for f in os.listdir(SESSION_DIR) if f.endswith(".pkl")]
