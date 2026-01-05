"""核心引擎：通过 provider 抽象层调用模型。"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from providers import ask as _provider_ask

def ask(prompt):
    return _provider_ask(prompt)
