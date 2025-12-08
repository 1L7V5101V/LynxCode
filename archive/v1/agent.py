"""最早的原型：直接调 OpenAI API 的 toy。"""
import os
import openai

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")
if not API_KEY:
    raise RuntimeError("需要设置 OPENAI_API_KEY")

openai.api_key = API_KEY

def ask(prompt):
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print(ask("hello"))
