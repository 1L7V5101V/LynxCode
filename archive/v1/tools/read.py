"""读文件工具。"""
import os

def read_file(path):
    if not os.path.isfile(path):
        return f"error: 文件不存在 {path}"
    try:
        with open(path) as f:
            return f.read()
    except Exception as e:
        return f"error: 读文件失败 {e}"
