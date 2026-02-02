"""v2 工具注册中心。"""
import re

TOOL_PATTERN = re.compile(r'(\w+)\(["\'](.*?)["\']\)')

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, fn, description=""):
        self._tools[name] = {"fn": fn, "description": description}

    def parse_response(self, response):
        match = TOOL_PATTERN.search(response)
        if match:
            return {"name": match.group(1), "args": [match.group(2)]}
        return None

    def execute(self, call):
        name = call["name"]
        if name not in self._tools:
            return f"error: unknown tool {name}"
        return self._tools[name]["fn"](*call["args"])
