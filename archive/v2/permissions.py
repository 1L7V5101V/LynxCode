"""权限系统——重新设计，独立于 tool_executor。"""
import os

class PermissionChecker:
    def __init__(self):
        self.allowlist = {
            "ls", "cat", "pwd", "echo", "git", "python", "pip",
            "cd", "mkdir", "touch", "cp", "mv", "rm", "head", "tail", "grep",
            "find", "wc", "sort", "uniq", "diff", "tree",
        }
        self.denylist = {
            "sudo", "su", "chmod", "chown", "kill", "pkill",
            "reboot", "shutdown", "init", "systemctl",
        }

    def check_command(self, command):
        parts = command.strip().split()
        if not parts:
            return False, "empty command"
        base = os.path.basename(parts[0])
        if base in self.denylist:
            return False, f"command denied: {base}"
        if base in self.allowlist:
            return True, ""
        return False, f"command not in allowlist: {base}"

    def check_path(self, path, mode="read"):
        return True, ""
