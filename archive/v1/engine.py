"""核心引擎：tool calling 解析改进。"""
import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from providers import ask as _provider_ask
from tools import read_file, run_shell

TOOL_DESCRIPTIONS = """
你有以下工具可用：

read_file(path) - 读取文件内容
run_shell(command) - 执行 shell 命令

要使用工具，在回复中写:
TOOL: read_file("foo.py")
TOOL: run_shell("ls -la")

工具结果会在下一轮消息中返回给你。
"""

TOOL_PATTERN = re.compile(r'TOOL:\s*(\w+)\(["\'](.*?)["\']\)', re.DOTALL)

def _execute_tool(tool_name, arg):
    if tool_name == "read_file":
        return read_file(arg)
    elif tool_name == "run_shell":
        return run_shell(arg)
    return f"未知工具: {tool_name}"

def ask(prompt):
    full_prompt = TOOL_DESCRIPTIONS + "\n\n用户: " + prompt
    response = _provider_ask(full_prompt)
    match = TOOL_PATTERN.search(response)
    if match:
        tool_name, arg = match.groups()
        result = _execute_tool(tool_name, arg)
        return _provider_ask(full_prompt + "\n\n工具结果:\n" + result)
    return response
