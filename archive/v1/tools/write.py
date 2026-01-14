"""写文件工具。"""
import os

def write_file(path, content):
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"written: {path}"
    except Exception as e:
        return f"error: 写文件失败 {e}"
