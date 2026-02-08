"""权限系统雏形：简单的 allow/deny 列表。"""
import os

ALLOW_COMMANDS = {
    "ls", "cat", "pwd", "echo", "git", "python", "pip",
    "cd", "mkdir", "touch", "cp", "mv", "rm", "head", "tail",
}

DENY_COMMANDS = {
    "sudo", "su", "chmod", "chown", "kill", "pkill",
}

def check_shell(command):
    parts = command.strip().split()
    if not parts:
        return False, "空命令"
    cmd = parts[0]
    if cmd in DENY_COMMANDS:
        return False, f"禁止的命令: {cmd}"
    return True, ""

def check_read(path):
    return True, ""

def check_write(path):
    return True, ""
