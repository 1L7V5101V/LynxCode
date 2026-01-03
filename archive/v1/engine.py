"""核心引擎：拆分出来的模型调用逻辑。"""
import json
import os
import openai

with open(os.path.join(os.path.dirname(__file__), "config.json")) as f:
    config = json.load(f)

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")
if API_KEY:
    openai.api_key = API_KEY

def ask(prompt):
    provider = config.get("provider", "openai")
    if provider == "anthropic":
        from anthropic_client import ask as _anthropic_ask
        return _anthropic_ask(prompt)
    else:
        if not API_KEY:
            return "error: 没有设置 API key"
        resp = openai.ChatCompletion.create(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            messages=[{"role": "user", "content": prompt}]
        )
        return resp["choices"][0]["message"]["content"]
