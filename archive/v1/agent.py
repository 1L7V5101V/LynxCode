"""最早的原型：直接调 OpenAI API 的 toy。"""
import json
import os
import openai

with open("config.json") as f:
    config = json.load(f)

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")
if not API_KEY:
    raise RuntimeError("需要设置 OPENAI_API_KEY")

openai.api_key = API_KEY

def ask(prompt):
    resp = openai.ChatCompletion.create(
        model=config["model"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        messages=[{"role": "user", "content": prompt}]
    )
    return resp["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print(ask("hello"))
