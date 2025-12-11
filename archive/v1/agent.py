"""玩具原型：尝试 stream 模式（有 bug）。"""
import json
import os
import sys
import openai

with open("config.json") as f:
    config = json.load(f)

def ask(prompt, stream=False):
    provider = config.get("provider", "openai")
    if provider == "anthropic":
        from anthropic_client import ask as _anthropic_ask
        return _anthropic_ask(prompt)
    else:
        API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")
        openai.api_key = API_KEY
        if stream:
            resp = openai.ChatCompletion.create(
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for chunk in resp:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    print(content, end="", flush=True)
            print()
            return ""
        else:
            resp = openai.ChatCompletion.create(
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                messages=[{"role": "user", "content": prompt}]
            )
            return resp["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print(ask("写一首诗", stream=True))
