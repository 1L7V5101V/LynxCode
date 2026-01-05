import os
import openai

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")

def ask(prompt, model="gpt-4", temperature=0.7, max_tokens=2048):
    if not API_KEY:
        return "error: 没有设置 OPENAI_API_KEY"
    openai.api_key = API_KEY
    resp = openai.ChatCompletion.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp["choices"][0]["message"]["content"]
