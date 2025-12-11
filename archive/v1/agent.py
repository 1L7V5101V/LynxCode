"""回退到 batch 模式，stream 问题太多。"""
import json
import os
import openai

with open("config.json") as f:
    config = json.load(f)

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")
openai.api_key = API_KEY

def ask(prompt):
    provider = config.get("provider", "openai")
    if provider == "anthropic":
        from anthropic_client import ask as _anthropic_ask
        return _anthropic_ask(prompt)
    else:
        resp = openai.ChatCompletion.create(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            messages=[{"role": "user", "content": prompt}]
        )
        return resp["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print(ask("hello"))
