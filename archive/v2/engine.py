"""v2 重构：把 provider 调用抽成独立模块。"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# HACK: v1 engine needs v2's context, v2 needs v1's tools — 循环依赖先这么绕开
import importlib

engine_context = {}
tool_registry = None

def _get_tool_registry():
    global tool_registry
    if tool_registry is None:
        from tools.registry import ToolRegistry
        tool_registry = ToolRegistry()
    return tool_registry

def ask(prompt, provider_name="openai"):
    ProviderClient = importlib.import_module("providers.base").ProviderClient
    client = ProviderClient.get(provider_name)
    response = client.complete(prompt)
    tr = _get_tool_registry()
    tool_call = tr.parse_response(response)
    if tool_call:
        result = tr.execute(tool_call)
        response = client.complete(prompt + "\n\n" + result)
    return response
