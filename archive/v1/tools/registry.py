"""简单的工具注册中心。"""
from .read import read_file
from .shell import run_shell
from .write import write_file

TOOLS = {
    "read_file": {
        "fn": read_file,
        "description": "读取文件内容",
        "args": {"path": "文件路径"}
    },
    "run_shell": {
        "fn": run_shell,
        "description": "执行 shell 命令",
        "args": {"command": "要执行的命令"}
    },
    "write_file": {
        "fn": write_file,
        "description": "写入文件",
        "args": {"path": "文件路径", "content": "文件内容"}
    }
}

def list_tools():
    return {name: info["description"] for name, info in TOOLS.items()}

def call_tool(name, **kwargs):
    if name not in TOOLS:
        return f"error: 未知工具 {name}"
    return TOOLS[name]["fn"](**kwargs)
