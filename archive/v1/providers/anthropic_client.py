import os
import anthropic

API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")

def ask(prompt, model="claude-3-opus-20240229", max_tokens=2048):
    if not API_KEY:
        return "error: 没有设置 ANTHROPIC_API_KEY"
    client = anthropic.Anthropic(api_key=API_KEY)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text
