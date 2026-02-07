"""v2 工具注册中心——重新设计。"""
import re

TOOL_CALL_RE = re.compile(r'(\w+)\(["\'](.*?)["\']\)')

class Registry:
    def __init__(self):
        self._tools = {}

    def register(self, name, fn, description=""):
        self._tools[name] = {"fn": fn, "description": description}

    def try_dispatch(self, response):
        match = TOOL_CALL_RE.search(response)
        if not match:
            return None
        name, arg = match.groups()
        tool = self._tools.get(name)
        if not tool:
            return f"error: unknown tool {name}"
        try:
            return tool["fn"](arg)
        except Exception as e:
            return f"error: {e}"
