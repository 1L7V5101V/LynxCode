import os
import openai

class OpenAIProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")
        self.model = "gpt-4"

    def complete(self, prompt, **kwargs):
        openai.api_key = self.api_key
        resp = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return resp["choices"][0]["message"]["content"]
