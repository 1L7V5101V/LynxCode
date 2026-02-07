"""v2 引擎——重新设计，明确单向依赖。"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from providers.base import get_provider
from tools.registry import Registry

class Engine:
    def __init__(self, provider_name="openai"):
        self.provider = get_provider(provider_name)
        self.tools = Registry()
        self.history = []

    def ask(self, prompt):
        self.history.append({"role": "user", "content": prompt})
        response = self.provider.complete(self._build_prompt())
        tool_result = self.tools.try_dispatch(response)
        if tool_result:
            self.history.append({"role": "assistant", "content": f"[tool: {tool_result}]"})
            response = self.provider.complete(self._build_prompt())
        self.history.append({"role": "assistant", "content": response})
        return response

    def _build_prompt(self):
        return "\n".join(f"{m['role']}: {m['content']}" for m in self.history[-10:])
