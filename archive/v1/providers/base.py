"""统一 provider 调用接口。"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def ask(prompt):
    config = load_config()
    provider_name = config.get("default_provider", "openai")
    provider_cfg = config.get("providers", {}).get(provider_name, {})
    if provider_name == "anthropic":
        from .anthropic_client import ask as _anthropic_ask
        return _anthropic_ask(prompt, **provider_cfg)
    elif provider_name == "openai":
        from .openai_client import ask as _openai_ask
        return _openai_ask(prompt, **provider_cfg)
    else:
        return f"error: 未知 provider {provider_name}"
