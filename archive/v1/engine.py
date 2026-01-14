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
    print(f"[debug] full_prompt len={len(full_prompt)}")  # DEBUG
    response = _provider_ask(full_prompt)
    print(f"[debug] response={response[:200]}")  # DEBUG
    match = re.search(r'(\w+)\(["\'](.*?)["\']\)', response)
    print(f"[debug] match={match}")  # DEBUG
    if match:
        tool_name = match.group(1)
        arg_str = match.group(2)
        print(f"[debug] tool_name={tool_name} arg={arg_str}")  # DEBUG
        result = call_tool(tool_name, arg_str)
        print(f"[debug] result={result[:100]}")  # DEBUG
        return _provider_ask(prompt + "\n\n工具结果:\n" + result)
    print(f"[debug] no tool call detected, returning raw response")  # DEBUG
    return response
