"""Provider 抽象层——v2 重构。"""
import os

_providers = {}

def get_provider(name):
    if name not in _providers:
        if name == "openai":
            from .openai_client import OpenAIProvider
            _providers[name] = OpenAIProvider()
        elif name == "anthropic":
            from .anthropic_client import AnthropicProvider
            _providers[name] = AnthropicProvider()
        else:
            raise ValueError(f"unknown provider: {name}")
    return _providers[name]
