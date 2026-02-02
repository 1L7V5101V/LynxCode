"""v2 重构：把 provider 调用抽成独立模块。"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from providers.base import ProviderClient
from tools.registry import ToolRegistry

engine_context = {}
tool_registry = ToolRegistry()

def ask(prompt, provider_name="openai"):
    client = ProviderClient.get(provider_name)
    response = client.complete(prompt)
    tool_call = tool_registry.parse_response(response)
    if tool_call:
        result = tool_registry.execute(tool_call)
        response = client.complete(prompt + "\n\n" + result)
    return response
