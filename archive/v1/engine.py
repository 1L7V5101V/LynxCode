"""核心引擎：带简陋 tool calling。"""
import json
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

def ask(prompt):
    full_prompt = TOOL_DESCRIPTIONS + "\n\n用户: " + prompt
    response = _provider_ask(full_prompt)

    if response.startswith("TOOL:"):
        tool_line = response[len("TOOL:"):].strip()
        try:
            if tool_line.startswith("read_file"):
                path = tool_line.split('"')[1]
                result = read_file(path)
                return _provider_ask(full_prompt + "\n\n工具结果:\n" + result)
            elif tool_line.startswith("run_shell"):
                cmd = tool_line.split('"')[1]
                result = run_shell(cmd)
                return _provider_ask(full_prompt + "\n\n工具结果:\n" + result)
        except Exception as e:
            return f"工具调用失败: {e}"

    return response
