"""Provider 抽象层——v2 重构。"""
import os

class ProviderClient:
    _instances = {}

    @classmethod
    def get(cls, name):
        if name not in cls._instances:
            if name == "openai":
                from .openai_client import OpenAIProvider
                cls._instances[name] = OpenAIProvider()
            elif name == "anthropic":
                from .anthropic_client import AnthropicProvider
                cls._instances[name] = AnthropicProvider()
            else:
                raise ValueError(f"unknown provider: {name}")
        return cls._instances[name]
