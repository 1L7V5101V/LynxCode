"""核心引擎：通过 registry 调用工具。"""
import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from providers import ask as _provider_ask
from tools.registry import list_tools, call_tool

TOOL_DESCRIPTIONS = """
你有以下工具可用：
"""

def ask(prompt):
    tool_list = "\n".join([f"  {name}({', '.join(info['args'].keys())}) - {info['description']}"
                          for name, info in sorted(list_tools().items())])
    full_prompt = TOOL_DESCRIPTIONS + tool_list + "\n\n" + "用户: " + prompt
    response = _provider_ask(full_prompt)
    match = re.search(r'(\w+)\(["\'](.*?)["\']\)', response)
    if match:
        tool_name = match.group(1)
        arg_str = match.group(2)
        result = call_tool(tool_name, arg_str)
        return _provider_ask(prompt + "\n\n工具结果:\n" + result)
    return response
