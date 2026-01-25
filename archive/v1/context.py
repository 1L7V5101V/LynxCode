"""简单的对话上下文管理：滑窗截断。"""
import json

MAX_HISTORY_TOKENS = 6000

class Context:
    def __init__(self):
        self.messages = []

    def add_user(self, text):
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant(self, text):
        self.messages.append({"role": "assistant", "content": text})
        self._trim()

    def _trim(self):
        total = sum(len(m["content"]) for m in self.messages)
        while total > MAX_HISTORY_TOKENS * 4 and len(self.messages) > 2:
            removed = self.messages.pop(0)
            total -= len(removed["content"])

    def build_prompt(self, system_msg=""):
        parts = [{"role": "system", "content": system_msg}] if system_msg else []
        parts.extend(self.messages)
        return parts
