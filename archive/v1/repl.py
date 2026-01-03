"""简陋的交互式 REPL 循环。"""
import sys
from engine import ask

def main():
    print("Nova v0.0.1 — 简陋 REPL (exit 退出)")
    while True:
        try:
            prompt = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if prompt.strip().lower() in ("exit", "quit"):
            break
        if not prompt.strip():
            continue
        print()
        print(ask(prompt))

if __name__ == "__main__":
    main()
