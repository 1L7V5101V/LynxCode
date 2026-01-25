"""核心引擎：集成 context 管理器。"""
import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from providers import ask as _provider_ask
from tools.registry import list_tools, call_tool
from context import Context

TOOL_DESCRIPTIONS = """
你有以下工具可用：
"""

ctx = Context()

def ask(prompt):
    ctx.add_user(prompt)
    tool_list = "\n".join([f"  {name}({', '.join(info['args'].keys())}) - {info['description']}"
                          for name, info in sorted(list_tools().items())])
    full_prompt = TOOL_DESCRIPTIONS + tool_list + "\n\n" + ctx.build_prompt()
    response = _provider_ask(full_prompt)
    match = re.search(r'(\w+)\(["\'](.*?)["\']\)', response)
    if match:
        tool_name = match.group(1)
        arg_str = match.group(2)
        tool_result = call_tool(tool_name, arg_str)
        ctx.add_assistant(f"[调用工具 {tool_name}]")
        ctx.add_user(f"工具 {tool_name} 返回: {tool_result}")
        tool_list = "\n".join([f"  {name}({', '.join(info['args'].keys())}) - {info['description']}"
                              for name, info in sorted(list_tools().items())])
        response = _provider_ask(TOOL_DESCRIPTIONS + tool_list + "\n\n" + ctx.build_prompt())
    ctx.add_assistant(response)
    return response
